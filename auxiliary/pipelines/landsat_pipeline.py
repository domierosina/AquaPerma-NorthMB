"""
===============================================================================
 Script:        landsat_pipeline.py
 Project:       AquaPerma – Northern Manitoba Surface Water Monitoring
 Author:        Domenica B.
 Created:       2025-11-30
 Description:
    This script processes Landsat Collection-2 Level-2 Surface Reflectance (SR) scenes.
    It reads .tar archives or already-extracted scene folders from `data/raw/Landsat_zipped/`,
    computes vegetation and water indices (NDVI, NDWI, NBR), and outputs:

      - GeoTIFFs per index, clipped to AOI if provided
      - Quick-look PNG images
      - CSV summary of mean indices over AOI


     Main Landsat Collection-2 L2 processing pipeline for the AquaPerma project.
     - Extracts tar archives (if present)
     - Reads SR bands and QA_PIXEL
     - Computes NDVI, NDWI, NBR
     - Applies conservative QA masking
     - Clips to AOI (KML) when available
     - Writes per-scene GeoTIFFs, quick-look PNGs and a CSV summary

 Outputs:
     data/landsat_processed/<scene>/*_NDVI.tif
     data/landsat_processed/landsat_indices_summary.csv

 Usage:
 ------
 Open in Jupyter or VSCode (# %% cells), or run from command line:
 python pipelines/landsat_pipeline.py

 Requirements: rasterio, geopandas, numpy, pandas, matplotlib, tqdm
===============================================================================
"""

# %%
import os
import re
import tarfile
from pathlib import Path
from datetime import datetime
import warnings

import numpy as np
import pandas as pd
import rasterio
from rasterio.mask import mask
from rasterio.enums import Resampling
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import mapping
from tqdm import tqdm

warnings.filterwarnings('ignore')

# %%
# -------------------
# USER CONFIG
# -------------------
LANDSAT_FOLDER = Path("data/raw/Landsat_zipped")      # input raw tar files
OUT_DIR = Path("data/landsat_processed")             # processed outputs
OUT_DIR.mkdir(parents=True, exist_ok=True)
AOI_KML = Path("data/aoi/2025_aoi.kml")             # optional AOI

# Parameters
CLOUD_QA_BITMASK = None  # set to integer mask if you want to mask QA_PIXEL (we auto-interpret common bits)
DOWNSAMPLE = False  # if True will resample to lower resolution for quick plots
PLOT_DPI = 150

# %%
# -------------------
# Utility functions
# -------------------
def find_tar_files(folder: Path):
    return sorted(folder.glob("*.tar"))


def extract_tar(tar_path: Path, dest_folder: Path):
    """Extract tar if dest_folder doesn't already contain expected files."""
    if dest_folder.exists() and any(dest_folder.glob("*.TIF")):
        print(f"Skipping extraction (already present): {dest_folder}")
        return
    print(f"Extracting {tar_path} -> {dest_folder}")
    dest_folder.mkdir(parents=True, exist_ok=True)
    with tarfile.open(tar_path) as tar:
        tar.extractall(path=dest_folder)


def collect_band_paths(scene_folder: Path):
    """Collect SR band paths and QA_PIXEL for a scene folder.
    Returns dict with keys like 'B2','B3',... and 'QA_PIXEL'
    Works with names containing '_SR_B' or '_SR_B2.TIF' or 'SR_B2'
    """
    files = list(scene_folder.rglob("*.TIF"))
    bands = {}
    for f in files:
        name = f.name.upper()
        m = re.search(r"_SR_B(\d{1,2})\.TIF", name)
        if not m:
            m = re.search(r"_B(\d{1,2})\.TIF", name)
        if m:
            b = int(m.group(1))
            bands[f"B{b}"] = f
            continue
        if "QA_PIXEL" in name:
            bands['QA_PIXEL'] = f
    return bands


def read_band(band_path, out_dtype=np.float32):
    with rasterio.open(band_path) as src:
        arr = src.read(1).astype(out_dtype)
        meta = src.meta.copy()
    return arr, meta


def write_geotiff(path, data, meta, nodata=None):
    meta_copy = meta.copy()
    meta_copy.update(dtype=rasterio.float32, count=1, compress='deflate')
    if nodata is not None:
        meta_copy.update(nodata=nodata)
    with rasterio.open(path, 'w', **meta_copy) as dst:
        dst.write(data.astype(rasterio.float32), 1)


