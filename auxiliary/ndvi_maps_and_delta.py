"""
===============================================================================
 Script:        ndvi_maps_and_delta.py
 Project:       AquaPerma – Northern Manitoba Surface Water Monitoring
 Author:        Domenica B.
 Created:       2025-12-05
 Description:
     This script generates spatial NDVI visualizations for the Landsat-based
     AOI processing pipeline used in the AquaPerma project. It does the
     following:

     1. Reads the Landsat index summary table:
            data/landsat_processed/landsat_indices_summary.csv

     2. Extracts scene acquisition dates, identifies the earliest and latest
        valid NDVI scenes, and locates the corresponding NDVI GeoTIFF files.

     3. Loads the earliest and latest NDVI rasters, handling nodata values and
        (if necessary) reprojecting/resampling one raster to match the other.

     4. Generates three maps as PNGs:
            • NDVI map for earliest scene
            • NDVI map for latest scene
            • NDVI delta map (latest – earliest)

     5. Saves a georeferenced NDVI delta GeoTIFF:
            outputs/maps/ndvi_delta_<earliest>_to_<latest>.tif

 Outputs:
     - outputs/figures/ndvi_<scene>.png
     - outputs/figures/ndvi_delta_<earliest>_to_<latest>.png
     - outputs/maps/ndvi_delta_<earliest>_to_<latest>.tif

 Notes:
     • Intended for use on processed Landsat data created by the main pipeline.
     • Handles mismatched projections/resolutions automatically.
     • NDVI delta values indicate vegetation change over the project period.

 Requirements:
     Python 3.9+
     rasterio, numpy, pandas, matplotlib

===============================================================================
"""

from pathlib import Path
import rasterio
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import re
import os

PROC_DIR = Path("/Users/domenica/Desktop/AquaPerma-NorthMB/data/landsat_processed")
OUT_MAP_DIR = Path("/Users/domenica/Desktop/AquaPerma-NorthMB/outputs/maps")
OUT_FIG_DIR = Path("/Users/domenica/Desktop/AquaPerma-NorthMB/outputs/figures")
CSV_PATH = PROC_DIR / "landsat_indices_summary.csv"

OUT_MAP_DIR.mkdir(parents=True, exist_ok=True)
OUT_FIG_DIR.mkdir(parents=True, exist_ok=True)

# helper to extract date (same logic as timeseries)
def extract_date(scene_name):
    m = re.search(r"_(\d{8})_", scene_name)
    if m:
        return pd.to_datetime(m.group(1), format="%Y%m%d")
    m2 = re.search(r"(\d{4})(\d{2})(\d{2})", scene_name)
    if m2:
        return pd.to_datetime("".join(m2.groups()), format="%Y%m%d")
    return pd.NaT

# Load summary CSV
df = pd.read_csv(CSV_PATH)
df['acq_date'] = df['scene'].astype(str).apply(extract_date)
df = df.sort_values('acq_date').reset_index(drop=True)

# Ensure there are valid NDVI files
def locate_ndvi_tif(scene_id):
    # scene folder likely PROC_DIR / scene_id / <scene_id>_NDVI.tif
    scene_folder = PROC_DIR / scene_id
    tif1 = scene_folder / f"{scene_id}_NDVI.tif"
    # fallback: any *_NDVI.tif under folder
    if tif1.exists():
        return tif1
    else:
        candidates = list(scene_folder.glob("*_NDVI.tif"))
        if candidates:
            return candidates[0]
    return None

# pick earliest and latest with valid NDVI files
valid_rows = []
for _, row in df.iterrows():
    scene = str(row['scene'])
    ndvi_path = locate_ndvi_tif(scene)
    if ndvi_path and ndvi_path.exists():
        valid_rows.append((row['acq_date'], scene, ndvi_path))
if len(valid_rows) < 2:
    raise SystemExit("Need at least two scenes with NDVI TIFFs to create delta map. Found: {}".format(len(valid_rows)))

