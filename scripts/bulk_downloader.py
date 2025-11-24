#!/usr/bin/env python3
"""
Bulk download Landsat 8 Collection 2 Level-2 and Sentinel-2 L2A scenes
for the Keeyask/Gillam project.

Landsat:
  - Uses USGS M2M via the `usgsm2m` CLI.
  - Dataset: landsat_ot_c2_l2
  - Scene IDs are hard-coded for 2016–2021, Path 34 Row 20.

Sentinel-2:
  - Uses Copernicus SciHub via `sentinelsat`.
  - Product type: S2MSI2A
  - Product identifiers are hard-coded for tile 15XVS, 2016–2021.

Credentials
-----------
Landsat (USGS M2M / EarthExplorer):
  - Read from environment variables if set:
        USGS_USERNAME
        USGS_PASSWORD
    otherwise prompted interactively.

Sentinel-2 (Copernicus SciHub):
  - Read from environment variables if set:
        COPERNICUS_USERNAME
        COPERNICUS_PASSWORD
    otherwise prompted interactively.

Outputs
-------
Landsat bundles -> data/raw/landsat/
Sentinel-2 products -> data/raw/sentinel/

Author: Domenica Burroughs
"""

from __future__ import annotations

import getpass
import os
import subprocess
from pathlib import Path
from typing import List

from sentinelsat import SentinelAPI


# ---------------------------------------------------------------------
# 1. Scene lists
# ---------------------------------------------------------------------
LANDSAT_SCENES: List[str] = [
    "LC08_L2SP_034020_20160711_20200905_02_T1",
    "LC08_L2SP_034020_20170730_20200902_02_T1",
    "LC08_L2SP_034020_20180816_20200822_02_T1",
    "LC08_L2SP_034020_20190719_20200820_02_T1",
    "LC08_L2SP_034020_20200705_20200912_02_T1",
    "LC08_L2SP_034020_20210724_20220128_02_T1",
]

SENTINEL_SCENES: List[str] = [
    "S2A_MSIL2A_20160720T165911_N0204_R112_T15XVS",
    "S2A_MSIL2A_20170809T165921_N0205_R112_T15XVS",
    "S2A_MSIL2A_20180818T165921_N0208_R112_T15XVS",
    "S2B_MSIL2A_20190722T165919_N0213_R112_T15XVS",
    "S2A_MSIL2A_20200802T165901_N0214_R112_T15XVS",
    "S2B_MSIL2A_20210725T165919_N0301_R112_T15XVS",
]

# Dataset / paths
LANDSAT_DATASET = "landsat_ot_c2_l2"
LANDSAT_OUT_DIR = Path("data/raw/landsat")
SENTINEL_OUT_DIR = Path("data/raw/sentinel")


# ---------------------------------------------------------------------
# 2. Credential helpers
# ---------------------------------------------------------------------
def get_usgs_credentials() -> tuple[str, str]:
    """Get USGS EarthExplorer / M2M credentials from env or prompt."""
    username = os.getenv("USGS_USERNAME")
    password = os.getenv("USGS_PASSWORD")

    if not username:
        username = input("USGS EarthExplorer username: ").strip()
    if not password:
        password = getpass.getpass("USGS EarthExplorer password (M2M): ")

    return username, password


def get_copernicus_credentials() -> tuple[str, str]:
    """Get Copernicus SciHub credentials from env or prompt."""
    username = os.getenv("COPERNICUS_USERNAME")
    password = os.getenv("COPERNICUS_PASSWORD")

    if not username:
        username = input("Copernicus SciHub username: ").strip()
    if not password:
        password = getpass.getpass("Copernicus SciHub password: ")

    return username, password


# ---------------------------------------------------------------------
# 3. Landsat bulk download via usgsm2m
# ---------------------------------------------------------------------
def download_landsat_bulk() -> None:
    """Bulk download all Landsat scenes using the `usgsm2m` CLI."""
    LANDSAT_OUT_DIR.mkdir(parents=True, exist_ok=True)
    username, password = get_usgs_credentials()

    cmd = [
        "usgsm2m",
        "download",
        "-u",
        username,
        "-p",
        password,
        "-d",
        LANDSAT_DATASET,
        "-o",
        str(LANDSAT_OUT_DIR),
    ] + LANDSAT_SCENES

    print("\n=== Landsat 8 bulk download (USGS M2M) ===\n")
    print("Command (without passwords):")
    print(" ".join(cmd[:7]) + " ... <scene IDs omitted> ...")
    print("\nThis may take a while depending on your connection.\n")

    try:
        subprocess.run(cmd, check=True)
        print("\n Landsat download complete.")
        print(f"Files saved under: {LANDSAT_OUT_DIR.resolve()}")
    except FileNotFoundError:
        print(
            "\n Could not find the `usgsm2m` command.\n"
            "Make sure you installed it in this environment:\n"
            "    conda activate aquaperma\n"
            "    pip install usgsm2m\n"
        )
    except subprocess.CalledProcessError as exc:
        print("\n usgsm2m reported an error.")
        print(f"Return code: {exc.returncode}")
        print("Check your username/password and scene IDs, then try again.")


# ---------------------------------------------------------------------
# 4. Sentinel-2 bulk download via sentinelsat
# ---------------------------------------------------------------------
def download_sentinel_bulk() -> None:
    """Bulk download all Sentinel-2 L2A scenes via Copernicus SciHub."""
    SENTINEL_OUT_DIR.mkdir(parents=True, exist_ok=True)
    username, password = get_copernicus_credentials()

    print("\n=== Sentinel-2 bulk download (Copernicus SciHub) ===\n")

    api = SentinelAPI(
        user=username,
        password=password,
        api_url="https://scihub.copernicus.eu/dhus",
    )

    for identifier in SENTINEL_SCENES:
        print(f"\nSearching for product: {identifier}")
        # Query by unique identifier (product title) + product type
        products = api.query(
            identifier=identifier,
            producttype="S2MSI2A",
        )

        if not products:
            print(f" No product found for identifier: {identifier}")
            continue

        # Get the first (and should be only) product
        product_id = next(iter(products.keys()))
        print(f"Found product ID: {product_id}. Starting download...")

        try:
            api.download(product_id, directory_path=str(SENTINEL_OUT_DIR))
            print(f" Downloaded Sentinel-2 product: {identifier}")
        except Exception as exc:  # broad catch is fine for a CLI helper
            print(f" Failed to download {identifier}: {exc}")

    print("\nSentinel-2 download routine finished.")
    print(f"Files (SAFE or ZIP) saved under: {SENTINEL_OUT_DIR.resolve()}")


# ---------------------------------------------------------------------
# 5. Main
# ---------------------------------------------------------------------
def main() -> None:
    print("Starting bulk downloads for Landsat 8 + Sentinel-2 (2016–2021)...")

    download_landsat_bulk()
    download_sentinel_bulk()

    print("\n All download routines finished. "
          "Next: unzip/extract and run your clipping script.")


if __name__ == "__main__":
    main()
