import geopandas as gpd

# Path to the folder where you unzipped the WRS2 files
shapefile_path = "7205/WRS2_descending_0/WRS2_descending.shp"

# Load the shapefile
gdf = gpd.read_file(shapefile_path)

# Optional: check the first few rows
print(gdf.head())

# Export to GeoJSON
geojson_path = "wrs2_grid.geojson"
gdf.to_file(geojson_path, driver="GeoJSON")

print(f"GeoJSON saved to {geojson_path}")
