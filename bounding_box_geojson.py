'''
We have the ground truth data of 2000 locations. Since we cannot use locations directly, we will create a bounding box near each loaction with 30m resolution (half_size = 15m)
After that we need to map our DEM data with this ground truth data to get the training dataset. 
This is then verified by verify_dem_mapping.ipynb
'''

import numpy as np
import pandas as pd
import pandas as pd
import geopandas as gpd
from shapely.geometry import box, Point

data = pd.read_csv("nbss_all_villages_new.csv")
dataf = pd.DataFrame(data)
print(dataf.head())
df = dataf[["lat", "long"]]

df = df.drop_duplicates(subset=['lat', 'long']).reset_index(drop=True)

gdf = gpd.GeoDataFrame(
    df,
    geometry=gpd.points_from_xy(df['long'], df['lat']),
    crs="EPSG:4326"
)

gdf_proj = gdf.to_crs(epsg=3857)   # Project to metric CRS (Web Mercator) for buffering in meters
half_side = 15

gdf_proj['geometry'] = gdf_proj.geometry.apply(
    lambda point: box(point.x - half_side, point.y - half_side, point.x + half_side, point.y + half_side)
)

gdf_boxes = gdf_proj.to_crs(epsg=4326)     # Reproject back to WGS84

output_path = "point_boxes.geojson"     #Choose your ouput location
gdf_boxes.to_file(output_path, driver='GeoJSON')
