import pathlib, numpy as np, rasterio, pandas as pd

# ── CONFIG ────────────────────────────────────────────────────────────────
DATA_DIR   = pathlib.Path("TIF_LST")                # folder with polygon_*.tif
CSV_OUT    = "lst_band_means.csv"                   # Excel‑friendly output
BAND_NAMES = ["LST_rabi", "LST_kharif", "LST_zaid"] # expected band order
SAVE_C     = False                                  # True → add *_C columns
# -------------------------------------------------------------------------

def f_to_c(f):          # °F → °C helper
    return (f - 32.0) * (5.0 / 9.0)

rows        = []        # one dict per file
master_cols = None      # set once from the first file

for tif in sorted(DATA_DIR.glob("polygon_*.tif")):
    with rasterio.open(tif) as src:
        if src.count != len(BAND_NAMES):
            raise ValueError(
                f"{tif.name}: expected {len(BAND_NAMES)} bands, got {src.count}"
            )

        means_f = []
        for i in range(1, src.count + 1):
            arr = src.read(i).astype("float32").ravel()
            arr = arr[~np.isnan(arr)]
            means_f.append(float(np.nan if arr.size == 0 else arr.mean()))

    # build row
    row = {"source": tif.name}                 # filename becomes the ID
    row.update(dict(zip(BAND_NAMES, means_f)))

    if SAVE_C:
        for k, v_f in zip(BAND_NAMES, means_f):
            row[k.replace("LST", "LST_C")] = None if np.isnan(v_f) else f_to_c(v_f)

    # remember canonical column order once
    if master_cols is None:
        master_cols = ["source"] + BAND_NAMES
        if SAVE_C:
            master_cols += [k.replace("LST", "LST_C") for k in BAND_NAMES]

    rows.append(row)

# ---- save as wide table --------------------------------------------------
df = pd.DataFrame(rows)[master_cols]   # enforce column order
df.to_csv(CSV_OUT, index=False)
print(f"✔ Band‑mean LST table for {len(rows)} files written to {CSV_OUT}")
df
