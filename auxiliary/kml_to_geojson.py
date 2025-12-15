import os
from osgeo import ogr

KML_PATH = "/Users/domenica/Desktop/AquaPerma-NorthMB/data/aoi/2025_aoi.kml"
GEOJSON_PATH = "/Users/domenica/Desktop/AquaPerma-NorthMB/data/aoi/2025_aoi.geojson"

# Open the KML
driver = ogr.GetDriverByName('KML')
ds = driver.Open(KML_PATH, 0)  # 0 = read-only
if ds is None:
    raise ValueError("Cannot open KML file.")

# Create GeoJSON driver
geojson_driver = ogr.GetDriverByName('GeoJSON')

# Delete existing GeoJSON if exists
if os.path.exists(GEOJSON_PATH):
    geojson_driver.DeleteDataSource(GEOJSON_PATH)

# Convert
geojson_driver.CopyDataSource(ds, GEOJSON_PATH)
print(f"Converted KML to GeoJSON: {GEOJSON_PATH}")