# sorted by date
valid_rows = sorted(valid_rows, key=lambda x: x[0])
earliest_date, earliest_scene, earliest_tif = valid_rows[0]
latest_date, latest_scene, latest_tif = valid_rows[-1]

print("Earliest:", earliest_scene, earliest_date.date(), earliest_tif)
print("Latest:  ", latest_scene, latest_date.date(), latest_tif)

# Read arrays (respecting nodata)
with rasterio.open(earliest_tif) as src_e:
    e_arr = src_e.read(1).astype('float32')
    e_meta = src_e.meta.copy()
    e_nodata = src_e.nodata

with rasterio.open(latest_tif) as src_l:
    l_arr = src_l.read(1).astype('float32')
    l_meta = src_l.meta.copy()
    l_nodata = src_l.nodata

# Replace nodata with nan for calculation
if e_nodata is not None:
    e_arr = np.where(e_arr == e_nodata, np.nan, e_arr)
if l_nodata is not None:
    l_arr = np.where(l_arr == l_nodata, np.nan, l_arr)

# Reproject/resample if shapes differ
if e_arr.shape != l_arr.shape or e_meta['transform'] != l_meta['transform'] or e_meta['crs'] != l_meta['crs']:
    # try to reproject latest to earliest grid (use rasterio.warp.reproject)
    from rasterio.warp import calculate_default_transform, reproject, Resampling
    dst_meta = e_meta.copy()
    dst_shape = (e_meta['height'], e_meta['width'])
    l_reproj = np.full(dst_shape, np.nan, dtype='float32')
    with rasterio.open(latest_tif) as src:
        reproject(
            source=rasterio.band(src, 1),
            destination=l_reproj,
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=e_meta['transform'],
            dst_crs=e_meta['crs'],
            resampling=Resampling.bilinear
        )
    l_arr = l_reproj

# Compute delta (latest - earliest)
delta = l_arr - e_arr

# Clip delta to reasonable range for visualization [-1,1] (NDVI)
delta_plot = np.clip(delta, -1.0, 1.0)

# Plotting helper
def plot_raster(arr, title, vmin=-1, vmax=1, cmap='RdYlGn', outpath=None):
    plt.figure(figsize=(8,6))
    im = plt.imshow(arr, vmin=vmin, vmax=vmax, cmap=cmap)
    plt.title(title)
    plt.axis('off')
    cbar = plt.colorbar(im, fraction=0.036, pad=0.04)
    if outpath:
        plt.savefig(outpath, dpi=300, bbox_inches='tight')
        print("Saved:", outpath)
    plt.close()

# Save earliest, latest and delta PNGs
plot_raster(e_arr, f"NDVI {earliest_scene} ({earliest_date.date()})", -1, 1,
            outpath=OUT_FIG_DIR / f"ndvi_{earliest_scene}.png")
plot_raster(l_arr, f"NDVI {latest_scene} ({latest_date.date()})", -1, 1,
            outpath=OUT_FIG_DIR / f"ndvi_{latest_scene}.png")
plot_raster(delta_plot, f"NDVI Delta (latest - earliest): {latest_date.date()} - {earliest_date.date()}",
            -0.5, 0.5, cmap='bwr',
            outpath=OUT_FIG_DIR / f"ndvi_delta_{earliest_scene}_to_{latest_scene}.png")

# Save delta GeoTIFF (use earliest meta as base)
delta_meta = e_meta.copy()
delta_meta.update(dtype=rasterio.float32, count=1, nodata=-9999.0, compress='deflate')
delta_out_tif = OUT_MAP_DIR / f"ndvi_delta_{earliest_scene}_to_{latest_scene}.tif"
with rasterio.open(delta_out_tif, 'w', **delta_meta) as dst:
    write_arr = np.nan_to_num(delta, nan=-9999.0).astype('float32')
    dst.write(write_arr, 1)
print("Saved delta GeoTIFF:", delta_out_tif)
