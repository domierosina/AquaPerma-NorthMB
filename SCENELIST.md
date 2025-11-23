# Scene List for Keeyask/Gillam (2016–2021)

This document lists all Landsat 8 and Sentinel-2 scenes required for the AquaPerma-NorthMB project, covering the Keeyask/Gillam region for the 2016–2021 period.

---

## Landsat 8 Collection 2 Level-2 (Surface Reflectance)

**Path: 34   Row: 20**

Download each Scene ID from **USGS EarthExplorer**.

### 2016

* LC08_L2SP_034020_20160711_20200905_02_T1

### 2017

* LC08_L2SP_034020_20170730_20200902_02_T1

### 2018

* LC08_L2SP_034020_20180816_20200822_02_T1

### 2019

* LC08_L2SP_034020_20190719_20200820_02_T1

### 2020

* LC08_L2SP_034020_20200705_20200912_02_T1

### 2021

* LC08_L2SP_034020_20210724_20220128_02_T1

### Required Landsat Bands

* B3 (Green)
* B5 (NIR)
* QA_PIXEL
* (Optional) DSWE

Place downloaded files under:

```
data/raw/landsat/<sceneID>/
```

---

## Sentinel-2 Level-2A (Tile 15XVS)

Download each Scene ID from **Copernicus SciHub** or AWS Sentinel-2.

### 2016

* S2A_MSIL2A_20160720T165911_N0204_R112_T15XVS

### 2017

* S2A_MSIL2A_20170809T165921_N0205_R112_T15XVS

### 2018

* S2A_MSIL2A_20180818T165921_N0208_R112_T15XVS

### 2019

* S2B_MSIL2A_20190722T165919_N0213_R112_T15XVS

### 2020

* S2A_MSIL2A_20200802T165901_N0214_R112_T15XVS

### 2021

* S2B_MSIL2A_20210725T165919_N0301_R112_T15XVS

### Required Sentinel-2 Bands

* B03 (Green)
* B08 (NIR)

Place downloaded files under:

```
data/raw/sentinel/<sceneID>/
```

---

## Next Step

Run:

```bash
python src/download_data.py
```

This will clip all scenes into:

```
data/processed/clipped/landsat/
data/processed/clipped/sentinel/
```

---
