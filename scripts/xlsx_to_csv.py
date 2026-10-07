"""One-time step: convert the raw Excel file into a compact, typed CSV.gz.

Why: parsing .xlsx (zipped XML) is slow and memory hungry. We pay that cost once
and commit a small file, so the server never touches Excel.
"""
import pandas as pd

SRC = "data/data.xlsx"
DST = "data/lines.csv.gz"

df = pd.read_excel(SRC)
print("rows read:", len(df))

# Order_Datetime is DD-MM-YYYY HH:MM:SS in the brief; handle both text and real datetimes.
if not pd.api.types.is_datetime64_any_dtype(df["Order_Datetime"]):
    df["Order_Datetime"] = pd.to_datetime(df["Order_Datetime"], format="%d-%m-%Y %H:%M:%S")

# --- basic data-quality checks (documented in the README) ---
assert df.isna().sum().sum() == 0, "unexpected nulls"
print("duplicate rows:", df.duplicated().sum())
print("zero-price rows (free dips):", (df["Price"] == 0).sum())

df["Order_Datetime"] = df["Order_Datetime"].dt.strftime("%Y-%m-%d %H:%M:%S")
df.to_csv(DST, index=False, compression="gzip")
print("wrote", DST)