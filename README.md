
# AquaPerma-NorthMB
NDWI-based surface water change detection in Northern Manitoba (GACS/COMP 7205)

[![CI](https://github.com/USER/AquaPerma-NorthMB/actions/workflows/ci.yml/badge.svg)](#)

---

## 📌 How this repo meets the grading criteria

- **GitHub repository created:** This repository is structured and ready to publish.
- **Proper Git usage:** See **[CONTRIBUTING.md](CONTRIBUTING.md)** for branching, commits, pushes, and PR workflow. Includes commit message guidelines and a lightweight Git flow.
- **Code comments for clarity:** All modules in `src/` include docstrings and inline comments explaining inputs/outputs and assumptions.
- **Management of raw data:** `data/README.md` explains folder policy, filenames, and options for large files (Git LFS or external storage). `.gitignore` excludes large/raw data by default.
- **Well-structured README:** This document provides setup, usage, repo structure, and reproducibility notes.

> Example repos provided by instructor:
> - https://github.com/Kylelhc/BC_RadiogenomicCPDM
> - https://github.com/mattthuang/BC_RadiogenomicGAN

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
├── .github/workflows/ci.yml           # CI: lint + tests
├── .flake8                            # Linting rules
├── CONTRIBUTING.md                    # Git workflow and commit rules
├── LICENSE
├── Makefile                           # Common commands
├── README.md
├── requirements.txt
├── env.yml
├── pytest.ini
├── config/
│   └── config.example.yaml
├── data/
│   ├── README.md                      # Data management policy
│   ├── aoi/                           # Area of interest files
│   ├── raw/
│   ├── interim/
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

## ⚙️ Setup
### Option A: Conda (recommended)
```bash
conda env create -f env.yml
conda activate aquaperma-northmb
```

### Option B: pip
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
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

---

## 🔄 Git Workflow (for grading)
- Create feature branches from `main` (e.g., `feature/ndwi-thresholding`).
- Make **small, frequent commits** with descriptive messages.
- Push branches and open Pull Requests to merge into `main`.
- Tag milestone commits (e.g., `v0.1-proposal-demo`).

Details in **[CONTRIBUTING.md](CONTRIBUTING.md)**.

---

## 📝 Citation
TBD. 

---

## 🙏 Acknowledgements
Built for GACS/COMP 7205 coursework. Inspired by the structure of the example repos and uses Rasterio/GeoPandas/OpenCV/scikit-image/QGIS.
