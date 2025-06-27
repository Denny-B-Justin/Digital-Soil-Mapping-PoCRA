'''
  Extracting data from DEM
  Collect the SRTM 30m resolution data from https://dwtkns.com/srtm30m/
  Use the below code to extract "contours", "elevation_zones", "slope_zones", and "peaks" values from the DEM
  The coordinates tou extract can be used to make the matrix "dem_locations". This will help us loop through and extract all required features.
''' 
import numpy as np
import pandas as pd
import rasterio
from rasterio.transform import from_origin
from rasterio.features import shapes
import geopandas as gpd
from shapely.geometry import LineString, Polygon, Point
from skimage import measure
from scipy.ndimage import gaussian_filter
import os



def read_hgt(file_path):
    """Reads a .hgt file and returns the DEM array and rasterio transform"""
    size = os.path.getsize(file_path)
    if size == 3601 * 3601 * 2:
        resolution = 3601  # SRTM1
    elif size == 1201 * 1201 * 2:
        resolution = 1201  # SRTM3
    else:
        raise ValueError("Unknown HGT file resolution")

    data = np.fromfile(file_path, np.dtype('>i2')).reshape((resolution, resolution))
    data = np.where(data == -32768, np.nan, data)

    filename = os.path.basename(file_path)
    lat = int(filename[1:3])
    lon = int(filename[4:7])
    if filename[0] == 'S': lat = -lat
    if filename[3] == 'W': lon = -lon

    # Define affine transform (top-left origin)
    pixel_size = 1 / (resolution - 1)
    transform = from_origin(lon, lat + 1, pixel_size, pixel_size)

    return data, transform, 'EPSG:4326'

def extract_features_from_hgt(hgt_file, output_prefix="hingoli_features"):
    dem, transform, crs = read_hgt(hgt_file)
    results = {}

    # 1. Contours
    contours = []
    for level in range(int(np.nanmin(dem)), int(np.nanmax(dem)), 100):
        for contour in measure.find_contours(dem, level):
            coords = [rasterio.transform.xy(transform, r, c) for r, c in contour]
            contours.append({"geometry": LineString(coords), "elevation": level})
    results['contours'] = gpd.GeoDataFrame(contours, crs=crs)

    # 2. Elevation Zones
    zones = np.digitize(dem, bins=[0, 200, 400, 600, 800, 1000])
    polygons = []
    for shp, val in shapes(zones.astype(np.int16), mask=~np.isnan(dem), transform=transform):
        polygons.append({"geometry": Polygon(shp["coordinates"][0]), "zone": val})
    results['elevation_zones'] = gpd.GeoDataFrame(polygons, crs=crs)

    # 3. Slope Zones
    dem_smooth = gaussian_filter(dem, sigma=1)
    gy, gx = np.gradient(dem_smooth)
    slope = np.sqrt(gx**2 + gy**2)
    slope_zones = np.digitize(slope, bins=[0, 10, 20, 30])
    slopes = []
    for shp, val in shapes(slope_zones.astype(np.int16), mask=~np.isnan(dem), transform=transform):
        slopes.append({"geometry": Polygon(shp["coordinates"][0]), "slope_class": val})
    results['slope_zones'] = gpd.GeoDataFrame(slopes, crs=crs)

    # 4. Peaks (top 10 highest points)
    flat_idx = np.argsort(dem.ravel())[::-1][:10]
    peak_coords = np.unravel_index(flat_idx, dem.shape)
    peaks = []
    for r, c in zip(*peak_coords):
        lon, lat = rasterio.transform.xy(transform, r, c)
        peaks.append({"geometry": Point(lon, lat), "elevation": dem[r, c]})
    results['peaks'] = gpd.GeoDataFrame(peaks, crs=crs)

    for layer, gdf in results.items():
        out_file = f"C:/Users/NDKSP/OneDrive/Desktop/DSM Project/DEM/Shape_Files/{output_prefix}_{layer}.shp"
        if not os.path.exists(out_file):
            gdf.to_file(out_file)
            # print(f"Saved: {out_file}")
        # else:
            # print(f"Skipped (already exists): {out_file}")

# Example usage
dem_locations = [[17,75], [17,76], [18,75], [18,76],[18,77], [19,76], [19,77], [19,78], [19, 79], [20,74], [20,75], [20,76], [20,77], [20,78], [20,79], [21,75], [21,76], [21,78], [21,79]]

for cord in dem_locations:  
    lat, long = str(cord[0]), str(cord[1])  
    extract_features_from_hgt(f"N{lat}E0{long}.hgt", output_prefix= f"{lat}_{long}")
