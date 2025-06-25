'''
The sample calibration data is been used to verify the process. The file will have elevation and slope currently.
'''

import geopandas as gpd
import pandas as pd

calib_data = pd.read_csv("% caalibration_data_sample %")   #Path to sample calibration data
calib_data = calib_data.rename(columns={"Y_Latitude": "lat", "X_Longitud": "long"})

old_gt = pd.DataFrame(calib_data, columns=["lat", "long", "Elevation", "Slope"])

gt = gpd.GeoDataFrame(old_gt, geometry=gpd.points_from_xy(old_gt.long, old_gt.lat), crs="EPSG:4326")

proj_crs = gt.estimate_utm_crs()
gt = gt.to_crs(proj_crs).reset_index().rename(columns={"index":"gt_idx"})

dem_tiles = [
    (17,75), (17,76), (18,75), (18,76),
    (18,77), (19,76), (19,77), (19,78), (19,79),
    (20,74), (20,75), (20,76), (20,77), (20,78), (20,79),
    (21,75), (21,76), (21,78), (21,79)
]
pref = r"C:/Users/NDKSP/OneDrive/Desktop/DSM Project/DEM/Shape_Files/"

param_suffixes = {
    "contours":        "contours",
    "elevation_zones": "elevation_zones",
    "slope_zones":     "slope_zones",
    "peaks":           "peaks"
}

results = pd.DataFrame(index=gt["gt_idx"])

for param, suffix in param_suffixes.items():
    gdfs = [ gpd.read_file(f"{pref}{lat}_{lon}_{suffix}.shp")
             for lat, lon in dem_tiles ]
    layer = gpd.GeoDataFrame(pd.concat(gdfs,ignore_index=True),
                              crs=gdfs[0].crs).to_crs(proj_crs)

    if param in ("elevation_zones", "slope_zones"):
        val = [c for c in layer.columns
               if c!="geometry" and pd.api.types.is_numeric_dtype(layer[c])][0]
        ix = gpd.overlay(gt[["gt_idx","geometry"]], layer[["geometry", val]],
                         how="intersection", keep_geom_type=True)
        ix["area"] = ix.geometry.area
        agg = ( ix.assign(w=ix[val]*ix["area"])
                  .groupby("gt_idx")[["w","area"]]
                  .sum()
                  .assign(**{param: lambda df: df["w"]/df["area"]}) )
        results[param] = agg[param]

    elif param=="peaks":
        joined = gpd.sjoin(gt, layer[["geometry"]], how="left", predicate="contains")
        counts = joined.groupby("gt_idx").size()
        results[param] = counts

    elif param=="contours":
        ix = gpd.overlay(gt[["gt_idx","geometry"]], layer[["geometry"]],
                         how="intersection", keep_geom_type=False)
        ix["length"] = ix.geometry.length
        lengths = ix.groupby("gt_idx")["length"].sum()
        results[param] = lengths

gt_final = gt.merge(results, left_on="gt_idx", right_index=True)

common = gt_final.merge(old_gt, on=['lat','long'], how='inner') 
common["Elevation_Diff"] = common["Elevation_x"] - common["Elevation_y"]
common["Slope_Diff"] = common["Slope_x"] - common["Slope_y"]

print(sum(common["Elevation_Diff"]), sum(common["Slope_Diff"])) 

#if the output is 0,0 all the values are same and the extration process is correct.
