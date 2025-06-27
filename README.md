## Project Steps

### Step 1: Looking into the ground truth data

### Step 2: Create a 30m resolution bounding box for the ground truth data  
File: `bounding_box_geojson.py`

### Step 3: Extract required data from DEM (elevation, slope, etc) and save them as shape files  
File: `basic_data_extraction.py`

### Step 4: Map the extracted data with the ground truth boundary boxes  
File: `mapping_dem.py`

### Step 5: Verify the mapped data with the provided calibration sample  
We run the whole code again, but with the latitude and longitude values from the calibration table  
File: `verify_dem_mapping.py`

### Step 6: Extract the required data directly from the HGT files for point
All the required data are extracted directly from HGT files. Contains code to extract data from each ground truth point (not bounding box). The final output exported as CSV which can be then used for ML modelling.
File: `point_all_value_extraction.py` 

### Step 7: Extract the data for ground truth GeoJSON
Since we wanted the weighted average of each parameter, match the DEM parameters with bounding box coordinates. The code contains data extraction for each bounding box.     
File: ` `

---

## File Roles

- **Data Download:** `download_sentinal_data.py`  
- **Data Preprocessing:** `bounding_box_geojson.py → data_extraction.py → mapping_dem.py`  
- **Data Validation:** `verify_dem_mapping.ipynb`

