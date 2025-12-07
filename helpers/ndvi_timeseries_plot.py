#!/usr/bin/env python3
"""
ndvi_timeseries_plot.py

Run this in a notebook or python -i to get quick plots and check values

Usage:
    python tests/ndvi_timeseries_plot.py

Notes:

"""

import re
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


csv = Path("/Users/domenica/Desktop/AquaPerma-NorthMB/data/processed/landsat_processed/landsat_indices_summary.csv")
df = pd.read_csv(csv)

# try to extract YYYYMMDD from scene string
def extract_date(scene_name):
    # common Landsat pattern: ..._YYYYMMDD_...
    m = re.search(r"_(\d{8})_", scene_name)
    if m:
        return pd.to_datetime(m.group(1), format="%Y%m%d")
    # fallback: try any 8-digit group
    m2 = re.search(r"(\d{4})(\d{2})(\d{2})", scene_name)
    if m2:
        return pd.to_datetime("".join(m2.groups()), format="%Y%m%d")
    return pd.NaT

df['acq_date'] = df['scene'].apply(extract_date)
df = df.sort_values('acq_date').reset_index(drop=True)

# if date parsing failed for all, you can supply manual dates
if df['acq_date'].isna().all():
    print("Warning: no dates parsed from scene names. Consider adding date column to CSV.")
else:
    # Plot
    x = df['acq_date']
    y = df['ndvi_mean'].astype(float)

    plt.figure(figsize=(8,4))
    plt.plot(x, y, marker='o', linestyle='-', label='Mean NDVI (Landsat)')
    # linear trend
    ok = ~np.isnan(y)
    if ok.sum() >= 2:
        xo = (x.astype('int64') // 10**9).values[ok]  # seconds since epoch
        coefs = np.polyfit(xo, y.values[ok], deg=1)
        trend = np.polyval(coefs, xo)
        plt.plot(x.values[ok], trend, linestyle='--', label='Linear trend')
    plt.xlabel('Acquisition date')
    plt.ylabel('Mean NDVI')
    plt.title('NDVI time series over AOI')
    plt.grid(alpha=0.3)
    plt.legend()
    plt.tight_layout()

    out_fig = Path("/Users/domenica/Desktop/AquaPerma-NorthMB/outputs/figures")
    out_fig.mkdir(parents=True, exist_ok=True)
    fname = out_fig / "ndvi_timeseries.png"
    plt.savefig(fname, dpi=300)
    print("Saved figure:", fname)
    plt.show()
