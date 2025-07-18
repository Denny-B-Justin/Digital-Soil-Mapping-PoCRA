# ── Imports ────────────────────────────────────────────────────────────────
import os, io, zipfile, shutil, requests, json
import ee, geopandas as gpd
from shapely.geometry import mapping


# Initialize Earth Engine
ee.Authenticate()
ee.Initialize()

# ── CONFIG ────────────────────────────────────────────────────────────────
GEOJSON_PATH = "point_boxes.geojson"
BANDS        = ["B2","B3","B4","B5","B6","B7","B8","B11","B12"]
YEARS        = [2020, 2021, 2022, 2023, 2024]
OUT_DIR      = "seasonal_stack"
os.makedirs(OUT_DIR, exist_ok=True)

SEASONS = {
    "rabi": ("11-01","03-15"),
    "kharif": ("06-15","10-15"),
    "zaid": ("03-16","06-14")
}

HLS_S30 = "NASA/HLS/HLSS30/v002"
HLS_L30 = "NASA/HLS/HLSL30/v002"

# ── Helper: tidy geometry ─────────────────────────────────────────────────
def _clean(geom, prec=5):
    def fix(o):
        if isinstance(o,float): return round(o,prec)
        if isinstance(o,(list,tuple)): return [fix(i) for i in o]
        if isinstance(o,dict): return {k:fix(v) for k,v in o.items()}
        return o
    return fix(mapping(geom))

# ── ◆◆◆ ADD SPECTRAL INDICES FUNCTIONS ◆◆◆ ──────────────────────────────
# These utilities leave the **original 9‑band extraction untouched**.
# Indices are computed **after** the seasonal composite is ready but **before**
# renaming, so downstream logic stays the same.
# -------------------------------------------------------------------------

def add_indices(img: ee.Image) -> ee.Image:
    """Append NDVI, GNDVI, SAVI, TVI, EVI and BI to *img* and return it."""
    red   = img.select("B4")   # Red
    green = img.select("B3")   # Green
    blue  = img.select("B2")   # Blue
    nir   = img.select("B8")   # Near‑Infrared
    swir  = img.select("B11")  # Short‑Wave Infrared

    ndvi  = nir.subtract(red).divide(nir.add(red)).rename("NDVI")
    gndvi = nir.subtract(green).divide(nir.add(green)).rename("GNDVI")
    savi  = nir.subtract(red).multiply(1.5).divide(nir.add(red).add(0.5)).rename("SAVI")
    tvi   = nir.subtract(red).multiply(120).subtract(green.subtract(red).multiply(200)).multiply(0.5).rename("TVI")
    evi   = nir.subtract(red).multiply(2.5).divide(nir.add(red.multiply(6)).subtract(blue.multiply(7.5)).add(1)).rename("EVI")
    bi    = swir.subtract(nir).divide(swir.add(nir)).rename("BI")

    # return image with six extra bands appended at the end
    return img.addBands([ndvi, gndvi, savi, tvi, evi, bi])

# ── Load AOIs ─────────────────────────────────────────────────────────────
gdf = gpd.read_file(GEOJSON_PATH).to_crs("EPSG:4326")

for idx, row in gdf.iterrows():
    idx=371
    geom_ee = ee.Geometry(_clean(row.geometry))
    polygon_id = row.get("id", f"polygon_{idx}")

    def col(start,end,sat):
        return (ee.ImageCollection(sat)
                  .filterBounds(geom_ee)
                  .filterDate(start,end)
                  .select(BANDS))

    season_images = []
    for season, (start_mmdd, end_mmdd) in SEASONS.items():
        yearly_means = []
        for y in YEARS:
            start = f"{y}-{start_mmdd}"
            end   = f"{y+1}-{end_mmdd}" if start_mmdd > end_mmdd else f"{y}-{end_mmdd}"
            c     = col(start,end,HLS_S30)
            if c.size().getInfo() == 0:
                c = col(start,end,HLS_L30)
            yearly_means.append(c.mean().clip(geom_ee))
        season_img = ee.ImageCollection(yearly_means).mean()
        # ── ▶▶ INSERTING SPECTRAL INDICES ◀◀ ──────────────────────────────
        season_img = add_indices(season_img)
        # ── ▲▲ INDICES ADDED (stay above this line) ▲▲ ──────────────────

        # Dynamically fetch band order to avoid rename‑length mismatches
        orig_names = season_img.bandNames().getInfo()  # Python list
        renamed_bands = [f"{bn}_{season}" for bn in orig_names]

        # Rename and store
        season_img = season_img.rename(renamed_bands)
        season_images.append(season_img)
        band_names_master.extend(renamed_bands)
        
    final_img = ee.Image.cat(season_images)

    # Set band names and save as JSON
    band_names = [f"{b}_{season}" for season in SEASONS for b in BANDS]
    json_path = os.path.join(OUT_DIR, f"{polygon_id}_bands.json")
    with open(json_path, "w") as jf:
        json.dump(band_names, jf)

    url = final_img.getDownloadURL({
        "scale": 30,
        "region": geom_ee,
        "crs": "EPSG:4326",
        "bandIds": band_names,
        "filePerBand": False
    })

    print(f"Downloading ZIP for polygon {polygon_id}…")
    resp = requests.get(url, stream=True)
    resp.raise_for_status()

    zip_path = os.path.join(OUT_DIR, f"{polygon_id}.zip")
    with open(zip_path, "wb") as f:
        shutil.copyfileobj(resp.raw, f)

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        members = [m for m in zip_ref.namelist() if m.lower().endswith(".tif")]
        if not members:
            raise ValueError("No .tif file found in downloaded ZIP.")
        member = members[0]
        out_tif = os.path.join(OUT_DIR, f"{polygon_id}.tif")
        with zip_ref.open(member) as zf, open(out_tif, "wb") as out:
            shutil.copyfileobj(zf, out)
        print(f"✔ Saved: {out_tif}")

    os.remove(zip_path)

print("All polygons processed.")
