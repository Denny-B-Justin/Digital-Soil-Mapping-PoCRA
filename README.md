## Project Steps

### Step 1: Looking into the ground truth data

### Step 2: Create a 30m resolution bounding box for the ground truth data  
File: `bounding_box_geojson.py`

### Step 3: Extract required data from DEM (elevation, slope, MRRTF, etc) and save them as shape files  
File: `data_extraction.py`

### Step 4: Map the extracted data with the ground truth boundary boxes  
File: `mapping_dem.py`

### Step 5: Verify the mapped data with the provided calibration sample  
We run the whole code again, but with the latitude and longitude values from the calibration table  
File: `verify_dem_mapping.py`

---

## File Roles

- **Data Download:** `download_sentinal_data.py`  
- **Data Preprocessing:** `bounding_box_geojson.py → data_extraction.py → mapping_dem.py`  
- **Data Validation:** `verify_dem_mapping.ipynb`

