
from src.ndwi import compute_ndwi
import numpy as np

def test_compute_ndwi_basic():
    g = np.array([[0.6, 0.4],[0.2, 0.0]], dtype='float32')
    n = np.array([[0.2, 0.4],[0.2, 0.0]], dtype='float32')
    ndwi = compute_ndwi(g, n)
    assert ndwi.shape == g.shape
    # Where green==nir, NDWI should be 0 (except handling division by zero at 0,0)
    assert np.isclose(ndwi[0,1], 0.0, atol=1e-5)
