#!/usr/bin/env python3
"""
diagnose_sentinel_presence.py

Search multiple public Sentinel mirrors (AWS COGS, AWS legacy L2A/L1C, and GCP public)
for MGRS tiles and dates (within a +/- window). Prints any matched prefixes and direct URLs.

Requires:
    pip install boto3 requests
Usage:
    python diagnose_sentinel_presence.py
"""

import os
from datetime import datetime, timedelta
from botocore.config import Config
from botocore import UNSIGNED
import boto3
import requests

# Configure anonymous AWS S3 client
s3 = boto3.client('s3', config=Config(signature_version=UNSIGNED))

# Inputs: tiles and target Landsat dates
tiles = ['14VMJ', '14VNJ']
landsat_dates = [
    '2016-07-11',
    '2017-07-30',
    '2018-08-16',
    '2019-07-19',
    '2020-07-05',
    '2021-07-24'
]

# Buckets/roots to try
AWS_COGS_BUCKET = "sentinel-cogs"
AWS_COGS_ROOT = "sentinel-s2-l2a-cogs"   # COGS mirror (non-zero-padded path)
AWS_L2A_BUCKET = "sentinel-s2-l2a"       # legacy L2A (zero-padded)
AWS_L1C_BUCKET = "sentinel-s2-l1c"       # legacy L1C (zero-padded)
GCP_BASE = "https://storage.googleapis.com/gcp-public-data-sentinel-2"

# How many days to search around each Landsat date
WINDOW_DAYS = 30

def mgrs_parts(tile):
    utm = tile[:2]
    lat = tile[2]
    sq = tile[3:]
    return utm, lat, sq

def try_aws_prefix_list(bucket, prefix):
    """Return True + sample keys if listing returns content."""
    try:
        resp = s3.list_objects_v2(Bucket=bucket, Prefix=prefix, MaxKeys=5)
    except Exception as e:
        return False, f"ERROR ({e})"
    if resp.get('KeyCount', 0) > 0 or resp.get('CommonPrefixes'):
        keys = []
        if resp.get('CommonPrefixes'):
            keys = [p['Prefix'] for p in resp['CommonPrefixes']]
        else:
            keys = [c['Key'] for c in resp.get('Contents', [])]
        return True, keys
    return False, None

def try_gcp_http(prefix_path):
    """HEAD request to check if GCP path exists (try metadata.json and index)."""
    # Candidate URLs to check under prefix
    candidates = [
        f"{GCP_BASE}/{prefix_path}metadata.xml",
        f"{GCP_BASE}/{prefix_path}metadata.json",
        f"{GCP_BASE}/{prefix_path}index.html",
    ]
    found = []
    for url in candidates:
        try:
            r = requests.head(url, timeout=10)
            if r.status_code == 200:
                found.append(url)
        except Exception:
            pass
    # Also try listing by fetching bucket prefix (not easily listable via HTTP) - skip
    return found

def check_all_for_tile_date(tile, target_dt):
    utm, lat, sq = mgrs_parts(tile)
    yyyy = f"{target_dt.year}"
    mm_z = f"{target_dt.month:02d}"
    dd_z = f"{target_dt.day:02d}"
    mm_nz = f"{target_dt.month}"
    dd_nz = f"{target_dt.day}"

    candidate_prefixes = []

    # 1) AWS COGS style (non-zero padded)
    candidate_prefixes.append((AWS_COGS_BUCKET, f"{AWS_COGS_ROOT}/{utm}/{lat}/{sq}/{yyyy}/{mm_nz}/{dd_nz}/"))
    candidate_prefixes.append((AWS_COGS_BUCKET, f"{AWS_COGS_ROOT}/{utm}/{lat}/{sq}/{yyyy}/{mm_z}/{dd_z}/"))

    # 2) AWS legacy tiles (zero-padded)
    candidate_prefixes.append((AWS_L2A_BUCKET, f"tiles/{utm}/{lat}/{sq}/{yyyy}/{mm_z}/{dd_z}/"))
    candidate_prefixes.append((AWS_L1C_BUCKET, f"tiles/{utm}/{lat}/{sq}/{yyyy}/{mm_z}/{dd_z}/"))

    # For each candidate, check AWS listing and GCP HTTP
    results = []
    for bucket, prefix in candidate_prefixes:
        ok, sample = try_aws_prefix_list(bucket, prefix)
        if ok:
            # prepare direct HTTP/CORS URL for convenience (COGS uses sentinel-cogs.s3.amazonaws...)
            if bucket == AWS_COGS_BUCKET:
                http_base = f"https://{bucket}.s3.amazonaws.com/{prefix}"
            else:
                http_base = f"https://{bucket}.s3.amazonaws.com/{prefix}"
            results.append({
                'source': 'AWS',
                'bucket': bucket,
                'prefix': prefix,
                'http_example': http_base,
                'sample': sample
            })

    # Also check GCP HTTP paths (non-zero and zero padded)
    gcp_prefix_nz = f"tiles/{utm}/{lat}/{sq}/{yyyy}/{mm_nz}/{dd_nz}/"
    gcp_prefix_z = f"tiles/{utm}/{lat}/{sq}/{yyyy}/{mm_z}/{dd_z}/"
    gcp_found_nz = try_gcp_http(gcp_prefix_nz)
    gcp_found_z = try_gcp_http(gcp_prefix_z)
    if gcp_found_nz:
        results.append({'source': 'GCP_HTTP', 'prefix': gcp_prefix_nz, 'hits': gcp_found_nz})
    if gcp_found_z:
        results.append({'source': 'GCP_HTTP', 'prefix': gcp_prefix_z, 'hits': gcp_found_z})

    return results

if __name__ == "__main__":
    overall_found = False
    for tile in tiles:
        print(f"\n=== TILE {tile} ===")
        for ld in landsat_dates:
            target = datetime.strptime(ld, "%Y-%m-%d")
            print(f"\nTarget Landsat date: {ld} (search +/- {WINDOW_DAYS} days)")
            found_any = []
            for delta in range(-WINDOW_DAYS, WINDOW_DAYS + 1):
                dt = target + timedelta(days=delta)
                res = check_all_for_tile_date(tile, dt)
                if res:
                    overall_found = True
                    found_any.extend([ (dt.strftime("%Y-%m-%d"), r) for r in res ])
            if not found_any:
                print("  No matches found in AWS COGS, AWS legacy L2A/L1C, or GCP HTTP for +/- window.")
            else:
                print(f"  Found {len(found_any)} candidate(s):")
                for date_str, r in found_any:
                    if r['source'] == 'AWS':
                        print(f"   - {r['source']} {r['bucket']} prefix={r['prefix']} (check: {r['http_example']})")
                        if r['sample']:
                            # print sample keys or prefixes
                            for s in r['sample'][:5]:
                                print(f"       sample: {s}")
                    else:
                        print(f"   - {r['source']} prefix={r['prefix']}")
                        for h in r['hits']:
                            print(f"       http: {h}")
    if not overall_found:
        print("\nNo Sentinel entries found for any tile/date in the searched windows across tested mirrors.")
        print("Next recommended steps:")
        print("  1) Increase WINDOW_DAYS and re-run, e.g. WINDOW_DAYS=90")
        print("  2) Search by AOI bbox (lat/lon) instead of tile IDs — I can provide that script")
        print("  3) If you need older L1C specifically (2016), search the L1C bucket or Copernicus archive via SciHub")
    else:
        print("\nSome candidates were found. Open the printed HTTP URLs in your browser to inspect exact files / download targets.")
