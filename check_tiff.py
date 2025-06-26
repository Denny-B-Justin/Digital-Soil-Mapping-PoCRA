'''
Use this code to check if your downloaded sentinal/HLS data have required sentinal values or not.
Install rasterio by: pip install rasterio
'''

import rasterio

tif_path = " % TIF File path % "

with rasterio.open(tif_path) as src:
    print("---- General Info ----")
    print(f"File: {tif_path}")
    print(f"CRS: {src.crs}")
    print(f"Width: {src.width}")
    print(f"Height: {src.height}")
    print(f"Number of bands: {src.count}")
    print(f"Bounds: {src.bounds}")
    print(f"Data type: {src.dtypes}")
    print(f"Driver: {src.driver}")

    print("\n---- Metadata ----")
    print(src.meta)

    print("\n---- Band Info ----")
    for i in range(1, src.count + 1):
        print(f"Band {i}:")
        band = src.read(i)
        print(f"  Shape: {band.shape}")
        print(f"  Min: {band.min()}")
        print(f"  Max: {band.max()}")
        print(f"  Mean: {band.mean()}")
        print(f"  Data type: {band.dtype}")

    print("\n---- Tags ----")
    print(src.tags())
