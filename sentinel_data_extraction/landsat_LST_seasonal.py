# ── Imports ────────────────────────────────────────────────────────────────
import re
import pathlib

import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.mask import mask

# ── CONFIG ────────────────────────────────────────────────────────────────
DATA_DIR   = pathlib.Path("TIF_LST")              # folder with polygon_*.tif
BOXES_GJ   = "gt_point_boxes.geojson"                    # your GT boxes
BAND_NAMES = ["LST_rabi", "LST_kharif", "LST_zaid"]       # expected band order
BAND_STAT  = np.mean                                     # statistic to apply

# ── LOAD ALL GT BOXES (in WGS-84) ─────────────────────────────────────────
boxes_gdf = gpd.read_file(BOXES_GJ).to_crs("EPSG:4326")

# ── Prepare storage for results ────────────────────────────────────────────
rows = []
F2C = lambda f: (f - 32.0) * (5.0/9.0)
# ── Loop over each polygon_*.tif ───────────────────────────────────────────
pattern = re.compile(r"polygon_(\d+)\.tif$")
for tif_path in sorted(DATA_DIR.glob("polygon_*.tif")):
    m = pattern.search(tif_path.name)
    if not m:
        print(f"⚠ Skipping {tif_path.name}: filename doesn’t match ‘polygon_#.tif’")
        continue

    idx = int(m.group(1))
    if idx >= len(boxes_gdf):
        print(f"⚠ No GT box #{idx} – skipping {tif_path.name}")
        continue

    # Get the ground-truth polygon for this index
    gt_row   = boxes_gdf.iloc[idx]
    geom     = [gt_row.geometry]

    # Read & mask the raster
    with rasterio.open(tif_path) as src:
        print(f"Processing {tif_path.name} …")
        # mask() returns an array of shape (bands, rows, cols)
        img, _ = mask(src, geom, crop=True)
        if img.shape[0] != len(BAND_NAMES):
            raise ValueError(
                f"Expected {len(BAND_NAMES)} bands, got {img.shape[0]} in {tif_path.name}"
            )

    # Compute per-band statistic
    # reshape → (bands, n_pixels)
    vals_f = BAND_STAT(img.reshape(img.shape[0], -1), axis=1)
    # vals = BAND_STAT(img.reshape(img.shape[0], -1), axis=1)
    vals_c = F2C(vals_f)
    # Assemble result row
    row = {
        "polygon_id": idx,
        "lat":        float(gt_row["lat"]),
        "lon":        float(gt_row["long"]),
        "source":     tif_path.name
    }
    # attach each season’s mean
    for name, v in zip(BAND_NAMES, vals_f):
        row[name] = float(v)

    rows.append(row)

# ── Build DataFrame & save ─────────────────────────────────────────────────
df = pd.DataFrame(rows)

print("Result preview:")
# print(df.head())

# to CSV
out_csv = "lst_seasonal_summary.csv"
df.to_csv(out_csv, index=False)
df
