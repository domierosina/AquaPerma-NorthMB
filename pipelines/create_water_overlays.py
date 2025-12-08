"""
===============================================================================
 Script:        create_water_overlays.py
 Project:       AquaPerma – Northern Manitoba Surface Water Monitoring
 Author:        Domenica B.
 Created:       2025-12-07
 Description:
    Generate true-color RGB overlays with NDWI water masks for all processed
    Landsat scenes.

    For each scene folder in `data/processed/landsat_processed/<scene>/`:
      - finds Blue (B2), Green (B3), Red (B4) bands (case-insensitive)
      - stacks them into an RGB image
      - applies a robust percentile stretch (2nd-98th) for display
      - overlays the binary water mask (`*_water_mask.tif`) in semi-transparent blue
      - saves overlay PNG as: data/processed/landsat_processed/<scene>/<scene>_water_overlay.png

 Outputs:
     data/processed/landsat_processed/<scene>/<scene>_water_overlay.png

 Usage:
 ------
 python pipelines/create_water_overlays.py

 Requirements: rasterio, numpy, matplotlib, pathlib
===============================================================================
"""

import sys
from pathlib import Path
import numpy as np
import rasterio
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

# -------------------
# USER CONFIG
# -------------------
PROCESSED_DIR = Path("data/processed/landsat_processed")
OUT_SUFFIX = "_water_overlay.png"
PLOT_DPI = 200
ALPHA = 0.45          # transparency for water overlay
PCT_MIN, PCT_MAX = 2, 98  # percentile stretch for RGB display

# -------------------
# helper: find band file by band number (B2/B3/B4)
# -------------------
def find_band_file(scene_folder: Path, band_num: int):
    # common patterns: *_B2.TIF, *_sr_b2.TIF, *B2.TIF (case-insensitive)
    patterns = [f"*_{'B'+str(band_num)}.TIF", f"*_{'B'+str(band_num)}.tif", f"*B{band_num}.TIF", f"*B{band_num}.tif"]
    # also allow any file containing '_B2' ignoring case
    candidates = [p for p in scene_folder.rglob("*") if p.is_file() and f"_B{band_num}" in p.name.upper()]
    if candidates:
        return sorted(candidates)[0]
    # fallback to glob with patterns
    for pat in patterns:
        files = list(scene_folder.glob(pat))
        if files:
            return files[0]
    return None

# -------------------
# main loop
# -------------------
scene_folders = [p for p in PROCESSED_DIR.iterdir() if p.is_dir()]
if not scene_folders:
    print(f"No scene folders found in {PROCESSED_DIR}. Exiting.")
    sys.exit(0)

for scene in sorted(scene_folders):
    scene_name = scene.name
    # find bands
    b2 = find_band_file(scene, 2)  # blue
    b3 = find_band_file(scene, 3)  # green
    b4 = find_band_file(scene, 4)  # red
    mask_file = next(scene.glob(f"{scene_name}_water_mask.tif"), None)

    if not (b2 and b3 and b4):
        print(f"[SKIP] {scene_name}: missing one of B2/B3/B4 -> B2:{b2}, B3:{b3}, B4:{b4}")
        continue
    if not mask_file:
        print(f"[SKIP] {scene_name}: water mask not found ({scene_name}_water_mask.tif)")
        continue

    # read bands (read as float)
    try:
        with rasterio.open(b2) as src:
            blue = src.read(1).astype(np.float32)
        with rasterio.open(b3) as src:
            green = src.read(1).astype(np.float32)
        with rasterio.open(b4) as src:
            red = src.read(1).astype(np.float32)
    except Exception as e:
        print(f"[ERROR] Failed to read bands for {scene_name}: {e}")
        continue

    # stack to RGB (order: R, G, B)
    rgb = np.stack([red, green, blue], axis=2)

    # handle nodata: mask out where all bands are nodata (or NaN)
    valid_mask = ~np.isnan(rgb).all(axis=2)
    if not np.any(valid_mask):
        print(f"[SKIP] {scene_name}: no valid pixels in RGB bands")
        continue

    # robust percentile stretch per band
    rgb_stretched = np.zeros_like(rgb, dtype=np.float32)
    for i in range(3):
        band = rgb[:, :, i]
        # compute percentiles only on valid pixels
        valid_vals = band[~np.isnan(band)]
        if valid_vals.size == 0:
            vmin, vmax = 0, 1
        else:
            vmin = np.percentile(valid_vals, PCT_MIN)
            vmax = np.percentile(valid_vals, PCT_MAX)
            if vmax == vmin:
                vmax = vmin + 1e-6
        # clip and scale 0..1
        band_clip = np.clip(band, vmin, vmax)
        rgb_stretched[:, :, i] = (band_clip - vmin) / (vmax - vmin)

    # ensure values are within 0..1 and set invalid to 0
    rgb_stretched = np.nan_to_num(rgb_stretched, nan=0.0)
    rgb_stretched = np.clip(rgb_stretched, 0.0, 1.0)

    # read water mask (assumed binary 0/1)
    try:
        with rasterio.open(mask_file) as src:
            mask_arr = src.read(1).astype(np.uint8)
    except Exception as e:
        print(f"[ERROR] Failed to read mask for {scene_name}: {e}")
        continue

    # Prepare overlay: mask==1 will be blue
    # Create a masked array so non-water pixels are transparent
    water_mask = (mask_arr == 1)

    # Plot and save
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.imshow(rgb_stretched)
    # colored overlay (use a simple blue colormap)
    if np.any(water_mask):
        cmap = ListedColormap(['none', 'blue'])
        # use alpha to make overlay semi-transparent: we plot mask as image with alpha
        ax.imshow(np.ma.masked_where(~water_mask, water_mask), cmap='Blues', alpha=ALPHA)
    ax.set_title(f"{scene_name} — Water overlay")
    ax.axis('off')

    out_path = scene / f"{scene_name}{OUT_SUFFIX}"
    plt.tight_layout()
    plt.savefig(out_path, dpi=PLOT_DPI, bbox_inches='tight', pad_inches=0.01)
    plt.close(fig)
    print(f"[SAVED] Overlay for {scene_name} -> {out_path}")
