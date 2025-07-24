import pandas as pd
import numpy as np

def texture_from_values(sand: float, clay: float, silt: float) -> str:
    
    # --- branch 1: clay ≥ 40 % ------------------------------------
    if clay >= 40:
        if silt >= 40:
            return "silty clay"
        elif sand >= 45:
            return "sandy clay"
        else:
            return "clay"

    # --- branch 2: 27 % ≤ clay < 40 % -----------------------------
    if clay >= 27:
        if silt >= 28:
            return "silty clay loam"
        elif sand >= 20:
            return "sandy clay loam"
        else:
            return "clay loam"

    # --- branch 3: 20 % ≤ clay < 27 % -----------------------------
    if clay >= 20:
        if sand >= 52:
            return "sandy loam"
        elif silt >= 50:
            return "silt loam"
        else:
            return "loam"

    # --- branch 4: clay < 20 % ------------------------------------
    if clay < 7:                       # very low clay
        if sand >= 85:
            return "sand"
        elif sand >= 70:
            return "loamy sand"
        else:
            return "sandy loam"
    else:                              # 7 % ≤ clay < 20 %
        if silt >= 80:
            return "silt"
        elif silt >= 50:
            return "silt loam"
        else:
            return "loam"


# ------------------------------------------------------------------
# 2. Vectorised DataFrame helper -----------------------------------
# ------------------------------------------------------------------
def assign_texture(df: pd.DataFrame,
                   sand_col: str = "D",
                   clay_col: str = "E",
                   silt_col: str = "F",
                   out_col: str  = "texture") -> pd.DataFrame:
    
    sand = df[sand_col]
    clay = df[clay_col]
    silt = df[silt_col]

    # Each condition mirrors the same hierarchy as the nested IFs
    conds  = [
        (clay >= 40) & (silt >= 40),
        (clay >= 40) & (silt < 40) & (sand >= 45),
        (clay >= 40) & (silt < 40) & (sand < 45),

        (clay >= 27) & (clay < 40) & (silt >= 28),
        (clay >= 27) & (clay < 40) & (silt < 28) & (sand >= 20),
        (clay >= 27) & (clay < 40) & (silt < 28) & (sand < 20),

        (clay >= 20) & (clay < 27) & (sand >= 52),
        (clay >= 20) & (clay < 27) & (sand < 52) & (silt >= 50),
        (clay >= 20) & (clay < 27) & (sand < 52) & (silt < 50),

        (clay < 20) & (clay < 7)  & (sand >= 85),
        (clay < 20) & (clay < 7)  & (sand < 85) & (sand >= 70),
        (clay < 20) & (clay < 7)  & (sand < 70),

        (clay < 20) & (clay >= 7) & (silt >= 80),
        (clay < 20) & (clay >= 7) & (silt < 80) & (silt >= 50),
        (clay < 20) & (clay >= 7) & (silt < 50),
    ]

    choices = [
        "silty clay", "sandy clay", "clay",
        "silty clay loam", "sandy clay loam", "clay loam",
        "sandy loam", "silt loam", "loam",
        "sand", "loamy sand", "sandy loam",
        "silt", "silt loam", "loam",
    ]

    df[out_col] = np.select(conds, choices, default="undefined")
    return df

