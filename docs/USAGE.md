
# Usage Guide

This guide shows a typical workflow from inputs to outputs.

1. Prepare `config/config.yaml`:
   - Set AOI path (e.g., `data/aoi/aoi.geojson`)
   - Temporal window (start/end)
   - Source toggles and raster CRS/resolution

2. Place input rasters in `data/raw/`.

3. Compute NDWI for two time points:
   ```bash
   python -m src.cli ndwi --input <green.tif> --nir <nir.tif> --out data/processed/ndwi_2019.tif
   python -m src.cli ndwi --input <green2.tif> --nir <nir2.tif> --out data/processed/ndwi_2024.tif
   ```

4. Generate change map:
   ```bash
   python -m src.cli change-detect --t1 data/processed/ndwi_2019.tif --t2 data/processed/ndwi_2024.tif        --out data/processed/ndwi_change_2019_2024.tif --threshold 0.1
   ```

5. Quicklook PNG for reports:
   ```bash
   python -m src.cli quicklook --raster data/processed/ndwi_change_2019_2024.tif        --out_png docs/figures/change_preview.png
   ```

6. Summarize water mask area:
   ```bash
   python -m src.cli summarize --mask data/processed/water_mask_2024.tif        --out_csv data/processed/water_area_2024.csv
   ```

Troubleshooting tips:
- Check raster alignment/CRS with QGIS.
- Adjust thresholds in config or CLI arguments.
- Verify nodata values and band ordering.
