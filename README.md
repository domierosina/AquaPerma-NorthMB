
# AquaPerma-NorthMB
NDWI-based surface water change detection in Northern Manitoba (GACS 7205)

---
## 🧭 Overview
This repository provides a compact, reproducible pipeline to **detect and visualize surface water changes** in **Northern Manitoba** using **multi-temporal satellite imagery** and **NDWI**. It emphasizes a workflow that runs on modest hardware while remaining transparent and extensible.

### Key Features
- NDWI computation and water mask creation for time slices
- Simple **temporal change detection** via difference/thresholding
- CLI commands for NDWI, change detection, quicklooks, and summary stats
- Clean folder structure and configuration-driven paths
- Hooks for Landsat DSWE and Sentinel-2 inputs
- CI pipeline (pytest + flake8) for basic quality checks

---

## 🗂 Repository Structure
```
AquaPerma-NorthMB/
├── LICENSE
├── README.md
├── environment.yml
├── data/
│   ├── README.md                      # Data management policy
│   ├── aoi/                           # Area of interest files
│   ├── raw/
│   └── processed/
├── docs/
│   ├── USAGE.md                       # Step-by-step usage guide
│   └── figures/
├── notebooks/
│   └── 00_sanity_check.ipynb          # Optional EDA placeholder
├── scripts/
│   └── prepare_example_data.py        # Guidance for local test data
├── src/
│   ├── __init__.py
│   ├── cli.py
│   ├── ndwi.py
│   ├── change_detection.py
│   ├── preprocessing.py
│   ├── stats.py
│   └── viz.py
└── tests/
    └── test_ndwi.py
```

---

## ⚙️ Environment Setup
To ensure a reproducible environment, all necessary dependencies are specified in the environment.yml file. We recommend using Conda (Miniconda or Anaconda) to create and manage the environment named aquaperma.

###  🐍 Using Conda
Follow these steps to create and activate the project environment:

Create the environment from the YAML file:

```bash
conda env create -f environment.yml
```

Activate the environment:

```bash
conda activate aquaperma
```

Deactivate the environment when you are finished working:
```bash
conda deactivate
```
---

## 🔧 Configuration
1. Copy `config/config.example.yaml` to `config/config.yaml` and edit:
   - Paths (`data_dir`, etc.)
   - AOI (`aoi.geojson` path)
   - Temporal window (`start`, `end`)
   - Source toggles (`landsat_dswe`, `sentinel2`)
   - Raster CRS and resolution
2. Place inputs under `data/raw/` (e.g., `landsat_dswe/` or `sentinel2/`).

---

## ▶️ Usage (CLI)
Compute NDWI and change maps driven by your config:
```bash
python -m src.cli --config config/config.yaml ndwi   --input data/raw/landsat_dswe/example_green.tif   --nir data/raw/landsat_dswe/example_nir.tif   --out data/processed/ndwi_example.tif

python -m src.cli --config config/config.yaml change-detect   --t1 data/processed/ndwi_2019.tif   --t2 data/processed/ndwi_2024.tif   --out data/processed/ndwi_change_2019_2024.tif   --threshold 0.1
```

Generate a quicklook PNG from any raster:
```bash
python -m src.cli quicklook   --raster data/processed/ndwi_example.tif   --out_png docs/figures/ndwi_example.png
```

Summarize a binary water mask (0/1) to CSV:
```bash
python -m src.cli summarize   --mask data/processed/water_mask_2024.tif   --out_csv data/processed/water_area_2024.csv
```

---

## 🧪 Quality (CI), Linting, and Tests
- Run tests locally:
```bash
pytest -q
```
- Lint the code:
```bash
flake8 src
```
- The GitHub Action in `.github/workflows/ci.yml` runs both on every push/PR.

---

## 🗄 Data Management Policy
See `data/README.md` for:
- Raw vs. interim vs. processed directories
- Recommended filenames and metadata
- Handling large files (Git LFS vs. external storage)
- Reproducibility tips

- RawData is currently hosted on OneDrive

---

## 📝 Citation
TBD. 

---

## 🙏 Acknowledgements
Built for GACS 7205 coursework. Inspired by the structure of the example repos and uses Rasterio/GeoPandas/OpenCV/scikit-image/QGIS.
