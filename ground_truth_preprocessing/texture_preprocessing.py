import re
import pandas as pd

# --- EXAMPLE DATAFRAME ---------------------------------------
# df = pd.read_csv("your_file.csv")          # real workflow
# df['texture_raw'] = [...]                 # the messy column name

# --- NORMALISATION + CATEGORISATION --------------------------
def normalise(tx):
    """
    Safe normalisation:
    - Handles None, NaN, float, etc.
    - Lowercases, strips, removes parenthesis text, collapses whitespace
    """
    if not isinstance(tx, str):
        if pd.isna(tx):
            return ''
        tx = str(tx)
    tx = tx.lower().strip()
    tx = re.sub(r'\([^)]*\)', '', tx)        # remove anything in ()
    return re.sub(r'\s+', ' ', tx)           # collapse whitespace

def classify(tx):
    """
    Returns USDA-style two/three-letter code
    (all caps) for the cleaned string.
    """
    tx = normalise(tx)

    # order matters – test most-specific patterns first
    rules = [
        (r'sandy clay loam',        'sandy clay loam'),
        (r'silty clay loam',        'silty clay loam'),
        (r'clay loam',              'clay loam'),
        (r'sandy loam',             'sandy loam'),
        (r'silt loam',              'silt loam'),
        (r'sandy clay',             'sandy clay'),
        (r'silty clay',             'silty clay'),
        (r'\bloam\b',               'loam'),
        (r'\bsand\b',               'sand'),
        (r'\bsilt\b',               'silt'),
        (r'\bclay\b',               'clay'),
    ]
    for pat, code in rules:
        if re.search(pat, tx):
            return code
    return 'NA'                      # or pd.NA / None if you prefer



# --- APPLY TO YOUR DATAFRAME ---------------------------------
df_merged['texture'] = df_merged["texture"].apply(classify)

df_merged['texture'].unique()  # Display counts of each texture code
