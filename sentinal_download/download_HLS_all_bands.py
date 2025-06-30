'''
Create a Google Cloud account and autherize the Earth Engine before starting the process.
'''

import os, io, zipfile, shutil, requests
import ee, geopandas as gpd, rasterio
from shapely.geometry import mapping

# ── CONFIG ────────────────────────────────────────────────────────────────
GEOJSON_PATH = "point_boxes_200m.geojson"
AOI_INDEX    = 0                # which feature to use
BANDS        = ["B2","B3","B4","B5","B6","B7","B8","B11","B12"]
YEARS        = [2020, 2021, 2022, 2023, 2024]
SEASON_RANGE = ("11-01","03-15")         # rabi
OUT_DIR      = "rabi_allbands"
MAKE_STACK   = True                       
os.makedirs(OUT_DIR, exist_ok=True)

HLS_S30 = "NASA/HLS/HLSS30/v002"
HLS_L30 = "NASA/HLS/HLSL30/v002"

# ── EE session ────────────────────────────────────────────────────────────
ee.Authenticate()
ee.Initialize(project="code-in-python-461408")

# ── Helper: tidy geometry ─────────────────────────────────────────────────
def _clean(geom, prec=5):
    def fix(o):
        if isinstance(o,float): return round(o,prec)
        if isinstance(o,(list,tuple)): return [fix(i) for i in o]
        if isinstance(o,dict): return {k:fix(v) for k,v in o.items()}
        return o
    return fix(mapping(geom))

# ── 1) Build “rabi” composite ─────────────────────────────────────────────
gdf       = gpd.read_file(GEOJSON_PATH).to_crs("EPSG:4326")
geom_ee   = ee.Geometry(_clean(gdf.iloc[AOI_INDEX].geometry))

def col(start,end,sat):   # 9-band HLS collection
    return (ee.ImageCollection(sat)
              .filterBounds(geom_ee)
              .filterDate(start,end)
              .select(BANDS))

start_mmdd, end_mmdd = SEASON_RANGE
yearly_means = []
for y in YEARS:
    start = f"{y}-{start_mmdd}"
    end   = f"{y+1}-{end_mmdd}" if start_mmdd > end_mmdd else f"{y}-{end_mmdd}"
    c     = col(start,end,HLS_S30)
    if c.size().getInfo() == 0:
        c = col(start,end,HLS_L30)       # Sentinel gap → Landsat
    yearly_means.append(c.mean().clip(geom_ee))

rabi_img = ee.ImageCollection(yearly_means).mean()

# ── 2) Download all bands (one file each) ─────────────────────────────────
url = rabi_img.getDownloadURL({
    "scale": 30,
    "region": geom_ee,
    "crs": "EPSG:4326",
    "bandIds": BANDS,        # keep order stable
    "fileFormat": "GeoTIFF",
    "filePerBand": True      # ← crucial!
})

print("Fetching ZIP from Earth Engine…")
resp = requests.get(url, stream=True)
resp.raise_for_status()

band_paths = []
with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
    for member in z.namelist():
        if member.lower().endswith(".tif"):
            band_name = member.split("_")[-1].replace(".tif","")  # e.g. “B2”
            out_path  = os.path.join(OUT_DIR, f"rabi_{band_name}.tif")
            with z.open(member) as src, open(out_path,"wb") as dst:
                shutil.copyfileobj(src, dst, 65536)
            band_paths.append(out_path)
            print(f"• extracted {band_name}")

# ── 3) Build a 9-band stack ───────────────────────────────────
if MAKE_STACK:
    stack_path = os.path.join(OUT_DIR, "rabi_stack.tif")
    with rasterio.open(band_paths[0]) as ref:
        profile = ref.profile
    profile.update(count=len(band_paths), compress="lzw")
    with rasterio.open(stack_path, "w", **profile) as dst:
        for idx, path in enumerate(band_paths, start=1):
            with rasterio.open(path) as src:
                dst.write(src.read(1), idx)
                dst.set_band_description(idx, os.path.basename(path))
    print(f"9-band COG written → {stack_path}")

print("Done.")

# ── 4) Check the stack ────────────────────────────────────────────────
with rasterio.open(stack_path) as src:
    print(f"CRS: {src.crs}")
    print(f"Number of bands: {src.count}")
    print(f"Width x Height: {src.width} x {src.height}")
    
    all_bands = src.read()
    print(f"Shape of array (bands, height, width): {all_bands.shape}")

    for i in range(all_bands.shape[0]):
        band_data = all_bands[i]
        print(f"Band {i+1} → min: {band_data.min()}, max: {band_data.max()}, mean: {band_data.mean():.2f}")
