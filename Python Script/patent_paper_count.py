import pandas as pd
import json

input_path = r"F:\學術\UW-Madison\HCI research\FSU\csv&json\uw_madison_cs_papers_10yr.csv"

output_unique_csv = "uw_madison_cs_papers_unique_patent_count.csv"
output_hist_json = "patent_count_distribution.json"

# Read file
df = pd.read_csv(input_path)

# Make sure columns are clean
df.columns = df.columns.str.strip()

# Convert patent_count to number
df["patent_count"] = pd.to_numeric(df["patent_count"], errors="coerce").fillna(0).astype(int)

# Convert year to number
df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")

# Keep one row per unique paperid
# If the same paperid appears multiple times, keep the max patent_count
unique_papers = (
    df.groupby("paperid", as_index=False)
      .agg({
          "year": "first",
          "date": "first",
          "cited_by_count": "max",
          "reference_count": "max",
          "citation_count": "max",
          "patent_count": "max"
      })
)

# Sort by patent_count from high to low
unique_papers = unique_papers.sort_values(
    by="patent_count",
    ascending=False
)

# Save sorted unique paper list
unique_papers.to_csv(output_unique_csv, index=False)

# Build patent_count histogram data
distribution = (
    unique_papers["patent_count"]
    .value_counts()
    .sort_index()
    .reset_index()
)

distribution.columns = ["patent_count", "paper_count"]

# Save as JSON for website histogram
histogram_data = {
    "title": "Patent Citation Distribution of UW-Madison CS Papers",
    "total_unique_papers": int(len(unique_papers)),
    "histogram": distribution.to_dict(orient="records")
}

with open(output_hist_json, "w", encoding="utf-8") as f:
    json.dump(histogram_data, f, indent=2)

print("Done.")
print(f"Unique papers saved to: {output_unique_csv}")
print(f"Histogram JSON saved to: {output_hist_json}")
print(f"Total unique papers: {len(unique_papers)}")