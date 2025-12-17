
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
│   ├── aoi/                                           # Area of interest files
│   ├── raw/
│       │   ├── sentinel2/
│       │   └── landsat8/   
│   └── results/
│       │   ├── sentinel2/
│       │   ├── landsat8/
│       │   └── report/
├── docs/
│   ├── Proposal.pdf
│   ├── FinalPaper.pdf
│   └── visuals/                  
├── notebooks/
│   ├── 00_AOI_Map_Print.ipynb
│   ├── 00_download_and_QA_larger_AOI.ipynb
│   ├── 01_sanity_check_backends_options.ipynb
│   ├── 02_scene_selection_and_data_download.ipynb
│   └── 03_surface_water_change_analysis.ipynb          
└── auxiliary/                                         # Scripts made to speed up development. OPTIONAL
    ├── pipelines/
    ├── WRS2_descending_0/
    ├── kml_to_geojson.py
    ├── test_ndwi.py
    ├── check_kml.py
    ├── ndvi_maps_and_delta.py
    └── tile_mapping.py  
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
###  🔑 Data Access (VITO openEO)
This project utilizes the VITO openEO backend (openeo.vito.be) to access Sentinel-2 and Landsat imagery without manually downloading raw scenes.
1. Create a VITO openEO Account
2. Go to the VITO openEO portal: 👉 https://portal.openeo.vito.be
3. Click Sign up and create a free account using: GitHub OR institutional email
4. Once logged in, your account is automatically enabled for: Sentinel-2 (L1C / L2A), Landsat 8–9, Batch processing via openEO

*No API key is required. Authentication uses OAuth via your browser.*

--- 

## 🔧 Requirements
Key Python packages (from environment.yml):
- numpy
- pandas
- rasterio
- geopandas
- matplotlib
- folium
- openeo (for scene downloads)
- tqdm

---

## ▶️ Usage
1️⃣ Scene Selection & Download (openEO)
Notebook: `02_scene_selection_and_data_download.ipynb`

This notebook:
- Connects to the VITO openEO backend
- Loads Sentinel-2 and Landsat collections
- Filters by AOI, date range, and cloud cover
- Computes NDWI
- Exports NDWI and binary water mask GeoTIFFs

Inputs
- AOI file (.geojson or .kml)
- Date ranges (summer months)
- Sensor selection

Outputs
- NDWI GeoTIFFs
- Water mask GeoTIFFs
- Saved under data/results/<sensor>/

Run with:
`jupyter notebook notebooks/02_scene_selection_and_data_download.ipynb`

2️⃣ NDWI Change Detection & Analysis

Notebook: `03_surface_water_change_analysis.ipynb`

This notebook performs all temporal analysis using the downloaded NDWI rasters.

Generated outputs (8 total):
- Year-to-year ΔNDWI maps
- Year-to-year water gain/loss overlays
- Multi-year water persistence maps
- Earliest → latest ΔNDWI maps
- Earliest → latest per-pixel % NDWI change maps
- Quantitative CSV summary
- Sensor-specific multi-panel summary figures
- Per-pixel % NDWI change for consecutive years

Run with:
`jupyter notebook notebooks/03_surface_water_change_analysis.ipynb`

Notes for Reproducibility
- All processing is done server-side via openEO until final GeoTIFF export
- No raw satellite scenes are downloaded
- The workflow is reproducible with only: AOI file, openEO account, Defined date ranges

---

## Auxiliary Scripts

The `auxiliary/` folder contains helper or test scripts that may be useful for:
- Checking or converting AOI files
- Testing NDWI or other indices
- Debugging or exploring the pipeline

These scripts are **not required** for the main processing workflow.
---

## 📝 Data Sources and Citations
Full citations in final paper. This project uses publicly available Earth observation data accessed via the VITO openEO platform.

**Satellite Data**
_Sentinel-2_
European Space Agency (ESA).
Sentinel-2 MSI Level-1C and Level-2A products.
Accessed via the openEO VITO backend.

_Landsat 8–9_
U.S. Geological Survey (USGS) & National Aeronautics and Space Administration (NASA).
Landsat Collection 2 Level-2 products.
Accessed via the openEO VITO backend.

****NDWI Reference****
McFeeters, S. K. (1996).
The use of the Normalized Difference Water Index (NDWI) in the delineation of open water features.
International Journal of Remote Sensing, 17(7), 1425–1432.
https://doi.org/10.1080/01431169608948714

**Platform Citations**
_openEO Platform_
openEO Consortium.
https://openeo.org

_VITO openEO Backend_
Flemish Institute for Technological Research (VITO).
https://openeo.vito.be

---

## 🙏 Acknowledgements
Built for GACS 7205 coursework. Inspired by the structure of the example repos and uses Rasterio/GeoPandas/OpenCV/scikit-image/QGIS.
