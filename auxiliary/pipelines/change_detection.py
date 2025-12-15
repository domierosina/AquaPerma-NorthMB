"""
===============================================================================
 Script:        change_detection.py
 Project:       AquaPerma – Northern Manitoba Surface Water Monitoring
 Author:        Domenica B.
 Created:       2025-12-07
 Description:
    Compute change-detection rasters from NDWI-derived binary water masks.

    For all scenes in data/processed/landsat_processed/ (ordered by date), compute
    pairwise changes between consecutive scenes. For a given pair (A -> B):
      - gain  : pixel 0 in A and 1 in B  -> coded as 1
      - loss  : pixel 1 in A and 0 in B  -> coded as 2
      - nochg : equal values (both 0 or both 1) -> coded as 0
      - nodata: 255

    Outputs:
      - data/processed/landsat_processed/<sceneA>_to_<sceneB>_change.tif
      - data/processed/landsat_processed/<sceneA>_to_<sceneB>_change.png
      - data/processed/landsat_processed/change_detection_summary.csv

 Usage:
 ------
 python pipelines/change_detection.py

 Requirements: rasterio, numpy, pandas, matplotlib, pathlib, re
===============================================================================
"""

import re
from pathlib import Path
import numpy as np
import rasterio
from rasterio.enums import Resampling
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

# -------------------
# CONFIG
# -------------------
PROCESSED_DIR = Path("data/processed/landsat_processed")
OUT_DIR = PROCESSED_DIR
PLOT_DPI = 200

# change coding (uint8)
# 0 = no change, 1 = gain (non-water -> water), 2 = loss (water -> non-water)
NODATA = 255

# -------------------
# Helpers
# -------------------
def scene_date_from_name(name:str):
    """
    Extract the first 8-digit YYYYMMDD occurrence in the scene name.
    Returns pd.Timestamp or None.
    """
    m = re.search(r'(\d{8})', name)
    if not m:
        return None
    try:
        return pd.to_datetime(m.group(1), format='%Y%m%d')
    except Exception:
        return None

def find_water_mask(scene_folder:Path):
    """Return path to water mask tif if present, else None."""
    masks = list(scene_folder.glob("*_water_mask.tif"))
    if masks:
        return masks[0]
    # fallback: any file with 'water_mask' in name
    for p in scene_folder.iterdir():
        if p.is_file() and 'water_mask' in p.name.lower() and p.suffix.lower() in ('.tif', '.tiff'):
            return p
    return None

def save_change_png(change_arr, out_png_path):
    """Save a PNG with colors: loss=red, nochange=white, gain=blue."""
    cmap = ListedColormap(['white', 'blue', 'red'])  # index 0->white,1->blue,2->red
    # create masked array for nodata
    mask_nodata = (change_arr == NODATA)
    plot_arr = change_arr.copy()
    plot_arr = np.where(plot_arr==NODATA, 0, plot_arr)  # map nodata to background (white)
    fig, ax = plt.subplots(figsize=(8,8))
    ax.imshow(plot_arr, cmap=cmap, vmin=0, vmax=2)
    if np.any(mask_nodata):
        # overlay nodata as transparent -- here we leave it white
        pass
    ax.axis('off')
    plt.tight_layout()
    plt.savefig(out_png_path, dpi=PLOT_DPI, bbox_inches='tight', pad_inches=0.01)
    plt.close(fig)

# -------------------
# Main
# -------------------
# Collect scene folders and dates
scene_folders = [p for p in PROCESSED_DIR.iterdir() if p.is_dir()]
scene_info = []
for s in scene_folders:
    dt = scene_date_from_name(s.name)
    scene_info.append((s, dt))

# keep only scenes with a parsable date
scene_info = [t for t in scene_info if t[1] is not None]
# sort by date
scene_info.sort(key=lambda x: x[1])

if len(scene_info) < 2:
    print("Need at least two dated scenes for change detection. Exiting.")
    raise SystemExit(0)

