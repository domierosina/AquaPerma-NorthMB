===============================================================================
 Notebook:       landsat_results_plots.ipynb
 Project:        AquaPerma – Northern Manitoba Surface Water Monitoring
 Author:         Domenica B.
 Created:        2025-12-07
 Description:
    Reads Landsat index and water summaries, generates plots for presentation:
      - Mean NDVI, NDWI, NBR over time
      - Water area and percent water over time
      - Optional: overlay water masks for selected scenes
===============================================================================

# %%
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# %%
# Paths to CSV summaries
LANDSAT_PROCESSED_DIR = Path("data/landsat_processed")
INDICES_CSV = LANDSAT_PROCESSED_DIR / 'landsat_indices_summary.csv'
WATER_CSV = LANDSAT_PROCESSED_DIR / 'landsat_water_summary.csv'

# %%
# Load summaries
df_indices = pd.read_csv(INDICES_CSV)
df_water = pd.read_csv(WATER_CSV)

# Sort by scene (assumes scenes have dates in name)
df_indices = df_indices.sort_values('scene')
df_water = df_water.sort_values('scene')

# %%
# Plot NDVI, NDWI, NBR over time
plt.figure(figsize=(10, 5))
plt.plot(df_indices['scene'], df_indices['ndvi_mean'], marker='o', label='NDVI')
plt.plot(df_indices['scene'], df_indices['ndwi_mean'], marker='o', label='NDWI')
if 'nbr_mean' in df_indices.columns:
    plt.plot(df_indices['scene'], df_indices['nbr_mean'], marker='o', label='NBR')
plt.xticks(rotation=45, ha='right')
plt.ylabel('Index Value')
plt.title('Mean Landsat Indices Over Time')
plt.legend()
plt.tight_layout()
plt.savefig(LANDSAT_PROCESSED_DIR / 'indices_over_time.png', dpi=150)
plt.show()

# %%
# Plot water area (km²) and percent water
plt.figure(figsize=(10, 5))
plt.plot(df_water['scene'], df_water['water_area_m2']/1e6, marker='o', label='Water Area (km²)')
plt.plot(df_water['scene'], df_water['percent_water'], marker='o', label='Percent Water (%)')
plt.xticks(rotation=45, ha='right')
plt.ylabel('Water Metrics')
plt.title('Water Extent Over Time')
plt.legend()
plt.tight_layout()
plt.savefig(LANDSAT_PROCESSED_DIR / 'water_metrics_over_time.png', dpi=150)
plt.show()

# %%
# Optional: display water masks for selected scenes
import rasterio
from matplotlib.colors import ListedColormap

selected_scenes = [df_water['scene'].iloc[0], df_water['scene'].iloc[-1]]  # first and last scene
for scene in selected_scenes:
    mask_path = LANDSAT_PROCESSED_DIR / scene / f"{scene}_water_mask.tif"
    if mask_path.exists():
        with rasterio.open(mask_path) as src:
            mask_arr = src.read(1)
        plt.figure(figsize=(6,6))
        cmap = ListedColormap(['white', 'blue'])
        plt.imshow(mask_arr, cmap=cmap)
        plt.title(f"Water Mask - {scene}")
        plt.axis('off')
        plt.show()
