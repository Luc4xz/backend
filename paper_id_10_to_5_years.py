import pandas as pd
from pathlib import Path

# =========================
# Input / Output paths
# =========================
input_path = r"F:\學術\UW-Madison\HCI research\FSU\csv&json\csv\uw_madison_cs_papers_unique_10yr.csv"
output_path = "uw_madison_cs_papers_unique_recent_5yr.csv"

# =========================
# Read CSV
# =========================
df = pd.read_csv(input_path)

# Make sure year is numeric
df["year"] = pd.to_numeric(df["year"], errors="coerce")

# =========================
# Extract recent 5 years
# Method: based on the latest year in your file
# =========================
latest_year = int(df["year"].max())
start_year = latest_year - 4

recent_5yr_df = df[
    (df["year"] >= start_year) &
    (df["year"] <= latest_year)
].copy()

# Optional: sort by year, then paperid
recent_5yr_df = recent_5yr_df.sort_values(["year", "paperid"])

# =========================
# Save result
# =========================
recent_5yr_df.to_csv(output_path, index=False)

print(f"Latest year in file: {latest_year}")
print(f"Extracted years: {start_year} - {latest_year}")
print(f"Rows before filtering: {len(df)}")
print(f"Rows after filtering: {len(recent_5yr_df)}")
print(f"Saved to: {output_path}")