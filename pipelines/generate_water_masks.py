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

# %%
import rasterio
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# %%
# -------------------
# USER CONFIG
# -------------------
NDWI_FOLDER = Path("data/processed/landsat_processed")
THRESHOLD = 0.3
PLOT_DPI = 150
OUTPUT_CSV = NDWI_FOLDER / "landsat_water_summary.csv"
OUTPUT_WATER_AREA_PLOT = NDWI_FOLDER / "water_area_plot.png"
OUTPUT_PERCENT_WATER_PLOT = NDWI_FOLDER / "percent_water_plot.png"

# -------------------
# PROCESS ALL SCENES
# -------------------
scene_dirs = [d for d in NDWI_FOLDER.iterdir() if d.is_dir()]
summary_list = []

for scene_dir in scene_dirs:
    ndwi_path = scene_dir / f"{scene_dir.name}_NDWI.tif"
    if not ndwi_path.exists():
        print(f"NDWI file not found for {scene_dir.name}, skipping...")
        continue

    # read NDWI
    with rasterio.open(ndwi_path) as src:
        ndwi_arr = src.read(1)
        meta = src.meta.copy()
        transform = src.transform
        pixel_area = abs(transform.a * transform.e)  # in map units (m² if UTM)

    # generate binary water mask
    water_mask = (ndwi_arr > THRESHOLD).astype(np.uint8)

    # save water mask GeoTIFF
    out_mask_path = scene_dir / f"{scene_dir.name}_water_mask.tif"
    meta.update(dtype=rasterio.uint8, count=1, compress='deflate')
    meta.pop('nodata', None)  # remove any existing nodata
    with rasterio.open(out_mask_path, 'w', **meta) as dst:
        dst.write(water_mask, 1)

    # save quick-look PNG
    out_png_path = scene_dir / f"{scene_dir.name}_water_mask.png"
    plt.imshow(water_mask, cmap='Blues')
    plt.title(f"{scene_dir.name} Water Mask")
    plt.axis('off')
    plt.savefig(out_png_path, dpi=PLOT_DPI)
    plt.close()

    # compute water area metrics
    total_pixels = np.count_nonzero(water_mask >= 0)  # all valid pixels
    water_pixels = np.sum(water_mask == 1)
    water_area = water_pixels * pixel_area
    percent_water = (water_pixels / total_pixels) * 100

    summary_list.append({
        "scene": scene_dir.name,
        "total_pixels": total_pixels,
        "water_pixels": water_pixels,
        "water_area_m2": water_area,
        "percent_water": percent_water
    })

    print(f"Processed {scene_dir.name}: water pixels = {water_pixels}, percent water = {percent_water:.2f}%")

# -------------------
# SAVE CSV SUMMARY
# -------------------
df = pd.DataFrame(summary_list)
df = df.sort_values("scene")
df.to_csv(OUTPUT_CSV, index=False)
print(f"\nWater summary saved to {OUTPUT_CSV}")
print(df)

# -------------------
# PLOT WATER AREA OVER TIME
# -------------------
plt.figure(figsize=(10,5))
plt.plot(df['scene'], df['water_area_m2']/1e6, marker='o')  # convert m² to km²
plt.xticks(rotation=45)
plt.xlabel("Scene")
plt.ylabel("Water Area (km²)")
plt.title("Landsat Water Area Over Time")
plt.tight_layout()
plt.savefig(OUTPUT_WATER_AREA_PLOT, dpi=PLOT_DPI)
plt.close()
print(f"Water area plot saved to {OUTPUT_WATER_AREA_PLOT}")

# -------------------
# PLOT PERCENT WATER OVER TIME
# -------------------
plt.figure(figsize=(10,5))
plt.plot(df['scene'], df['percent_water'], marker='o', color='green')
plt.xticks(rotation=45)
plt.xlabel("Scene")
plt.ylabel("Percent Water (%)")
plt.title("Landsat Percent Water Over Time")
plt.tight_layout()
plt.savefig(OUTPUT_PERCENT_WATER_PLOT, dpi=PLOT_DPI)
plt.close()
print(f"Percent water plot saved to {OUTPUT_PERCENT_WATER_PLOT}")
