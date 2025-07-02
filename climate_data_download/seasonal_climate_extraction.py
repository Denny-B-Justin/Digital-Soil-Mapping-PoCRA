'''
Go to Worldclim website: https://www.worldclim.org/data/monthlywth.html
Download all the required zip files that contain TIF files and place them in one folder.
-> Kharif   Jun-Sep
-> Rabi     Oct-Mar (cross-year)
-> Zaid     Mar-Jun
'''

# -------------------------- CONFIG ----------------------------------
CSV_POINTS   = "your file with lat, long"     #   lat / long table
RASTER_ROOT  = "WorldClim_tifs"                 #   folder with .tif files
OUT_CSV      = "points_seasonal_climate.csv"

SELECT_DURATION = "10m"                       # pick ONE: 2.5m | 5m | 10m
VARIABLES       = ["tmin", "tmax", "prec"]     # change to ["tmax"] etc. if needed
YEARS           = [2020, 2021, 2022, 2023, 2024]

# seasonal month lists (1-based)
SEASONS = {
    "kh": [6, 7, 8, 9],                # Kharif   Jun-Sep
    "rb": [10, 11, 12, 1, 2, 3],       # Rabi     Oct-Mar (cross-year)
    "zd": [3, 4, 5, 6],                # Zaid     Mar-Jun
}
# --------------------------------------------------------------------

import os, rasterio
import pandas as pd
import numpy as np
from collections import defaultdict
from tqdm import tqdm

# 1) read points ----------------------------------------------------------
pts = pd.read_csv(CSV_POINTS)
assert {"lat", "long"}.issubset(pts.columns), "CSV must contain 'lat' and 'long'."
lons, lats = pts["long"].values, pts["lat"].values
n_pts      = len(pts)

# 2) prepare accumulators -------------------------------------------------
# dict[var][season] -> {'sum': ndarray, 'cnt': int}
acc = {v: {s: {"sum": np.zeros(n_pts, float), "cnt": 0}
           for s in SEASONS}
       for v in VARIABLES}

# 3) helper: sample one raster -------------------------------------------
def sample_tif(path, xy):
    with rasterio.open(path) as src:
        values = np.array([v[0] for v in src.sample(xy)], dtype=float)
        if src.nodata is not None:
            values[values == src.nodata] = np.nan
    return values

coords = list(zip(lons, lats))

# 4) main loop ------------------------------------------------------------
for var in VARIABLES:
    for year in YEARS:
        for month in range(1, 13):
            mm = f"{month:02d}"
            tif_name = f"wc2.1_cruts4.09_{SELECT_DURATION}_{var}_{year}-{mm}.tif"
            tif_path = os.path.join(
                RASTER_ROOT, tif_name
            )
            if not os.path.exists(tif_path):
                raise FileNotFoundError(tif_path)

            data = sample_tif(tif_path, coords)

            for season, months in SEASONS.items():
                if month in months:
                    acc[var][season]["sum"] += data
                    acc[var][season]["cnt"] += 1

            tqdm.write(f"• {var.upper()} {year}-{mm} done")

# 5) assemble final dataframe --------------------------------------------
out = pts.copy()

for var in VARIABLES:
    for season in SEASONS:
        s = acc[var][season]
        col = f"{var}_{season}"
        out[col] = s["sum"] / s["cnt"]         

out.to_csv(OUT_CSV, index=False)
print(f"Saved → {OUT_CSV} | shape = {out.shape}")
