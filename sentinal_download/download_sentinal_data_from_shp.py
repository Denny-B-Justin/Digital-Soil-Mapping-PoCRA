'''
Downlaod a shape (.shp) file to get the boundry details of the location you are looking to download.
Create a Google Cloud account and autherize the Earth Engine before starting the process
'''

import ee, geemap
import geopandas as gpd
from shapely.geometry import mapping, MultiPolygon, Polygon
import pandas as pd
import os
from pyproj import Transformer
import json

ee.Authenticate()
print('authenticated')
ee.Initialize(project='<project code from GCP>')  #Replace with your Google Cloud project
print('all good')
shapefile_path = " location of your .shp file"    #Replace with your shape file location

gdf = gpd.read_file(shapefile_path)
if gdf.crs and gdf.crs.to_string() != 'EPSG:4326':
    gdf = gdf.to_crs('EPSG:4326')
roi_polygon = gdf.geometry.unary_union
print('all good for now')

# if roi_polygon.is_empty:
#     raise ValueError("Geometry is empty. ERROR in shapefile.")

poly_geojson = mapping(roi_polygon)  # geometry to GeoJSON

geojson_string = json.dumps(poly_geojson, indent=2)
# print(geojson_string)
with open('location to save your geoJson file', 'w') as file:
    json.dump(poly_geojson, file, indent=2)

df = pd.DataFrame(poly_geojson['coordinates'])
# print(poly_geojson)
transformer = Transformer.from_crs("epsg:32643", "epsg:4326", always_xy=True)

def reproject_coords(multipolygon):
    new_coords = []
    for polygon in multipolygon:
        new_poly = []
        for ring in polygon:
            new_ring = []
            for coord in ring:
                x, y = coord[:2]  # drop Z
                lon, lat = transformer.transform(x, y)
                new_ring.append([lon, lat])
            new_poly.append(new_ring)
        new_coords.append(new_poly)
    return new_coords


# -----------------------------------------------------------------------------

POLY_INDEX   = 1   
START_DATE   = '2025-05-01'   #Change date according to your usecase          
END_DATE     = '2024-06-01'
OUTPUT_TIF   = "  export location to save your .tif file"

fixed_coords = reproject_coords(poly_geojson["coordinates"])
with open(r'location to save your geoJson file', 'w') as file:
    json.dump(fixed_coords, file, indent=2)

single_poly_coords = [fixed_coords[0]]
with open(r'location to save your geoJson file', 'w') as file:
    json.dump(single_poly_coords, file, indent=2)

if poly_geojson["type"] == "Polygon":
    roi_geom = ee.Geometry.Polygon(fixed_coords)

elif poly_geojson["type"] == "MultiPolygon":
    # Earth Engine wants [[rings]] for a Polygon, so add one level of nesting
    single_poly_coords = [fixed_coords[POLY_INDEX]]
    roi_geom = ee.Geometry.MultiPolygon(single_poly_coords)

else:
    raise ValueError(f"Unsupported geometry type: {poly_geojson['type']}")

s2_collection = (
    ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
      .filterBounds(roi_geom)
      .filterDate(START_DATE, END_DATE)
      .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20))
      .sort("system:time_start", False)
)

latest_image = s2_collection.first()

if latest_image is None or latest_image.getInfo().get('id') is None:
    raise RuntimeError("No Sentinel-2 image found for the given ROI, date range, and cloud filter.")

clipped_image = latest_image.clip(roi_geom).select(["B2", "B3", "B4", "B8"])   #Choose bands according to your usecase

proj_info     = clipped_image.select("B2").projection().getInfo()
crs           = proj_info["crs"]
crs_transform = proj_info["transform"]

geemap.ee_export_image(
    clipped_image,
    filename      = OUTPUT_TIF,
    region        = roi_geom,
    crs           = crs,
    crs_transform = crs_transform,
    file_per_band = False,
)

print("Export submitted to Tasks tab")
