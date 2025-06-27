import os
import math
import numpy as np
import pandas as pd
import rasterio
from rasterio.transform import from_origin
import rasterio.transform
from scipy.ndimage import uniform_filter
from matplotlib.colors import LightSource
import pvlib

def read_hgt(file_path):
    """Reads a .hgt file and returns (dem array, affine transform, crs)."""
    size = os.path.getsize(file_path)
    if size == 3601*3601*2:
        res = 3601
    elif size == 1201*1201*2:
        res = 1201
    else:
        raise ValueError("Unknown .hgt resolution")
    data = np.fromfile(file_path, '>i2').reshape((res, res))
    data = np.where(data == -32768, np.nan, data)
    fn = os.path.basename(file_path)
    lat = int(fn[1:3]) * (-1 if fn[0]=='S' else 1)
    lon = int(fn[4:7]) * (-1 if fn[3]=='W' else 1)
    pix = 1/(res-1)
    transform = from_origin(lon, lat+1, pix, pix)
    return data, transform, 'EPSG:4326'

def extract_point_metrics(hgt_file, points):
    """
    Given an .hgt DEM and a list of (lat, lon) tuples,
    returns a dict mapping each point to its metrics.
    """
    dem, transform, crs = read_hgt(hgt_file)
    nrows, ncols = dem.shape

    # meters per pixel (approx at mid-latitude)
    midlat = transform.f - transform.e*(nrows/2)
    latrad = math.radians(midlat)
    dx = transform.a * 111320 * math.cos(latrad)
    dy = -transform.e * 110574

    # precompute hillshade for the whole DEM
    ls = LightSource(azdeg=315, altdeg=45)
    hill = ls.hillshade(dem, vert_exag=1, dx=dx, dy=dy)

    results = {}
    for lat, lon in points:
        # map to row, col
        row, col = rasterio.transform.rowcol(transform, lon, lat)
        if not (1 <= row < nrows-1 and 1 <= col < ncols-1):
            raise IndexError(f"Point {(lat,lon)} too close to DEM edge")

        # extract 3×3 window
        win = dem[row-1:row+2, col-1:col+2]
        center = win[1,1]
        neigh = win.flatten()
        neigh = neigh[~np.isnan(neigh)]

        # 1. Elevation
        elev = center

        # 2. Terrain Ruggedness Index (TRI)
        tri = np.mean(np.abs(neigh - center))

        # 3. Slope (degrees) via central differences
        dzdx = (dem[row, col+1] - dem[row, col-1]) / (2*dx)
        dzdy = (dem[row+1, col] - dem[row-1, col]) / (2*dy)
        slope_rad = math.atan(math.hypot(dzdx, dzdy))
        slope_deg = math.degrees(slope_rad)

        # 4. Mid-Slope Position (MSP)
        msp = center - (neigh.max() + neigh.min()) / 2.0

        # 5. Relative Slope Position (RSP)
        rsp = (center - neigh.min()) / (neigh.max() - neigh.min() + 1e-9)

        # 6. MRVBF & MRRTF (scales 3, 9, 27)
        scales = [3, 9, 27]
        flat_vals  = [uniform_filter(dem, s)[row, col] - center for s in scales]
        ridge_vals = [center - uniform_filter(dem, s)[row, col] for s in scales]
        mrvbf = np.mean(flat_vals)
        mrrtf = np.mean(ridge_vals)

        # 7. Hillshade
        hillshade_val = hill[row, col]

        # 8. Single-day insolation (2025-05-01)
        day = pd.Timestamp("2025-05-01")
        sp = pvlib.solarposition.get_solarposition(day, lat, lon)
        zen = sp['zenith'].iloc[0]
        azi = sp['azimuth'].iloc[0]
        dni_ext = pvlib.irradiance.get_extra_radiation(day.dayofyear)
        ghi = max(dni_ext * math.cos(math.radians(zen)), 0)
        dhi = 0.1 * ghi
        insol = pvlib.irradiance.haydavies(
            0,        # surface_tilt
            0,        # surface_azimuth
            ghi,
            dni_ext,
            dhi,
            dni_ext,
            zen,
            azi
        )

        results[(lat, lon)] = {
            "elevation": elev,
            "TRI": tri,
            "slope_deg": slope_deg,
            "MSP": msp,
            "RSP": rsp,
            "MRVBF": mrvbf,
            "MRRTF": mrrtf,
            "hillshade": hillshade_val,
            "insolation_20250501": insol
        }

    return results

if __name__ == "__main__":
    dem_file = "N18E075.hgt"
    points   = [(18.9750176562139, 75.0214335630754)]
    metrics  = extract_point_metrics(dem_file, points)
    for pt, m in metrics.items():
        print(f"Point {pt}:")
        for key, val in m.items():
            print(f"  {key}: {val}")
        print()
