# %%
"""
Landsat Processed Data Validator (AquaPerma-NorthMB)

Checks the landsat_processed folder for:
 - Presence of NDVI, NDWI, NBR GeoTIFFs
 - Presence of quick-look PNGs
 - Consistency with the CSV summary file

Usage:
    python scripts/validate_landsat_outputs.py
"""

# %%
import os
from pathlib import Path
import pandas as pd

# %%
# CONFIG
PROCESSED_DIR = Path("/Users/domenica/Desktop/AquaPerma-NorthMB/data/processed/landsat_processed")
CSV_SUMMARY = PROCESSED_DIR / "landsat_indices_summary.csv"

# %%
# Load CSV summary
if not CSV_SUMMARY.exists():
    print("Error: CSV summary not found:", CSV_SUMMARY)
else:
    df = pd.read_csv(CSV_SUMMARY)
    scenes_in_csv = set(df['scene'])
    print(f"Scenes in summary CSV: {len(scenes_in_csv)}")

# %%
# Check folders
scene_folders = [p for p in PROCESSED_DIR.iterdir() if p.is_dir()]
print(f"Scene folders found: {len(scene_folders)}")

# %%
# Validation
missing_files = []
for folder in scene_folders:
    scene_name = folder.name
    tif_ndvi = folder / f"{scene_name}_NDVI.tif"
    tif_ndwi = folder / f"{scene_name}_NDWI.tif"
    tif_nbr = folder / f"{scene_name}_NBR.tif"
    png = folder / f"{scene_name}_indices.png"

    for f in [tif_ndvi, tif_ndwi, png]:
        if not f.exists():
            missing_files.append(str(f))

    # NBR is optional (Landsat 5 may not have SWIR2)
    if tif_nbr.exists() is False:
        print(f"Warning: NBR missing for {scene_name} (may be okay)")

# %%
# Compare CSV and folders
missing_scenes_in_csv = [f.name for f in scene_folders if f.name not in scenes_in_csv]
missing_folders_on_disk = [s for s in scenes_in_csv if (PROCESSED_DIR / s).exists() is False]

# %%
# Report
print("\n=== Validation Report ===")
if missing_files:
    print("Missing files:", missing_files)
else:
    print("All required files exist.")

if missing_scenes_in_csv:
    print("Scenes on disk missing in CSV:", missing_scenes_in_csv)
else:
    print("All scene folders are listed in CSV.")

if missing_folders_on_disk:
    print("Scenes in CSV missing on disk:", missing_folders_on_disk)
else:
    print("All CSV scenes exist on disk.")

print("\nValidation complete.")
