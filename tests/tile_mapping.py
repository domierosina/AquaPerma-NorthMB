# AquaPerma-NorthMB 
# Sentinel & Landsat Tile AOI Matching Script
# Robust version using lxml for KML parsing
# ==================================
# Author: Domenica B.

# ------------------------------
# Imports
# ------------------------------
import os
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from lxml import etree
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union

# --------------------------
# AOI Loader
# --------------------------
def load_kml_aoi_lxml(kml_file_path):
    """
    Extract geometries from a KML file using lxml. Supports Point and Polygon.
    Returns a list of Shapely geometry objects.
    """
    ns = {
        'kml': 'http://www.opengis.net/kml/2.2',
        'gx': 'http://www.google.com/kml/ext/2.2'
    }

    if not os.path.exists(kml_file_path):
        raise FileNotFoundError(f"KML file not found: {kml_file_path}")

    tree = etree.parse(kml_file_path)
    root = tree.getroot()

    geometries = []

    # Extract Points
    for coord in root.xpath('.//kml:Point/kml:coordinates', namespaces=ns):
        lon, lat, *_ = map(float, coord.text.strip().split(','))
        geometries.append(Point(lon, lat))

    # Extract Polygons
    for coords in root.xpath('.//kml:Polygon//kml:coordinates', namespaces=ns):
        pts = [tuple(map(float, c.split(',')))[:2] for c in coords.text.strip().split()]
        geometries.append(Polygon(pts))

    if not geometries:
        raise ValueError(f"No geometries found in {kml_file_path}. Check KML structure.")

    return geometries

# --------------------------
# Tile Matching Functions
# --------------------------
def match_aoi_to_tiles(aoi_geometries, tile_grid_path, id_column='Name'):
    """
    Generic function to match AOI geometries to a tile grid.
    Returns GeoDataFrame of matching tiles.
    """
    if not os.path.exists(tile_grid_path):
        raise FileNotFoundError(f"Tile grid file not found: {tile_grid_path}")

    tiles_gdf = gpd.read_file(tile_grid_path)
    matches = gpd.GeoDataFrame(columns=tiles_gdf.columns, crs=tiles_gdf.crs)

    for geom in aoi_geometries:
        intersecting = tiles_gdf[tiles_gdf.geometry.intersects(geom)]
        matches = gpd.GeoDataFrame(pd.concat([matches, intersecting], ignore_index=True))

    matches = matches.drop_duplicates(subset=id_column) if id_column in matches.columns else matches.drop_duplicates()
    return matches

# --------------------------
# Visualization
# --------------------------
def plot_aoi_with_tiles(aoi_geometries, sentinel_gdf=None, landsat_gdf=None):
    """
    Plot AOI and optionally Sentinel & Landsat tiles.
    """
    fig, ax = plt.subplots(figsize=(10, 10))

    if sentinel_gdf is not None:
        sentinel_gdf.boundary.plot(ax=ax, color='blue', linewidth=1, label='Sentinel-2 Tiles')

    if landsat_gdf is not None:
        landsat_gdf.boundary.plot(ax=ax, color='green', linewidth=1, label='Landsat Tiles')

    for geom in aoi_geometries:
        gpd.GeoSeries([geom]).boundary.plot(ax=ax, color='red', linewidth=2, label='AOI')

    ax.set_title("AOI with Sentinel-2 and Landsat Tiles")
    plt.legend()
    plt.show()

# --------------------------
# Main Script
# --------------------------
if __name__ == "__main__":
    # File paths
    kml_path = "data/aoi/2025_aoi.kml"
    sentinel_grid_path = "data/aoi/sentinel2_tiling_grid_wgs84.geojson"
    landsat_grid_path = "data/aoi/landsat_wrs2_grid.geojson"

    # Load AOI
    print(f"Loading AOI from {kml_path}...")
    aoi_geometries = load_kml_aoi_lxml(kml_path)
    print(f"Loaded {len(aoi_geometries)} geometries")

    # Match Sentinel-2 tiles
    sentinel_matches = match_aoi_to_tiles(aoi_geometries, sentinel_grid_path, id_column='Name')
    sentinel_tile_ids = sentinel_matches['Name'].tolist()
    print("Sentinel-2 tiles:", sentinel_tile_ids)

    # Match Landsat tiles
    landsat_matches = match_aoi_to_tiles(aoi_geometries, landsat_grid_path, id_column='PATH')
    landsat_tile_ids = landsat_matches.apply(lambda row: f"{row['PATH']}-{row['ROW']}", axis=1).tolist()
    print("Landsat tiles (Path-Row):", landsat_tile_ids)

    # Plot AOI with tiles
    plot_aoi_with_tiles(aoi_geometries, sentinel_gdf=sentinel_matches, landsat_gdf=landsat_matches)
