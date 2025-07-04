'''
Multiple Output Random Forest - for numerical target variables (pH, OC, AWC)
Random Forest - for catagorical target variables (texture)
'''


import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, LabelEncoder
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.multioutput import MultiOutputRegressor
from sklearn.metrics import r2_score, accuracy_score
import matplotlib.pyplot as plt

df = pd.read_csv('final_merged_v2.csv')
df = df[df['profile'].str.endswith('_01')]

df = df.drop(columns=['profile', 'district', 'lat', 'long', 'ud', 'ld', 'lab no.','ec mscm-1', 'caco3 %', 'ex. ca+mg meq/100g soil',
       'ex.ca meq/100g soil', 'ex.mg meq/100g soil', 'ex.na meq/100g soil',
       'ex.k meq/100g soil', 'sum', 'cec cmol(p+)kg-1', 'base saturation %',
       'av.n kg/ha', 'av.p kg/ha', 'av. k kg/ha', 'fe mg/kg', 'mn mg/kg',
       'cu mg/kg', 'zn mg/kg', 'sand%', '% clay', 'silt%', 'bulk density', '1/3 bar %', '15 bar%', 'wilting point',
       'field capacity', 'pwp', 'fc', 'site_id', 'geometry_wkt', 'geometry', 'source'])  # replace with your actual column names
# df = df.dropna(axis=0, subset=y_cols)    # must have targets

# 2) Fill or impute other missing X’s
# df.fillna(df.median(), inplace=True)
df = df[~((df['B3_rabi'] == 0) & (df['B4_rabi'] == 0))]
# 2) Define numeric vs. categorical targets
y_num_cols = ['ph', 'organic carbon %', 'awc']
y_cat_col  = 'texture'

# 3) Drop any rows missing any target
df = df.dropna(subset=y_num_cols + [y_cat_col])

# 4) Build X and y
X     = df.drop(columns=y_num_cols + [y_cat_col])
y_num = df[y_num_cols]
y_cat = df[y_cat_col]

# 5) Encode the categorical target
le = LabelEncoder()
y_cat_enc = le.fit_transform(y_cat)

# 6) Train/test split (70/30)
X_train, X_test, \
y_num_train, y_num_test, \
y_cat_train, y_cat_test = train_test_split(
    X,             # features
    y_num,         # numeric targets
    y_cat_enc,     # encoded texture
    train_size=0.7,
    random_state=42
)

# 7) Multi-output regressor for numeric targets
reg = MultiOutputRegressor(
    RandomForestRegressor(n_estimators=100, max_depth=30, random_state=0)
)
reg.fit(X_train, y_num_train)

# 8) Classifier for texture
clf = RandomForestClassifier(n_estimators=100, max_depth=30, random_state=1)
clf.fit(X_train, y_cat_train)

# 9) Predict
y_num_pred = reg.predict(X_test)
y_cat_pred = le.inverse_transform(clf.predict(X_test))

# 10) Evaluate
print("Numeric targets R²:", r2_score(y_num_test, y_num_pred))
print("Texture classification accuracy:", accuracy_score(y_cat_test, le.transform(y_cat_pred)))

plt.scatter(
    y_num_test.iloc[:,0], y_num_test.iloc[:,1],
    c='navy', s=50, alpha=0.4, label='True'
)
plt.scatter(
    y_num_pred[:,0], y_num_pred[:,1],
    c='cornflowerblue', marker='s', s=50, alpha=0.4,
    label=f'Regressor R²={r2_score(y_num_test, y_num_pred):.2f}'
)
plt.xlabel('ph')
plt.ylabel('organic carbon %')
plt.legend()
plt.show()
