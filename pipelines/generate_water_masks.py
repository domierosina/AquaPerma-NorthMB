"""
===============================================================================
 Script:        generate_water_masks.py
 Project:       AquaPerma – Northern Manitoba Surface Water Monitoring
 Author:        Domenica B.
 Created:       2025-12-07
 Description:
    This script generates binary water masks from NDWI GeoTIFF outputs produced
    by the main Landsat processing pipeline (`landsat_pipeline.py`), computes
    water area metrics for each scene, and produces plots showing temporal
    water extent and percent water.

    For each scene in `data/processed/landsat_processed/<scene>/`:

      - Reads the NDWI GeoTIFF
      - Applies a threshold (default NDWI > 0.3) to classify water vs non-water
      - Saves a binary water mask GeoTIFF
      - Saves a quick-look PNG for visualization
      - Computes total water pixels, water area (m²), percent water
      - Saves summary CSV and plots

 Outputs:
     data/processed/landsat_processed/<scene>/<scene>_water_mask.tif
     data/processed/landsat_processed/<scene>/<scene>_water_mask.png
     data/processed/landsat_processed/landsat_water_summary.csv
     data/processed/landsat_processed/water_area_plot.png
     data/processed/landsat_processed/percent_water_plot.png

 Usage:
 ------
 Open in Jupyter or VSCode (# %% cells), or run from command line:
 python pipelines/generate_water_masks_and_summary.py

 Requirements: rasterio, numpy, matplotlib, pandas, pathlib
===============================================================================
"""


import os
from pathlib import Path
import numpy as np
import pandas as pd
import rasterio
import matplotlib.pyplot as plt
from tqdm import tqdm

# -------------------
# User Config
# -------------------
LANDSAT_PROCESSED_DIR = Path("data/processed/landsat_processed")
OUT_DIR = LANDSAT_PROCESSED_DIR
OUT_DIR.mkdir(parents=True, exist_ok=True)


# ----------------------
# Threshold settings
# ----------------------
USE_MANUAL_THRESHOLD = False   # Set True to manually define threshold
MANUAL_THRESHOLD = 0.0        # Only used if USE_MANUAL_THRESHOLD = True

# Quick-look PNG settings
PLOT_DPI = 150

# -------------------
# Processing loop
# -------------------
results = []

for scene_folder in sorted(LANDSAT_PROCESSED_DIR.iterdir()):
    if not scene_folder.is_dir():
        continue

    ndwi_files = list(scene_folder.glob("*_NDWI.tif"))
    if not ndwi_files:
        print(f"No NDWI file found for scene {scene_folder.name}")
        continue

    ndwi_path = ndwi_files[0]

    with rasterio.open(ndwi_path) as src:
        ndwi_arr = src.read(1).astype(np.float32)
        meta = src.meta.copy()

    # Determine threshold per scene
    if USE_MANUAL_THRESHOLD:
        threshold = MANUAL_THRESHOLD
    else:
        ndwi_valid = ndwi_arr[~np.isnan(ndwi_arr)]
        threshold = ndwi_valid.mean() + 0.5 * ndwi_valid.std()

    # Generate water mask
    water_mask = (ndwi_arr > threshold).astype(np.uint8)

    # Write water mask GeoTIFF
    out_mask_path = scene_folder / f"{scene_folder.name}_water_mask.tif"
    meta.update(dtype=rasterio.uint8, count=1, compress='deflate', nodata=0)
    with rasterio.open(out_mask_path, 'w', **meta) as dst:
        dst.write(water_mask, 1)

    # Quick-look PNG
    plt.figure(figsize=(8, 8))
    plt.imshow(water_mask, cmap='Blues')
    plt.title(scene_folder.name)
    plt.axis('off')
    png_out = scene_folder / f"{scene_folder.name}_water_mask.png"
    plt.savefig(png_out, dpi=PLOT_DPI)
    plt.close()

    # Water stats
    total_pixels = np.count_nonzero(~np.isnan(ndwi_arr))
    water_pixels = np.count_nonzero(water_mask)
    pixel_area_m2 = abs(meta['transform'][0] * meta['transform'][4])
    water_area_m2 = water_pixels * pixel_area_m2
    percent_water = (water_pixels / total_pixels) * 100

    results.append({
        'scene': scene_folder.name,
        'total_pixels': total_pixels,
        'water_pixels': water_pixels,
        'water_area_m2': water_area_m2,
        'percent_water': percent_water
    })

    print(f"Processed {scene_folder.name}: water pixels = {water_pixels}, percent water = {percent_water:.2f}%")

# -------------------
# SAVE CSV SUMMARY
# -------------------
summary_df = pd.DataFrame(results)
summary_csv = OUT_DIR / 'landsat_water_summary.csv'
summary_df.to_csv(summary_csv, index=False)
print(f"\nWater summary saved to {summary_csv}")

# -------------------
# PLOT WATER AREA OVER TIME
# -------------------
plt.figure(figsize=(10, 4))
plt.plot(summary_df['scene'], summary_df['water_area_m2']/1e6, marker='o')
plt.xticks(rotation=45, ha='right')
plt.ylabel('Water Area (km²)')
plt.title('Water Area per Scene')
plt.tight_layout()
plt.savefig(OUT_DIR / 'water_area_plot.png', dpi=PLOT_DPI)
plt.close()
print(f"Water area plot saved to {OUTPUT_WATER_AREA_PLOT}")

# -------------------
# PLOT PERCENT WATER OVER TIME
# -------------------
plt.figure(figsize=(10, 4))
plt.plot(summary_df['scene'], summary_df['percent_water'], marker='o')
plt.xticks(rotation=45, ha='right')
plt.ylabel('Percent Water (%)')
plt.title('Percent Water per Scene')
plt.tight_layout()
plt.savefig(OUT_DIR / 'percent_water_plot.png', dpi=PLOT_DPI)
plt.close()
print(f"Percent water plot saved to {OUTPUT_PERCENT_WATER_PLOT}")
