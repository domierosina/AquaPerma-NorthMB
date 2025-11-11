
"""NDWI utilities.

This module computes the Normalized Difference Water Index (NDWI) from
green and NIR bands. Positive NDWI values typically indicate open water.

Formulation:
    NDWI = (Green - NIR) / (Green + NIR)

Assumptions:
- Input rasters are co-registered and share the same CRS, transform, and shape.
- Nodata handling: divisions by zero or invalid pixels are set to NaN by default.

"""
import numpy as np
import rasterio

def compute_ndwi(green: np.ndarray, nir: np.ndarray, nodata: float = np.nan) -> np.ndarray:
    """Compute NDWI from in-memory green and NIR arrays.

    Parameters
    ----------
    green : np.ndarray
        2D array of the green band (float or int).
    nir : np.ndarray
        2D array of the near-infrared band.
    nodata : float, optional
        Value to assign where computation is invalid (default: NaN).

    Returns
    -------
    np.ndarray
        NDWI array (float32) with same shape as inputs.
    """
    num = green.astype('float32') - nir.astype('float32')
    den = green.astype('float32') + nir.astype('float32')
    with np.errstate(divide='ignore', invalid='ignore'):
        ndwi = np.true_divide(num, den)
        ndwi[~np.isfinite(ndwi)] = nodata
    return ndwi

def compute_ndwi_rasters(green_path: str, nir_path: str, out_path: str, cfg=None):
    """Compute NDWI from separate green and NIR rasters and save as GeoTIFF.

    Notes
    -----
    - This function does not reproject or resample; ensure rasters are aligned.
    - Use `preprocessing.reproject_to_match` if alignment is needed.
    """
    with rasterio.open(green_path) as gsrc, rasterio.open(nir_path) as nsrc:
        green = gsrc.read(1)
        nir = nsrc.read(1)
        ndwi = compute_ndwi(green, nir, nodata=np.nan)

        meta = gsrc.meta.copy()
        meta.update(dtype='float32', count=1, nodata=np.nan)
        with rasterio.open(out_path, 'w', **meta) as dst:
            dst.write(ndwi.astype('float32'), 1)
