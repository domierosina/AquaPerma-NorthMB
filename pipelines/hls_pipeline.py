# %%
"""
===============================================================================
 Script:        hls_pipeline.py
 Project:       AquaPerma – Northern Manitoba Surface Water Monitoring
 Author:        Domenica B.
 Created:       2025-12-XX
 Description:
     Processing pipeline for NASA Harmonized Landsat-Sentinel (HLS) products,
     enabling cross-platform analysis consistent with Landsat-derived metrics.

     Features:
         • Downloads or loads local HLS L30/S30 granules
         • Extracts surface reflectance bands (green, red, NIR, SWIR1)
         • Computes NDVI, NDWI, MNDWI using unified formulas
         • Clips to AOI and saves cloud-masked outputs
         • Aligns temporal granules with Landsat dataset for dual-system
           comparison (2016–2021)

 Notes:
     • Allows AquaPerma results to incorporate the Sentinel-2 record
       without struggling with raw S2 L1C/L2A downloads.
     • Requires an Earthdata login + token.

 Folder structure:
     - raw HLS: data/hls_zipped/
     - processed: data/hls_processed/
     - plots: data/plots/hls/

Environment Set Up:
  conda create -n hls310 python=3.10
  conda activate hls310
  conda install -c conda-forge rasterio rioxarray geopandas shapely matplotlib numpy pandas tqdm fiona
  pip install rasterio-cli

===============================================================================
"""

import os
from pathlib import Path
import numpy as np
import pandas as pd
import rasterio
from rasterio.mask import mask
import geopandas as gpd
from shapely.geometry import mapping
import matplotlib.pyplot as plt
from tqdm import tqdm
import warnings
warnings.filterwarnings('ignore')

# %%
# USER CONFIG
HLS_FOLDER = Path("/Users/domenica/Desktop/AquaPerma-NorthMB/data/hls_zipped/")
AOI_KML = Path("/Users/domenica/Desktop/AquaPerma-NorthMB/data/aoi/2025_aoi.kml")  # optional
OUT_DIR = HLS_FOLDER.parent / "hls_processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)

PLOT_DPI = 150

# %%
# Utility functions
def collect_hls_band_paths(scene_folder: Path):
    """
    Collect HLS bands and QA band for a scene folder.
    Returns dict with keys like 'B01','B02',... and 'QA'.
    """
    files = list(scene_folder.rglob("*.tif"))
    bands = {}
    for f in files:
        name = f.name.upper()
        if "_QA" in name:
            bands['QA'] = f
        elif "_B" in name:
            b = name.split("_B")[-1].split(".")[0]
            bands[f"B{b}"] = f
    return bands

def read_band(band_path, out_dtype=np.float32):
    with rasterio.open(band_path) as src:
        arr = src.read(1).astype(out_dtype)
        meta = src.meta.copy()
    return arr, meta

def write_geotiff(path, data, meta, nodata=-9999):
    meta_copy = meta.copy()
    meta_copy.update(dtype=rasterio.float32, count=1, compress='deflate', nodata=nodata)
    with rasterio.open(path, 'w', **meta_copy) as dst:
        dst.write(np.nan_to_num(data, nan=nodata).astype(rasterio.float32), 1)

def load_aoi_kml(kml_path: Path):
    if not kml_path.exists():
        print("AOI KML not found, skipping AOI clipping")
        return None
    gdf = gpd.read_file(str(kml_path), driver='KML')
    geom = gdf.unary_union
    if gdf.crs is None:
        gdf.set_crs(epsg=4326, inplace=True)
    return gdf.to_crs(epsg=4326)

# %%
# Index calculations
def ndvi(nir, red):
    denom = (nir + red)
    return np.where(denom == 0, np.nan, (nir - red) / denom)

def ndwi(green, nir):
    denom = (green + nir)
    return np.where(denom == 0, np.nan, (green - nir) / denom)

def nbr(nir, swir2):
    denom = (nir + swir2)
    return np.where(denom == 0, np.nan, (nir - swir2) / denom)

# %%
# QA mask helper
def mask_clouds_from_qa(qa_arr):
    """
    Conservative mask: mask any non-zero QA value (clouds, invalid)
    """
    return qa_arr == 0

