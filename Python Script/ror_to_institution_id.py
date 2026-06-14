import pandas as pd

# Change this path if your file is in a different folder
file_path = r"F:\學術\UW-Madison\HCI research\FSU\sciscinet_affiliations.parquet"

target_ror = "01y2jtd41"

# Read the affiliations file
affiliations = pd.read_parquet(file_path)

# Check columns first
print("Columns:")
print(affiliations.columns)

print("\nFirst 5 rows:")
print(affiliations.head())

# Search by ROR
matched = affiliations[
    affiliations["ror"].astype(str).str.contains(target_ror, case=False, na=False)
]

print("\nMatched rows:")
print(matched)

# Save result
matched.to_csv("matched_affiliations.csv", index=False)

print("\nSaved matched rows to matched_affiliations.csv")