# %%
# -------------------
# AOI loader
# -------------------
def load_aoi_kml(kml_path: Path):
    if not kml_path.exists():
        print("AOI KML not found, skipping AOI clipping")
        return None
    gdf = gpd.read_file(str(kml_path), driver='KML')
    # union all geometries if multiple
    geom = gdf.unary_union
    # ensure WGS84
    if gdf.crs is None:
        gdf.set_crs(epsg=4326, inplace=True)
    return gdf.to_crs(epsg=4326)

# -------------------
# Index calculations
# -------------------
def ndvi(nir, red):
    # avoid division by zero
    denom = (nir + red)
    out = np.where(denom == 0, np.nan, (nir - red) / denom)
    return out


def ndwi(green, nir):
    denom = (green + nir)
    out = np.where(denom == 0, np.nan, (green - nir) / denom)
    return out


def nbr(nir, swir2):
    denom = (nir + swir2)
    out = np.where(denom == 0, np.nan, (nir - swir2) / denom)
    return out

# %%
# QA_PIXEL mask helper (simple common bits interpretation)
def mask_clouds_from_qa(qa_arr):
    """
    Interpret QA_PIXEL bits to mask clouds/water/invalid.
    This is a conservative mask: mask where cloud bits are set.
    Landsat QA_PIXEL bits reference (common): cloud/shadow/snow/land/water flags.
    Implementation depends on exact bit layout; here we mask values > 0 (safe conservative).
    """
    # conservative: mask any non-zero QA_PIXEL
    mask = (qa_arr == 0)
    return mask

# %%
# -------------------
# Main processing
# -------------------
def process_scene(scene_folder: Path, aoi_gdf=None, outdir: Path = OUT_DIR, download_png=True):
    bands = collect_band_paths(scene_folder)
    if not bands:
        print(f"No TIF bands found in {scene_folder}")
        return None

    # Required bands for indices: B4 (red), B5/B8/NIR depends on sensor. For Landsat-8:
    # B4 = Red, B5 = NIR, B6 = SWIR1, B7 = SWIR2
    required = ['B4', 'B5']
    for r in required:
        if r not in bands:
            print(f"Required band {r} missing in {scene_folder}; found bands: {list(bands.keys())}")
            return None

    # Read arrays and meta from one band (the red band) as reference
    red_arr, meta = read_band(bands['B4'])
    nir_arr, _ = read_band(bands['B5'])
    swir2_arr = None
    if 'B7' in bands:
        swir2_arr, _ = read_band(bands['B7'])
    elif 'B6' in bands:
        swir2_arr, _ = read_band(bands['B6'])

    # read QA_PIXEL if available
    qa_mask = None
    if 'QA_PIXEL' in bands:
        qa_arr, _ = read_band(bands['QA_PIXEL'], out_dtype=np.uint16)
        qa_mask = mask_clouds_from_qa(qa_arr)
    else:
        qa_mask = np.ones_like(red_arr, dtype=bool)

    # compute indices
    ndvi_arr = ndvi(nir_arr, red_arr)
    ndwi_arr = ndwi(red_arr, nir_arr)  # note: NDWI commonly uses green (B3). If B3 exists, use it.
    if 'B3' in bands:
        green, _ = read_band(bands['B3'])
        ndwi_arr = ndwi(green, nir_arr)

    nbr_arr = None
    if swir2_arr is not None:
        nbr_arr = nbr(nir_arr, swir2_arr)

    # apply QA mask (set masked pixels to nan)
    ndvi_arr = np.where(qa_mask, ndvi_arr, np.nan)
    ndwi_arr = np.where(qa_mask, ndwi_arr, np.nan)
    if nbr_arr is not None:
        nbr_arr = np.where(qa_mask, nbr_arr, np.nan)

    # clip to AOI if provided
    meta_crs = meta.get('crs')
    use_meta = meta.copy()
    if aoi_gdf is not None:
        # project AOI to raster CRS
        aoi_proj = aoi_gdf.to_crs(use_meta['crs'])
        geoms = [mapping(aoi_proj.unary_union)]
        # create mask window using rasterio.mask
        def clip_array(arr, rio_meta):
            with rasterio.open(bands['B4']) as src:
                out_image, out_transform = mask(src, geoms, crop=True)
                out_meta = src.meta.copy()
                out_meta.update({
                    "height": out_image.shape[1],
                    "width": out_image.shape[2],
                    "transform": out_transform
                })
            return out_image[0], out_meta

        # Clip reference band to get updated meta and transform
        try:
            _, out_meta = clip_array(red_arr, use_meta)
            use_meta = out_meta
            # For indices arrays, we need to re-read masked arrays using the mask window approach
            with rasterio.open(bands['B4']) as srcr:
                red_clip, _ = mask(srcr, geoms, crop=True)
                red_clip = red_clip[0]
            with rasterio.open(bands['B5']) as srcn:
                nir_clip, _ = mask(srcn, geoms, crop=True)
                nir_clip = nir_clip[0]
            ndvi_arr = ndvi(nir_clip.astype(np.float32), red_clip.astype(np.float32))
            if 'B3' in bands:
                with rasterio.open(bands['B3']) as srcg:
                    green_clip, _ = mask(srcg, geoms, crop=True)
                    green_clip = green_clip[0]
                ndwi_arr = ndwi(green_clip.astype(np.float32), nir_clip.astype(np.float32))
            if swir2_arr is not None:
                with rasterio.open(bands.get('B7') or bands.get('B6')) as srcs:
                    swir_clip, _ = mask(srcs, geoms, crop=True)
                    swir_clip = swir_clip[0]
                nbr_arr = nbr(nir_clip.astype(np.float32), swir_clip.astype(np.float32))
        except Exception as e:
            print("AOI clipping failed:", e)

    # write outputs
    scene_id = scene_folder.name
    scene_out = outdir / scene_id
    scene_out.mkdir(parents=True, exist_ok=True)

    ndvi_path = scene_out / f"{scene_id}_NDVI.tif"
    write_geotiff(ndvi_path, np.nan_to_num(ndvi_arr, nan=-9999.0), use_meta, nodata=-9999.0)

    ndwi_path = scene_out / f"{scene_id}_NDWI.tif"
    write_geotiff(ndwi_path, np.nan_to_num(ndwi_arr, nan=-9999.0), use_meta, nodata=-9999.0)

    if nbr_arr is not None:
        nbr_path = scene_out / f"{scene_id}_NBR.tif"
        write_geotiff(nbr_path, np.nan_to_num(nbr_arr, nan=-9999.0), use_meta, nodata=-9999.0)

    # quick-look PNG
    if download_png:
        fig, axs = plt.subplots(1, 3 if nbr_arr is not None else 2, figsize=(12, 4))
        im0 = axs[0].imshow(ndvi_arr, vmin=-1, vmax=1)
        axs[0].set_title('NDVI')
        plt.colorbar(im0, ax=axs[0], fraction=0.046)

        im1 = axs[1].imshow(ndwi_arr, vmin=-1, vmax=1)
        axs[1].set_title('NDWI')
        plt.colorbar(im1, ax=axs[1], fraction=0.046)

        if nbr_arr is not None:
            im2 = axs[2].imshow(nbr_arr, vmin=-1, vmax=1)
            axs[2].set_title('NBR')
            plt.colorbar(im2, ax=axs[2], fraction=0.046)

        plt.suptitle(scene_id)
        plt.tight_layout()
        png_out = scene_out / f"{scene_id}_indices.png"
        plt.savefig(png_out, dpi=PLOT_DPI)
        plt.close()

    # compute summary stats (mean over valid pixels)
    def mean_valid(arr):
        a = np.array(arr)
        a = a[~np.isnan(a)]
        if a.size == 0:
            return np.nan
        return float(np.nanmean(a))

    stats = {
        'scene': scene_id,
        'ndvi_mean': mean_valid(ndvi_arr),
        'ndwi_mean': mean_valid(ndwi_arr),
        'nbr_mean': mean_valid(nbr_arr) if nbr_arr is not None else None,
        'bands_found': list(bands.keys())
    }

    return stats