rows = []
# iterate consecutive pairs
for (s1, d1), (s2, d2) in zip(scene_info[:-1], scene_info[1:]):
    name1 = s1.name
    name2 = s2.name
    pair_label = f"{name1}_to_{name2}"
    print(f"Processing change: {pair_label}")

    m1 = find_water_mask(s1)
    m2 = find_water_mask(s2)
    if not m1 or not m2:
        print(f"  [SKIP] missing water mask for pair: {m1}, {m2}")
        continue

    with rasterio.open(m1) as src1, rasterio.open(m2) as src2:
        # Ensure same shape and transform. If not, resample second to first's grid.
        arr1 = src1.read(1)
        meta = src1.meta.copy()
        if (src1.width != src2.width) or (src1.height != src2.height) or (src1.transform != src2.transform):
            # resample src2 to src1
            data2 = src2.read(
                1,
                out_shape=(src1.height, src1.width),
                resampling=Resampling.nearest
            )
            arr2 = data2
            # Use src1.meta (already copied)
        else:
            arr2 = src2.read(1)

    # create nodata mask from inputs - treat any pixel where either is nodata as nodata
    # assume masks are uint8 with values 0/1; we'll treat 255 as nodata if present
    arr1_valid = (arr1 != NODATA)
    arr2_valid = (arr2 != NODATA)
    valid_mask = arr1_valid & arr2_valid

    # initialize change array with nodata
    change = np.full_like(arr1, fill_value=NODATA, dtype=np.uint8)

    # where valid, compute change:
    # gain: arr1==0 & arr2==1  -> code 1
    gain = (arr1 == 0) & (arr2 == 1) & valid_mask
    # loss: arr1==1 & arr2==0  -> code 2
    loss = (arr1 == 1) & (arr2 == 0) & valid_mask
    # nochange: (arr1==arr2) & valid_mask  -> code 0
    nochange = (arr1 == arr2) & valid_mask

    change[nochange] = 0
    change[gain] = 1
    change[loss] = 2

    # Save change GeoTIFF
    out_tif = OUT_DIR / f"{pair_label}_change.tif"
    out_meta = meta.copy()
    out_meta.update(dtype=rasterio.uint8, count=1, compress='deflate', nodata=NODATA)
    with rasterio.open(out_tif, 'w', **out_meta) as dst:
        dst.write(change, 1)

    # Save PNG visualization
    out_png = OUT_DIR / f"{pair_label}_change.png"
    save_change_png(change, out_png)

    # Compute areas: pixel area from meta transform (abs(a*e))
    transform = meta['transform']
    pixel_area = abs(transform[0] * transform[4])  # typically m² if UTM/metric CRS

    gain_pixels = np.count_nonzero(gain)
    loss_pixels = np.count_nonzero(loss)
    net_pixels = gain_pixels - loss_pixels

    gain_area_m2 = gain_pixels * pixel_area
    loss_area_m2 = loss_pixels * pixel_area
    net_area_m2 = net_pixels * pixel_area

    # percent relative to valid pixels
    valid_pixels_count = np.count_nonzero(valid_mask)
    if valid_pixels_count > 0:
        percent_gain = (gain_pixels / valid_pixels_count) * 100
        percent_loss = (loss_pixels / valid_pixels_count) * 100
    else:
        percent_gain = percent_loss = np.nan

    rows.append({
        'pair': pair_label,
        'date_from': d1.strftime('%Y-%m-%d'),
        'date_to': d2.strftime('%Y-%m-%d'),
        'gain_pixels': int(gain_pixels),
        'loss_pixels': int(loss_pixels),
        'gain_area_m2': float(gain_area_m2),
        'loss_area_m2': float(loss_area_m2),
        'net_area_m2': float(net_area_m2),
        'valid_pixels': int(valid_pixels_count),
        'percent_gain': float(percent_gain),
        'percent_loss': float(percent_loss),
        'change_tif': str(out_tif),
        'change_png': str(out_png)
    })

    print(f"  [SAVED] {out_tif.name} and {out_png.name} | gain: {gain_area_m2:.1f} m2 loss: {loss_area_m2:.1f} m2 net: {net_area_m2:.1f} m2")

# Save summary CSV
if rows:
    df = pd.DataFrame(rows)
    summary_csv = OUT_DIR / "change_detection_summary.csv"
    df.to_csv(summary_csv, index=False)
    print(f"\nChange detection summary saved to {summary_csv}")
else:
    print("No change pairs processed; no summary produced.")
