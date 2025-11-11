
"""Basic stats helpers for binary water masks."""
import numpy as np
import csv
import rasterio

def summarize_water(mask_path: str, out_csv: str):
    """Summarize water area from a binary mask (1=water, 0=non-water).

    Writes a CSV with pixel count and area (in map units squared).

    Parameters
    ----------
    mask_path : str
        Path to a UInt8 mask raster (0/1).
    out_csv : str
        CSV output path.
    """
    with rasterio.open(mask_path) as src:
        mask = src.read(1)
        pixel_area = abs(src.transform.a) * abs(src.transform.e)  # m^2 if projected in meters
        water_pixels = (mask == 1).sum()
        water_area_m2 = water_pixels * pixel_area
        with open(out_csv, 'w', newline='') as f:
            w = csv.writer(f)
            w.writerow(['water_pixels', 'pixel_area_m2', 'total_water_area_m2'])
            w.writerow([int(water_pixels), float(pixel_area), float(water_area_m2)])
