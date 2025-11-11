
"""Preprocessing utilities (e.g., reprojection, alignment).

Use these helpers to ensure rasters share CRS, extent, transform, and shape
before NDWI computation.
"""
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling

def reproject_to_match(src_path: str, ref_path: str, out_path: str):
    """Reproject and align src to match the reference raster grid/CRS.

    Parameters
    ----------
    src_path : str
        Path to source raster (any CRS/resolution supported by GDAL).
    ref_path : str
        Path to reference raster providing desired CRS, transform, and shape.
    out_path : str
        Output path for reprojected raster.
    """
    with rasterio.open(src_path) as src, rasterio.open(ref_path) as ref:
        transform, width, height = calculate_default_transform(
            src.crs, ref.crs, ref.width, ref.height, *ref.bounds
        )
        kwargs = ref.meta.copy()
        kwargs.update({
            'crs': ref.crs,
            'transform': ref.transform,
            'width': ref.width,
            'height': ref.height
        })
        with rasterio.open(out_path, 'w', **kwargs) as dst:
            for i in range(1, src.count + 1):
                reproject(
                    source=rasterio.band(src, i),
                    destination=rasterio.band(dst, i),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=ref.transform,
                    dst_crs=ref.crs,
                    resampling=Resampling.bilinear
                )
