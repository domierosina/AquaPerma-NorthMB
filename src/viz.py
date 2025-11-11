
"""Quick visualization utilities."""
import numpy as np
import rasterio
import matplotlib.pyplot as plt

def save_quicklook(raster_path: str, out_png: str):
    """Save a simple normalized single-band quicklook to PNG."""
    with rasterio.open(raster_path) as src:
        arr = src.read(1).astype('float32')
        finite = np.isfinite(arr)
        vmin = np.percentile(arr[finite], 2) if finite.any() else 0
        vmax = np.percentile(arr[finite], 98) if finite.any() else 1
        arr = np.clip((arr - vmin) / (vmax - vmin + 1e-6), 0, 1)

    plt.figure()
    plt.imshow(arr)
    plt.axis('off')
    plt.tight_layout()
    plt.savefig(out_png, dpi=200, bbox_inches='tight')
    plt.close()
