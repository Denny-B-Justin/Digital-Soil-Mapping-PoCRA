import pandas as pd
from functools import reduce

# --- FILE PATHS ---
base_file = "nbss_all_villages_new.csv"     # Priority file
other_files = [
    "groundtruth_with_dem_metrics.csv",
    "v2_gt_with_all_bands.csv",
    "gt_points_seasonal_climate.csv"
]

# --- READ MAIN DATAFRAME ---
df_main = pd.read_csv(base_file)

# --- LOAD AND MERGE OTHERS ---
def load_and_merge(df_base, other_file):
    df_other = pd.read_csv(other_file)
    return pd.merge(df_base, df_other, on=["lat", "long"], how="left")

# --- ITERATIVELY MERGE ALL FILES INTO df_main ---
df_merged = reduce(load_and_merge, other_files, df_main)

# --- RESULT ---
print("Merged dataframe shape:", df_merged.shape)
# Optional: df_merged.to_csv("final_merged.csv", index=False)
print("New Merged dataframe shape:", df_merged.shape)
df_merged = df_merged.drop_duplicates()  # Remove duplicates if any
print(df_merged.head())  # Display the first few rows of the merged dataframe
df_merged.to_csv("final_merged_file.csv", index=False)  # Save the merged dataframe
