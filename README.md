
# AquaPerma-NorthMB
NDWI-based surface water change detection in Northern Manitoba (GACS 7205)

---
## 🧭 Overview
This repository provides a compact, reproducible pipeline to **detect and visualize surface water changes** in **Northern Manitoba** using **multi-temporal satellite imagery** and **NDWI**. It emphasizes a workflow that runs on modest hardware while remaining transparent and extensible.

### Key Features
- NDWI computation and water mask creation
- Year-to-year and multi-year surface water change detection
- Per-pixel % NDWI change maps
- Sensor-specific multi-panel summaries
- Quantitative CSV summaries
- Supports Landsat 8 and Sentinel-2 imagery

---

## 🗂 Repository Structure
```
AquaPerma-NorthMB/
├── LICENSE
├── README.md
├── environment.yml
├── data/
│   ├── aoi/                           # Area of interest files
│   ├── raw/
│   └── results/
├── docs/
│   ├── Proposal.pdf
│   ├── FinalPaper.pdf
│   └── visuals/                  
├── notebooks/
│   └── 00_sanity_check.ipynb          
└── auxiliary/
    └── prepare_example_data.py        

```

---

## ⚙️ Environment Setup
To ensure a reproducible environment, all necessary dependencies are specified in the environment.yml file. We recommend using Conda (Miniconda or Anaconda) to create and manage the environment named aquaperma.

###  🐍 Using Conda
Follow these steps to create and activate the project environment:

Create the environment from the YAML file:
```bash
conda env create -f environment.yml
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

## Auxiliary Scripts

The `auxiliary/` folder contains helper or test scripts that may be useful for:
- Checking or converting AOI files
- Testing NDWI or other indices
- Debugging or exploring the pipeline

These scripts are **not required** for the main processing workflow.
---

## 📝 Citation
Included in final paper. 

---

## 🙏 Acknowledgements
Built for GACS 7205 coursework. Inspired by the structure of the example repos and uses Rasterio/GeoPandas/OpenCV/scikit-image/QGIS.
