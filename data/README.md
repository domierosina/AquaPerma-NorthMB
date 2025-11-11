
# Data Management

## Folders
- `raw/`      : Original, immutable files (e.g., DSWE rasters, Sentinel-2 bands). EXCLUDED from Git.
- `interim/`  : Temporary outputs created during processing.
- `processed/`: Final products (NDWI maps, change maps, summaries).

## Filenaming
Use informative names:
```
landsat_dswe_<PATH/SCENE>_<YYYYMMDD>.tif
sentinel2_L2A_<TILE>_<YYYYMMDD>_B03.tif  # green
sentinel2_L2A_<TILE>_<YYYYMMDD>_B08.tif  # NIR
ndwi_<YYYY>.tif
ndwi_change_<YYYY1>_<YYYY2>.tif
```
Include a companion `.json` or `.txt` with metadata if helpful.

## Large Files
- Prefer **external storage** (SSD) or **Git LFS** for big rasters.
- If using Git LFS:
  - Install LFS: `git lfs install`
  - Track patterns: `git lfs track "*.tif"`
  - Commit `.gitattributes`

## Reproducibility
- Keep `config/config.yaml` under version control.
- Document AOI, CRS, and temporal window.
- Record environment via `env.yml` or `pip freeze > requirements-lock.txt`.
