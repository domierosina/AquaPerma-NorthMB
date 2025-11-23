#!/usr/bin/env python3
"""
Clip Landsat 8 and Sentinel-2 scenes for the Gillam/Keeyask AOI (2016–2021).

This script assumes that you have already manually downloaded and unzipped
the scenes into:

    data/raw/landsat/
    data/raw/sentinel/

See scene.txt for list of scenes

It will:
  - walk those folders,
  - find relevant bands (Landsat: B3/B5/QA; Sentinel: B03/B08),
  - reproject the AOI to each raster's CRS,
  - clip each raster to the AOI, and
  - save the results into data/processed/clipped/.

Author: Domenica Burroughs
Date: 2025.11.23
"""

from pathlib import Path
from typing import Dict, Iterable

import rasterio
from rasterio.mask import mask
from rasterio.warp import transform_geom

# -------------------------------------------------------------------
# 1. AOI definition (Keeyask / Gillam area) in WGS84
# -------------------------------------------------------------------
AOI_WGS84: Dict = {
    "type": "Polygon",
    "coordinates": [[
        [-94.799, 56.32],
        [-94.799, 56.05],
        [-94.30, 56.05],
        [-94.30, 56.32],
        [-94.799, 56.32]
    ]]
}

LANDSAT_ROOT = Path("data/raw/landsat")
SENTINEL_ROOT = Path("data/raw/sentinel")
CLIPPED_ROOT = Path("data/processed/clipped")


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def clip_raster_to_aoi(infile: Path, outfile: Path, aoi_wgs84: Dict) -> None:
    """Clip a raster to AOI, reprojecting AOI to the raster CRS."""
    with rasterio.open(infile) as src:
        aoi_in_crs = transform_geom("EPSG:4326", src.crs, aoi_wgs84)
        out_img, out_transform = mask(src, [aoi_in_crs], crop=True)

        out_meta = src.meta.copy()
        out_meta.update(
            height=out_img.shape[1],
            width=out_img.shape[2],
            transform=out_transform,
        )

        ensure_dir(outfile.parent)
        with rasterio.open(outfile, "w", **out_meta) as dst:
            dst.write(out_img)

    print(f"✔ Clipped: {infile.name} → {outfile}")


def find_files(root: Path, patterns: Iterable[str]) -> Iterable[Path]:
    """Recursively find files under 'root' matching any of the glob patterns."""
    for pattern in patterns:
        for p in root.rglob(pattern):
            yield p


def clip_landsat_scenes() -> None:
    """Clip Landsat B3/B5/QA/DSWE bands under data/raw/landsat/."""
    if not LANDSAT_ROOT.exists():
        print(f"⚠ Landsat root not found: {LANDSAT_ROOT.resolve()}")
        return

    print("\n=== Clipping Landsat scenes ===")
    patterns = ["*B3*.TIF", "*B5*.TIF", "*QA_PIXEL*.TIF", "*DSWE*.TIF"]

    for infile in find_files(LANDSAT_ROOT, patterns):
        relative = infile.relative_to(LANDSAT_ROOT)
        outfile = CLIPPED_ROOT / "landsat" / relative
        clip_raster_to_aoi(infile, outfile, AOI_WGS84)


def clip_sentinel_scenes() -> None:
    """Clip Sentinel-2 B03/B08 bands under data/raw/sentinel/."""
    if not SENTINEL_ROOT.exists():
        print(f"⚠ Sentinel root not found: {SENTINEL_ROOT.resolve()}")
        return

    print("\n=== Clipping Sentinel-2 scenes ===")
    patterns = ["*B03*.jp2", "*B08*.jp2", "*B03*.tif", "*B08*.tif"]

    for infile in find_files(SENTINEL_ROOT, patterns):
        relative = infile.relative_to(SENTINEL_ROOT)
        outfile = CLIPPED_ROOT / "sentinel" / relative.with_suffix(".tif")
        clip_raster_to_aoi(infile, outfile, AOI_WGS84)


def main() -> None:
    ensure_dir(CLIPPED_ROOT)
    clip_landsat_scenes()
    clip_sentinel_scenes()
    print("\n Finished clipping all available scenes.")


if __name__ == "__main__":
    main()
