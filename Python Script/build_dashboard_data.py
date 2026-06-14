"""
Build one website-ready JSON file for coordinated D3 interaction:

1) Timeline: paper count by year
2) Patent histogram: Patent_Count distribution for the selected year

Why this script needs paper-level data:
The timeline JSON only stores {year, paper_count}.
The existing patent distribution JSON only stores the overall histogram.
For click-to-update interaction, the website needs histograms grouped by year,
so the script must read a paper-level file that has at least:
    year, patent_count
or:
    year, Patent_Count

Example:
python build_dashboard_data.py \
  --papers uw_madison_cs_papers_10yr.csv \
  --growth paper_growth_10yr.json \
  --global-patent patent_count_distribution.json \
  --output dashboard_data.json
"""

import argparse
import json
from pathlib import Path

import pandas as pd


def load_table(path: str) -> pd.DataFrame:
    """Load CSV, JSON, JSONL, or Parquet paper-level data."""
    p = Path(path)
    suffix = p.suffix.lower()

    if suffix == ".csv":
        return pd.read_csv(p)
    if suffix in [".json", ".js"]:
        return pd.read_json(p)
    if suffix == ".jsonl":
        return pd.read_json(p, lines=True)
    if suffix in [".parquet", ".pq"]:
        return pd.read_parquet(p)

    raise ValueError(f"Unsupported paper-level file type: {suffix}")


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Make column names predictable."""
    rename_map = {}

    for col in df.columns:
        lower = col.lower()
        if lower == "patent_count":
            rename_map[col] = "patent_count"
        elif lower == "year":
            rename_map[col] = "year"
        elif lower == "paperid":
            rename_map[col] = "paperid"

    df = df.rename(columns=rename_map)

    required = {"year", "patent_count"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(
            f"Missing required column(s): {missing}. "
            "Your paper-level file must contain year and patent_count/Patent_Count."
        )

    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["patent_count"] = pd.to_numeric(df["patent_count"], errors="coerce").fillna(0)

    df = df.dropna(subset=["year"])
    df["year"] = df["year"].astype(int)
    df["patent_count"] = df["patent_count"].astype(int)

    # If paperid exists, remove duplicate papers so the same paper is not counted twice.
    if "paperid" in df.columns:
        df["paperid"] = df["paperid"].astype(str)
        df = df.drop_duplicates(subset=["paperid"])

    return df


def build_timeline_from_papers(df: pd.DataFrame) -> list[dict]:
    """Create timeline directly from paper-level data."""
    timeline = (
        df.groupby("year")
        .size()
        .reset_index(name="paper_count")
        .sort_values("year")
    )
    return timeline.to_dict(orient="records")


def build_histograms_by_year(df: pd.DataFrame) -> dict[str, list[dict]]:
    """Create {year: [{patent_count, paper_count}, ...]} for D3 lookup."""
    grouped = (
        df.groupby(["year", "patent_count"])
        .size()
        .reset_index(name="paper_count")
        .sort_values(["year", "patent_count"])
    )

    by_year: dict[str, list[dict]] = {}
    for year, group in grouped.groupby("year"):
        by_year[str(int(year))] = [
            {
                "patent_count": int(row["patent_count"]),
                "paper_count": int(row["paper_count"]),
            }
            for _, row in group.iterrows()
        ]

    return by_year


def load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--papers", required=True, help="Paper-level CSV/JSON/JSONL/Parquet with year and patent_count.")
    parser.add_argument("--growth", default=None, help="Optional existing paper_growth_10yr.json.")
    parser.add_argument("--global-patent", default=None, help="Optional existing global patent_count_distribution.json.")
    parser.add_argument("--output", default="dashboard_data.json")
    parser.add_argument("--start-year", type=int, default=None)
    parser.add_argument("--end-year", type=int, default=None)
    args = parser.parse_args()

    papers = normalize_columns(load_table(args.papers))

    if args.start_year is not None:
        papers = papers[papers["year"] >= args.start_year]
    if args.end_year is not None:
        papers = papers[papers["year"] <= args.end_year]

    timeline = load_json(args.growth) if args.growth else build_timeline_from_papers(papers)
    histograms_by_year = build_histograms_by_year(papers)

    output = {
        "title": "UW-Madison CS Papers Dashboard Data",
        "description": "Use timeline for the line/bar chart. When a year is clicked, use patentHistogramByYear[String(year)] to update the histogram.",
        "timeline": timeline,
        "patentHistogramByYear": histograms_by_year,
    }

    if args.global_patent:
        output["globalPatentHistogram"] = load_json(args.global_patent)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print(f"Created {args.output}")
    print(f"Years available for interaction: {', '.join(output['patentHistogramByYear'].keys())}")


if __name__ == "__main__":
    main()