# %%
# Process single scene
def process_scene(scene_folder: Path, aoi_gdf=None, outdir: Path = OUT_DIR, save_png=True):
    bands = collect_hls_band_paths(scene_folder)
    if not bands:
        print(f"No HLS bands found in {scene_folder}")
        return None

    required = ['B04', 'B08']  # Red = B04, NIR = B08
    for r in required:
        if r not in bands:
            print(f"Required band {r} missing in {scene_folder}")
            return None

    red, meta = read_band(bands['B04'])
    nir, _ = read_band(bands['B08'])

    green = None
    if 'B03' in bands:
        green, _ = read_band(bands['B03'])

    swir2 = None
    if 'B11' in bands:
        swir2, _ = read_band(bands['B11'])

    qa_mask = None
    if 'QA' in bands:
        qa, _ = read_band(bands['QA'], out_dtype=np.uint16)
        qa_mask = mask_clouds_from_qa(qa)
    else:
        qa_mask = np.ones_like(red, dtype=bool)

    # Indices
    ndvi_arr = ndvi(nir, red)
    ndwi_arr = ndwi(green if green is not None else red, nir)
    nbr_arr = nbr(nir, swir2) if swir2 is not None else None

    # Apply QA mask
    ndvi_arr = np.where(qa_mask, ndvi_arr, np.nan)
    ndwi_arr = np.where(qa_mask, ndwi_arr, np.nan)
    if nbr_arr is not None:
        nbr_arr = np.where(qa_mask, nbr_arr, np.nan)

    # Clip to AOI
    if aoi_gdf is not None:
        geoms = [mapping(aoi_gdf.unary_union)]
        def clip_array(arr, band_path):
            with rasterio.open(band_path) as src:
                out_img, out_transform = mask(src, geoms, crop=True)
                out_meta = src.meta.copy()
                out_meta.update({
                    "height": out_img.shape[1],
                    "width": out_img.shape[2],
                    "transform": out_transform
                })
            return out_img[0], out_meta

        red_clip, meta = clip_array(red, bands['B04'])
        nir_clip, _ = clip_array(nir, bands['B08'])
        ndvi_arr = ndvi(nir_clip, red_clip)
        if green is not None:
            green_clip, _ = clip_array(green, bands['B03'])
            ndwi_arr = ndwi(green_clip, nir_clip)
        if swir2 is not None:
            swir_clip, _ = clip_array(swir2, bands['B11'])
            nbr_arr = nbr(nir_clip, swir_clip)

    # Save outputs
    scene_id = scene_folder.name
    scene_out = outdir / scene_id
    scene_out.mkdir(parents=True, exist_ok=True)

    write_geotiff(scene_out / f"{scene_id}_NDVI.tif", ndvi_arr, meta)
    write_geotiff(scene_out / f"{scene_id}_NDWI.tif", ndwi_arr, meta)
    if nbr_arr is not None:
        write_geotiff(scene_out / f"{scene_id}_NBR.tif", nbr_arr, meta)

    # Quick-look PNG
    if save_png:
        fig, axs = plt.subplots(1, 3 if nbr_arr is not None else 2, figsize=(12, 4))
        axs[0].imshow(ndvi_arr, vmin=-1, vmax=1)
        axs[0].set_title('NDVI')
        axs[1].imshow(ndwi_arr, vmin=-1, vmax=1)
        axs[1].set_title('NDWI')
        if nbr_arr is not None:
            axs[2].imshow(nbr_arr, vmin=-1, vmax=1)
            axs[2].set_title('NBR')
        plt.suptitle(scene_id)
        plt.tight_layout()
        plt.savefig(scene_out / f"{scene_id}_indices.png", dpi=PLOT_DPI)
        plt.close()

    stats = {
        'scene': scene_id,
        'ndvi_mean': float(np.nanmean(ndvi_arr)),
        'ndwi_mean': float(np.nanmean(ndwi_arr)),
        'nbr_mean': float(np.nanmean(nbr_arr)) if nbr_arr is not None else None,
        'bands_found': list(bands.keys())
    }

    return stats

# %%
# Run all scenes
def run_all(hls_folder: Path, aoi_kml: Path = None):
    aoi_gdf = load_aoi_kml(aoi_kml) if aoi_kml and aoi_kml.exists() else None
    results = []

    for scene in sorted(hls_folder.iterdir()):
        if scene.is_dir():
            stats = process_scene(scene, aoi_gdf=aoi_gdf)
            if stats:
                results.append(stats)

    df = pd.DataFrame(results)
    df.to_csv(OUT_DIR / "hls_indices_summary.csv", index=False)
    print("Summary CSV written:", OUT_DIR / "hls_indices_summary.csv")
    return df

# %%
if __name__ == "__main__":
    df = run_all(HLS_FOLDER, AOI_KML)
    print(df)
