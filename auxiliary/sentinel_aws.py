#!/usr/bin/env python3
"""
sentinel_aws_search_window.py

Search AWS public Sentinel-2 buckets (L2A preferred, fallback to L1C)
for products covering given MGRS tiles on or near target dates.

Drops back to a +/- window (days) and returns nearest matches.

Usage:
    python tests/sentinel_aws_search_window.py

Notes:
- Requires boto3: pip install boto3
- No AWS credentials required (uses anonymous access)
- SAFE folders are big; only download when you set download=True
"""

import os
from datetime import datetime, timedelta
from botocore.config import Config
from botocore import UNSIGNED
import boto3

# Config & buckets
S3_L2A = "sentinel-s2-l2a"
S3_L1C = "sentinel-s2-l1c"
s3 = boto3.client('s3', config=Config(signature_version=UNSIGNED))

# Inputs: tiles and landsat dates
tiles = ['14VMJ', '14VNJ']
landsat_dates = [
    '2016-07-11',
    '2017-07-30',
    '2018-08-16',
    '2019-07-19',
    '2020-07-05',
    '2021-07-24'
]

# How many days around the target to look (change as needed)
WINDOW_DAYS = 30

def mgrs_to_s3_path(tile_code):
    utm = tile_code[:2]
    latband = tile_code[2]
    sq = tile_code[3:]
    return utm, latband, sq

def list_prefixes_for_date(bucket, tile, dt):
    utm, latband, sq = mgrs_to_s3_path(tile)
    yyyy = f"{dt.year:04d}"
    mm = f"{dt.month:02d}"
    dd = f"{dt.day:02d}"
    prefix = f"tiles/{utm}/{latband}/{sq}/{yyyy}/{mm}/{dd}/"
    resp = s3.list_objects_v2(Bucket=bucket, Prefix=prefix, Delimiter='/')
    prefixes = []
    if resp.get('CommonPrefixes'):
        prefixes = [p['Prefix'] for p in resp['CommonPrefixes']]
    elif resp.get('Contents'):
        # derive top-level SAFE-like folder names from returned keys
        folders = set()
        for obj in resp['Contents']:
            key = obj['Key']
            # SAFE folder structure: tiles/.../<YYYY>/<MM>/<DD>/<PRODUCT>/...
            parts = key.split('/')
            if len(parts) > 6:
                folders.add('/'.join(parts[:7]) + '/')
        prefixes = sorted(folders)
    return prefix, prefixes

def search_tile_date(tile, target_date_str, window_days=3, prefer_buckets=(S3_L2A, S3_L1C)):
    target_dt = datetime.strptime(target_date_str, "%Y-%m-%d")
    matches = []
    for bucket in prefer_buckets:
        for delta in range(-window_days, window_days+1):
            dt = target_dt + timedelta(days=delta)
            prefix_root, prefixes = list_prefixes_for_date(bucket, tile, dt)
            if prefixes:
                for p in prefixes:
                    # product date can be inferred from prefix parts
                    parts = p.split('/')
                    # safe-guard: try to find YYYY/MM/DD in path
                    try:
                        yyyy = int(parts[4])
                        mm = int(parts[5])
                        dd = int(parts[6])
                        prod_date = datetime(yyyy, mm, dd)
                    except Exception:
                        prod_date = dt  # fallback
                    matches.append({
                        'bucket': bucket,
                        'prefix': p,
                        'prod_date': prod_date,
                        'delta_days': abs((prod_date - target_dt).days)
                    })
        # If we found matches in this bucket, prefer them (don't need to check other buckets)
        if matches:
            break
    # sort by closeness to target date
    matches = sorted(matches, key=lambda x: (x['delta_days'], x['prefix']))
    return matches

def download_prefix(bucket, prefix, outdir):
    paginator = s3.get_paginator('list_objects_v2')
    os.makedirs(outdir, exist_ok=True)
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get('Contents', []):
            key = obj['Key']
            relpath = key[len(prefix):]
            if relpath == '':
                continue
            target = os.path.join(outdir, relpath)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            print(f"Downloading s3://{bucket}/{key} -> {target}")
            s3.download_file(bucket, key, target)

if __name__ == "__main__":
    # Dry run listing
    for tile in tiles:
        print(f"\n=== Tile {tile} ===")
        for ld in landsat_dates:
            print(f"\nTarget Landsat date: {ld}")
            matches = search_tile_date(tile, ld, window_days=WINDOW_DAYS)
            if not matches:
                print("  No Sentinel-2 products found in window +/-", WINDOW_DAYS, "days for L2A or L1C.")
                continue
            # print top 5 matches
            for m in matches[:5]:
                print(f"  {m['bucket']} {m['prefix']}  (prod_date={m['prod_date'].date()} delta_days={m['delta_days']})")
            # Example: to download the best match, uncomment below:
            # best = matches[0]
            # outdir = os.path.join("sentinel_downloads", tile, ld, best['prefix'].strip('/').split('/')[-1])
            # download_prefix(best['bucket'], best['prefix'], outdir)

    print("\nDone. If you want to download automatically, set download code in the script (see comments).")