# %%
# -------------------
#  Runner: process all tar files (or already-extracted scene folders)
# -------------------
def run_all(lz_folder: Path, aoi_kml: Path = None):
    # prepare AOI gdf
    aoi_gdf = None
    if aoi_kml and aoi_kml.exists():
        aoi_gdf = load_aoi_kml(aoi_kml)

    results = []

    # handle .tar archives: extract each into a folder next to the tar
    tar_files = find_tar_files(lz_folder)
    if tar_files:
        for t in tar_files:
            sfolder = lz_folder / t.stem
            extract_tar(t, sfolder)
            stats = process_scene(sfolder, aoi_gdf=aoi_gdf)
            if stats:
                results.append(stats)
    else:
        # no tars: look for scene folders
        for scene in sorted(lz_folder.iterdir()):
            if scene.is_dir():
                stats = process_scene(scene, aoi_gdf=aoi_gdf)
                if stats:
                    results.append(stats)

    # save CSV summary
    df = pd.DataFrame(results)
    df.to_csv(OUT_DIR / 'landsat_indices_summary.csv', index=False)
    print('\nSummary written to', OUT_DIR / 'landsat_indices_summary.csv')
    return df

# %%
# -------------------
# Script execution
# -------------------
if __name__ == '__main__':
    df = run_all(LANDSAT_FOLDER, AOI_KML)
    print(df)
