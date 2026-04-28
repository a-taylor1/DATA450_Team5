"""
fbfm40_process.py
-----------------
Processes the LF2024 FBFM40 raster + DBF attribute table into a wide-format
DataFrame, mirrors the EVC pipeline in datamining_project2_updated.ipynb.
 
Usage:
    python fbfm40_process.py
 
Outputs:
    fbfm40_wide.csv   – wide-format pixel table (X, Y, EVCODE, one-hot fuel model cols)
"""
 
import rasterio
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from geopandas import read_file
 
# ── FILE PATHS ────────────────────────────────────────────────────────────────
TIF_PATH = "landfire_data/1777406920393_LF2024_FBFM40_CONUS.tif"
DBF_PATH = "landfire_data/1777406920399_LF2024_FBFM40_CONUS.dbf"
OUTPUT_CSV = "fbfm40_wide.csv"
 
NODATA_RASTER = 32767   # raw NoData value stored in the TIF
NODATA_TABLE  = -9999   # NoData value used in the DBF key table
 
# ── 1. LOAD KEY TABLE (DBF) ───────────────────────────────────────────────────
print("Loading key table …")
key_table: pd.DataFrame = read_file(DBF_PATH)
key_table = key_table.drop(columns=["R", "G", "B", "RED", "GREEN", "BLUE"], errors="ignore")
 
# Standardise FBFM40 code strings to safe column names
# e.g. "GR1" → "gr1",  "Fill-NoData" → "fill-nodata"
key_table["class_name"] = (
    key_table["FBFM40"]
    .str.lower()
    .str.replace(r"[^a-z0-9]", "-", regex=True)   # symbols → hyphens
    .str.strip("-")
)
print(key_table[["VALUE", "FBFM40", "class_name"]].to_string(index=False))
 
# Build fast lookup dicts
code_to_name = dict(zip(key_table["VALUE"], key_table["class_name"]))
 
# All valid (non-NoData) class names become boolean columns
valid_classes = key_table.loc[key_table["VALUE"] != NODATA_TABLE, "class_name"].tolist()
 
# ── 2. READ RASTER ────────────────────────────────────────────────────────────
print("\nReading raster …")
with rasterio.open(TIF_PATH) as src:
    band = src.read(1)
    transform = src.transform
    cols_idx, rows_idx = np.meshgrid(np.arange(src.width), np.arange(src.height))
    xs, ys = transform * (cols_idx, rows_idx)
 
# ── 3. BUILD BASE DATAFRAME ───────────────────────────────────────────────────
print("Building map_df …")
map_df = pd.DataFrame({
    "x": xs.flatten(),
    "y": ys.flatten(),
    "VALUE": band.flatten().astype(np.int32),
})
 
# Map raster NoData (32767) → table NoData (-9999)
map_df["VALUE"] = map_df["VALUE"].replace(NODATA_RASTER, NODATA_TABLE)
 
# ── 4. CONSTRUCT WIDE-FORMAT new_df ──────────────────────────────────────────
print("Constructing wide DataFrame …")
new_df = pd.DataFrame({
    "X": map_df["x"],
    "Y": map_df["y"],
    "EVCODE": map_df["VALUE"],
})
 
# Initialise one boolean column per fuel model class
for c in valid_classes:
    new_df[c] = False
 
# Vectorised assignment: for each unique EVCODE, set its column to True
for code, col_name in code_to_name.items():
    if code == NODATA_TABLE:
        continue
    mask = new_df["EVCODE"] == code
    if mask.any() and col_name in new_df.columns:
        new_df.loc[mask, col_name] = True
 
# ── 5. CLEAN ──────────────────────────────────────────────────────────────────
print("Cleaning …")
 
# Drop NoData (fill) rows
new_df = new_df[new_df["EVCODE"] != NODATA_TABLE].reset_index(drop=True)
 
# Drop fill-nodata column if present
new_df = new_df.drop(columns=["fill-nodata"], errors="ignore")
 
# Drop any columns that ended up with only one unique value (all-False, etc.)
single_val_cols = [c for c in new_df.columns if new_df[c].nunique() <= 1]
new_df = new_df.drop(columns=single_val_cols)
print(f"  Dropped {len(single_val_cols)} single-value columns: {single_val_cols}")
 
# Normalise X/Y coords to [0, 1]
new_df["xStandard"] = (new_df["X"] - new_df["X"].min()) / (new_df["X"].max() - new_df["X"].min())
new_df["yStandard"] = (new_df["Y"] - new_df["Y"].min()) / (new_df["Y"].max() - new_df["Y"].min())
 
print(f"\nFinal shape: {new_df.shape}")
print("Columns:", new_df.columns.tolist())
print(new_df.head())
 
# ── 6. SUMMARY STATS ──────────────────────────────────────────────────────────
print("\nFuel model distribution (% of valid pixels):")
fuel_cols = [c for c in new_df.columns
             if c not in ("X", "Y", "EVCODE", "xStandard", "yStandard")]
dist = {c: new_df[c].sum() for c in fuel_cols}
dist_series = pd.Series(dist).sort_values(ascending=False)
total = len(new_df)
for name, count in dist_series.items():
    print(f"  {name:<40s} {count:>8,}  ({count/total*100:5.1f}%)")
 
# ── 7. SAVE ───────────────────────────────────────────────────────────────────
print(f"\nSaving to {OUTPUT_CSV} …")
new_df.to_csv(OUTPUT_CSV, index=False)
print("Done.")
 
# ── 8. HEXBIN MAP (spatial density of each fuel group) ───────────────────────
def hexplot_column(column_name: str, alt_title: str = None):
    if alt_title is None:
        alt_title = column_name
    plt.figure(figsize=(12, 10))
    hb = plt.hexbin(
        x=new_df["X"],
        y=new_df["Y"],
        C=new_df[column_name].astype(float),
        reduce_C_function=np.mean,
        gridsize=100,
        cmap="Oranges",
        mincnt=1,
    )
    plt.colorbar(hb, label=f"Fraction of pixels — {alt_title}")
    plt.title(f"Spatial Distribution: {alt_title}")
    plt.xlabel("X Coordinate")
    plt.ylabel("Y Coordinate")
    plt.tight_layout()
    plt.savefig(f"hexbin_{column_name}.png", dpi=150)
    plt.show()
    print(f"  Saved hexbin_{column_name}.png")
 
# Plot the top 3 fuel models by pixel count
top3 = dist_series.head(3).index.tolist()
print(f"\nPlotting hexbin maps for top 3 fuel models: {top3}")
for col in top3:
    hexplot_column(col)
