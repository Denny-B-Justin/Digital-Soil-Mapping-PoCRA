import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

file_path = "/content/Pocra_district All Final Data_FINAL3MAY.xlsx"


sheets = pd.read_excel(file_path, sheet_name=None)

dfs = []
for sheet_name, df in sheets.items():
    if isinstance(df, pd.DataFrame) and not df.empty:
        df.columns = [col.strip().lower() for col in df.columns]
        if sheet_name.lower() == 'hingoli':
            cols = df.columns.tolist()
            if 'ud ld' in cols:
                idx = cols.index('ud ld')
                if idx + 1 < len(cols):
                    next_col = cols[idx + 1]
                    if next_col.strip() == '' or df[next_col].isna().all() or (df[next_col] == '').all():
                        df = df.rename(columns={'ud ld': 'ud', next_col: 'ld'})
        if 'lat' in df.columns:
            df['district'] = sheet_name
            dfs.append(df)


if dfs:
    df_merged = pd.concat(dfs, ignore_index=True)
    cols = df_merged.columns.tolist()
    lat_index = cols.index('lat')
    cols.insert(lat_index, cols.pop(cols.index('district')))
    df_merged = df_merged[cols]
    df_merged['lat'] = df_merged['lat'].ffill()
    df_merged['long'] = df_merged['long'].ffill()
    # print(df_merged)
else:
    print("No sheets with data and a 'lat' column were found.")

# df_merged.columns
def combine_columns(df, col_list, new_col):
    for col in col_list:
        if col in df.columns:
            if new_col in df.columns:
                df[new_col] = df[new_col].combine_first(df[col])
            else:
                df[new_col] = df[col]
    return df

col_variants = {
    'ud': ['ud', 'ud ld'],
    'ld': ['ld', 'unnamed: 4'],
    'site_id': ['site_id', 'unnamed: 3'],
    'bulk density': ['bulk density', 'bd'],
    'sand%': ['sand%', 'sand %'],
    'lab no.': ['lab no.', 'lab no', 'lab  no.'],
}

for main_col, variants in col_variants.items():
    df_merged = combine_columns(df_merged, variants, main_col)

to_drop = []
for main_col, variants in col_variants.items():
    for v in variants:
        if v != main_col and v in df_merged.columns:
            to_drop.append(v)
if to_drop:
    df_merged.drop(columns=to_drop, inplace=True)

cols = df_merged.columns.tolist()
main_cols = ['ud', 'ld', 'lab no.']
long_idx = cols.index('long') + 1
for c in reversed(main_cols):
    if c in cols:
        cols.insert(long_idx, cols.pop(cols.index(c)))
df_merged = df_merged[cols]
df_merged.drop(columns=['pwp.1', 'fc.1', 'awc.1'], inplace=True)
print(df_merged.columns)

df_merged.to_csv('nbss_all_villages_new.csv', index=False)
