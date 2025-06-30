# ---------------------------------------------------------------
#  Loop over polygon_* TIFs, join to their ground-truth boxes
#  Python 3.13.3 – needs rasterio, geopandas, pandas, numpy]
#  There should be a directory with TIFs and JSON in the naming format - polygon_0.tiff , polygon_0_bands.json respectively. 
# ---------------------------------------------------------------
import json, re, pathlib
import numpy as np, pandas as pd, geopandas as gpd, rasterio
from rasterio.mask import mask
from shapely.geometry import box

# ── CONFIG ──────────────────────────────────────────────────────
DATA_DIR  = pathlib.Path("% TIF File Directory%")    #insert the directory location here
BOXES_GJ  = "point_boxes.geojson"
BAND_STAT = np.mean

# ── LOAD ALL GT BOXES (in WGS-84) ───────────────────────────────
boxes_gdf = gpd.read_file(BOXES_GJ).to_crs("EPSG:4326")

rows = []                         

# ── LOOP OVER EACH polygon_*.tif ────────────────────────────────
tif_files = sorted(DATA_DIR.glob("polygon_*.tif"))
pattern   = re.compile(r"polygon_(\d+)\.tif$")

for tif in tif_files:
    m = pattern.search(tif.name)
    if not m:
        print(f"⚠ Skip {tif} (filename doesn’t match ‘polygon_#.tif’).")
        continue
    idx = int(m.group(1))
    if idx >= len(boxes_gdf):
        print(f"⚠ No GT box #{idx} – skipping {tif}.")
        continue
    gt_box   = boxes_gdf.iloc[idx]
    poly_geom = [gt_box.geometry]

    # ── locate the JSON with band names ─────────────────────────
    # accepted: polygon_0.json  OR  polygon_0_bands.json
    json_candidates = [tif.with_suffix(".json"),
                       tif.with_name(tif.stem + "_bands.json")]
    json_path = next((p for p in json_candidates if p.exists()), None)
    if json_path is None:
        print(f"⚠ No band-name JSON for {tif.name} – skipping.")
        continue
    band_names = json.load(json_path.open())

    # ── crop / mask the raster to the GT box ────────────────────
    with rasterio.open(tif) as src:
        img, _ = mask(src, poly_geom, crop=True)
        assert img.shape[0] == len(band_names), \
               f"Band count mismatch in {tif.name}"

    # ── summarise each band (mean here) ─────────────────────────
    band_vals = BAND_STAT(img.reshape(img.shape[0], -1), axis=1)

    # ── assemble row dict ───────────────────────────────────────
    row = {
        "lat"     : gt_box.geometry.centroid.y,
        "long"    : gt_box.geometry.centroid.x,
        "geometry": gt_box.geometry,
        "source"  : tif.name               # keep provenance
    }
    row.update({name: float(val)           # JSON band → value
                for name, val in zip(band_names, band_vals)})
    rows.append(row)


# ── BUILD FINAL GEO-DATAFRAME ───────────────────────────────────
result_gdf = gpd.GeoDataFrame(rows, geometry="geometry", crs="EPSG:4326")
result_gdf.head()                  
# result_gdf.to_file("gt_with_bands_all.geojson", driver="GeoJSON")
