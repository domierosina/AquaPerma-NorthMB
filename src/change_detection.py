
"""Temporal change detection for NDWI rasters.

Implements a simple differencing approach:
    change = NDWI_t2 - NDWI_t1

Positive values suggest water expansion; negative values suggest contraction.
Optionally writes a binary threshold mask to highlight significant changes.
"""
import numpy as np
import rasterio

def change_difference(t1_path: str, t2_path: str, out_path: str, threshold: float | None = None, cfg=None):
    """Compute NDWI difference map and save to GeoTIFF.

    Parameters
    ----------
    t1_path : str
        Path to NDWI raster at time 1.
    t2_path : str
        Path to NDWI raster at time 2.
    out_path : str
        Output path for the difference raster (float32).
    threshold : float | None
        If provided, also writes a UInt8 mask where |change| >= threshold.
    cfg : dict | None
        Optional configuration dictionary.

    Returns
    -------
    None
    """
    with rasterio.open(t1_path) as s1, rasterio.open(t2_path) as s2:
        a = s1.read(1).astype('float32')
        b = s2.read(1).astype('float32')
        change = b - a  # positive => likely water expansion

        meta = s1.meta.copy()
        meta.update(dtype='float32', count=1, nodata=np.nan)
        with rasterio.open(out_path, 'w', **meta) as dst:
            dst.write(change, 1)

        if threshold is not None:
            mask = (np.abs(change) >= threshold).astype('uint8')
            tmask_path = out_path.replace('.tif', f'_thr{threshold}.tif')
            m = meta.copy()
            m.update(dtype='uint8', nodata=0)
            with rasterio.open(tmask_path, 'w', **m) as mdst:
                mdst.write(mask, 1)
