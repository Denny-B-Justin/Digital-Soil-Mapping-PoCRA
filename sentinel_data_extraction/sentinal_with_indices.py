import json, re, pathlib, numpy as np, rasterio, pandas as pd

# ── CONFIG ────────────────────────────────────────────────────────────────
DATA_DIR   = pathlib.Path("indices_stack")        # folder with .tif + .json
CSV_OUT    = "polygon_band_means.csv"
fname_re   = re.compile(r"polygon_(\d+)\.tif$")
# ──────────────────────────────────────────────────────────────────────────

rows        = []        # one dict per polygon
master_cols = None      # canonical band order comes from the FIRST file

for tif in sorted(DATA_DIR.glob("polygon_*.tif")):
    # --- figure out a "source" identifier --------------------------------
    m = fname_re.search(tif.name)
    source_id = tif.name           # fallback: full stem

    # --- locate the matching JSON ----------------------------------------
    json_path = next(
        (p for p in [tif.with_suffix(".json"),
                     tif.with_name(tif.stem + "_bands.json")] if p.exists()),
        None
    )
    if json_path is None:
        print(f"[WARN] {tif.name}: no accompanying JSON; skipping.")
        continue

    band_names = json.loads(json_path.read_text())

    # --- read the image and compute per‑band means ------------------------
    with rasterio.open(tif) as src:
        if src.count != len(band_names):
            raise ValueError(
                f"{tif.name}: band count mismatch "
                f"(TIF={src.count}, JSON={len(band_names)})"
            )

        means = []
        for i in range(1, src.count + 1):
            arr = src.read(i).astype("float32").ravel()
            arr = arr[~np.isnan(arr)]
            means.append(float(np.nan if arr.size == 0 else arr.mean()))

    # --- remember the canonical column order (first file) ----------------
    if master_cols is None:
        master_cols = ["source"] + band_names

    # --- build the row dict ----------------------------------------------
    row = {"source": source_id}
    row.update(dict(zip(band_names, means)))
    rows.append(row)

# ---- build DataFrame in canonical column order and save -----------------
df = pd.DataFrame(rows)[master_cols]   # guarantees correct column ordering
df.to_csv(CSV_OUT, index=False)
print(f"✔ Band‑mean table for {len(rows)} polygons written to {CSV_OUT}")
