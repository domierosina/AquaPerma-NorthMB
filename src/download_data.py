#!/usr/bin/env python3
"""
Download Landsat 8 + DSWE + Sentinel-2 L2A scenes for the Gillam/Keeyask AOI (2016–2021)
and clip them to a local AOI polygon. Outputs are stored in data/raw/.

Author: Domenica Burroughs
Date: 2025.11.23
"""

import os
import requests
import zipfile
from pathlib import Path
import rasterio
from rasterio.mask import mask
import json

# ---------------------------------------------------------
# 1. AOI (Keeyask Reservoir / Gillam Area)
# ---------------------------------------------------------
AOI_GEOJSON = {
    "type": "Polygon",
    "coordinates": [[
        [-94.799, 56.32],
        [-94.799, 56.05],
        [-94.30, 56.05],
        [-94.30, 56.32],
        [-94.799, 56.32]
    ]]
}


# ---------------------------------------------------------
# 2. Scene Lists (curated earlier)
# ---------------------------------------------------------
LANDSAT_SCENES = [
    "LC08_L2SP_034020_20160711_20200905_02_T1",
    "LC08_L2SP_034020_20170730_20200902_02_T1",
    "LC08_L2SP_034020_20180816_20200822_02_T1",
    "LC08_L2SP_034020_20190719_20200820_02_T1",
    "LC08_L2SP_034020_20200705_20200912_02_T1",
    "LC08_L2SP_034020_20210724_20220128_02_T1"
]

SENTINEL_SCENES = [
    "S2A_MSIL2A_20160720T165911_N0204_R112_T15XVS",
    "S2A_MSIL2A_20170809T165921_N0205_R112_T15XVS",
    "S2A_MSIL2A_20180818T165921_N0208_R112_T15XVS",
    "S2B_MSIL2A_20190722T165919_N0213_R112_T15XVS",
    "S2A_MSIL2A_20200802T165901_N0214_R112_T15XVS",
    "S2B_MSIL2A_20210725T165919_N0301_R112_T15XVS"
]

# ---------------------------------------------------------
# 3. Helper Functions
# ---------------------------------------------------------
def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)
    return path


def download_file(url: str, dest: Path):
    """Download a single file with streaming."""
    print(f"Downloading: {url}")
    r = requests.get(url, stream=True)
    if r.status_code != 200:
        print(f"Failed: HTTP {r.status_code}")
        return None
    with open(dest, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    return dest


def clip_raster_to_aoi(infile: Path, outfile: Path, aoi_geojson: dict):
    """Clip raster to AOI polygon."""
    with rasterio.open(infile) as src:
        out_img, out_transform = mask(
            src,
            [aoi_geojson],
            crop=True
        )
        out_meta = src.meta.copy()

        out_meta.update({
            "height": out_img.shape[1],
            "width": out_img.shape[2],
            "transform": out_transform
        })

        with rasterio.open(outfile, "w", **out_meta) as dst:
            dst.write(out_img)

    print(f"Clipped: {outfile}")


# ---------------------------------------------------------
# 4. Landsat Download Function
# ---------------------------------------------------------
def download_landsat_scene(scene_id: str, outdir: Path):
    """
    Download Landsat 8 Surface Reflectance + DSWE from USGS S3 bucket.
    """
    base_url = f"https://landsat-pds.s3.amazonaws.com/c1/L8/{scene_id[10:13]}/{scene_id[13:16]}/{scene_id}"

    target_dir = ensure_dir(outdir / scene_id)
    print(f"\n=== Downloading Landsat Scene: {scene_id} ===")

    bands = ["B3.TIF", "B5.TIF"]  # Green + NIR
    qa = "QA_PIXEL.TIF"

    for suffix in bands + [qa]:
        url = f"{base_url}/{scene_id}_{suffix}"
        dest = target_dir / f"{scene_id}_{suffix}"
        download_file(url, dest)

    return target_dir


# ---------------------------------------------------------
# 5. Sentinel-2 Download Function
# ---------------------------------------------------------
def download_sentinel_scene(scene_id: str, outdir: Path):
    """
    Download Sentinel-2 L2A bands (B03 + B08 only) using AWS bucket.
    """
    tile = "15/XV/S"  # tile structure
    target_dir = ensure_dir(outdir / scene_id)

    print(f"\n=== Downloading Sentinel-2 Scene: {scene_id} ===")

    # Only the Green (B03) & NIR (B08) JP2 files
    band_files = ["B03.jp2", "B08.jp2"]

    for bf in band_files:
        url = (
            f"https://sentinel-cogs.s3.us-west-2.amazonaws.com/"
            f"sentinel-s2-l2a-cogs/{scene_id}/{bf}"
        )
        dest = target_dir / bf
        download_file(url, dest)

    return target_dir


# ---------------------------------------------------------
# 6. Main 
# ---------------------------------------------------------
def run_pipeline():
    landsat_out = Path("data/raw/landsat")
    sentinel_out = Path("data/raw/sentinel")
    clipped_out = Path("data/processed/clipped")
    ensure_dir(landsat_out)
    ensure_dir(sentinel_out)
    ensure_dir(clipped_out)

    # --- DOWNLOAD LANDSAT SCENES ---
    for scene in LANDSAT_SCENES:
        folder = download_landsat_scene(scene, landsat_out)

        # Clip the two needed bands
        for tif in folder.glob("*.TIF"):
            clip_raster_to_aoi(
                tif,
                clipped_out / f"{scene}_{tif.name}",
                AOI_GEOJSON
            )

    # --- DOWNLOAD SENTINEL SCENES ---
    for scene in SENTINEL_SCENES:
        folder = download_sentinel_scene(scene, sentinel_out)

        for jp2 in folder.glob("*.jp2"):
            clip_raster_to_aoi(
                jp2,
                clipped_out / f"{scene}_{jp2.name}",
                AOI_GEOJSON
            )


# ---------------------------------------------------------
# Run when executed directly
# ---------------------------------------------------------
if __name__ == "__main__":
    run_pipeline()
    print("\nAll downloads + clipping complete!")
