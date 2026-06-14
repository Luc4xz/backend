import pandas as pd
import json

# Input CSV file
input_csv = r"F:\學術\UW-Madison\HCI research\FSU\csv&json\csv\uw_madison_cs_papers_unique_10yr.csv"

# Output JSON file
output_json = "paper_growth_10yr.json"

# Read CSV
df = pd.read_csv(input_csv)

# Make sure paperid is treated as string
df["paperid"] = df["paperid"].astype(str)

# Remove duplicated papers
df_unique = df.drop_duplicates(subset=["paperid"])

# Count number of papers per year
year_counts = (
    df_unique
    .groupby("year")
    .size()
    .reset_index(name="paper_count")
)

# Sort by year
year_counts = year_counts.sort_values("year")

# Convert to JSON-friendly format
timeline_data = year_counts.to_dict(orient="records")

# Save as JSON
with open(output_json, "w", encoding="utf-8") as f:
    json.dump(timeline_data, f, indent=2)

print(f"Saved timeline data to {output_json}")
print(timeline_data)