'''

Go to Worldclim website: https://www.worldclim.org/data/monthlywth.html
Download all the required zip files that contain TIF files and place them in one folder.

'''


# -------------------------- CONFIG ----------------------------------
CSV_POINTS   = "your file with lat, long"    # your file with lat, long
RASTER_ROOT  = "WorldClim_files"               # folder that holds the .tif files
OUT_CSV      = "points_with_climate.csv"

DURATIONS    = ["10m"]               # spatial resolutions - ["2.5m", "5m", "10m"]
YEARS        = [2020, 2021, 2022, 2023, 2024]
MONTHS       = range(1, 13)                        # 1 … 12
VARIABLES    = ["tmin", "tmax", "prec"]                    # or ["tmax"] / ["tmin"]

# --------------------------------------------------------------------
import os, glob, rasterio
import pandas as pd
import numpy as np
from tqdm import tqdm

# 1) read the point layer ------------------------------------------------
pts_df = pd.read_csv(CSV_POINTS)
assert {"lat","long"}.issubset(pts_df.columns), "`lat`/`long` cols missing"

# 2) prepare an empty frame to accumulate results ------------------------
result = pts_df.copy()

# 3) helper: fetch 1 raster, sample all points ---------------------------
def sample_raster(raster_path, lons, lats):
    """Returns a 1-D np.array with a value per point; np.nan if outside / nodata."""
    with rasterio.open(raster_path) as src:
        coords = list(zip(lons, lats))
        vals   = np.fromiter((v[0] for v in src.sample(coords)), dtype=float, count=len(coords))
        nodata = src.nodata
        if nodata is not None:
            vals[vals == nodata] = np.nan
    return vals

# 4) main loop -----------------------------------------------------------
lons, lats = result["long"].values, result["lat"].values

for var in VARIABLES:
    for year in YEARS:
        for month in MONTHS:
            mm = f"{month:02d}"
            for dur in DURATIONS:
                tif_name = f"wc2.1_cruts4.09_{dur}_{var}_{year}-{mm}.tif"
                tif_path = os.path.join(RASTER_ROOT, tif_name)
                if not os.path.exists(tif_path):
                    raise FileNotFoundError(f"Missing raster: {tif_path}")

                col = f"{var}_{year}_{mm}_{dur}"
                result[col] = sample_raster(tif_path, lons, lats)

                # (optional) progress bar:
                tqdm.write(f"✓ extracted {col}")

# 5) write to disk -------------------------------------------------------
result.to_csv(OUT_CSV, index=False)
print(f"Saved → {OUT_CSV}  |  shape = {result.shape}")
