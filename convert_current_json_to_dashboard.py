import json
from pathlib import Path


# =========================
# Input JSON files
# =========================
# Put this script in the same folder as your JSON files,
# or change these paths to your actual file locations.

PAPER_GROWTH_FILE = r"F:\學術\UW-Madison\HCI research\FSU\Web\paper_growth_10yr.json"
PATENT_DISTRIBUTION_FILE = r"F:\學術\UW-Madison\HCI research\FSU\Web\patent_count_distribution.json"

OUTPUT_FILE = "dashboard_data.json"


def read_json(file_path):
    """Read a JSON file and return Python data."""
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Cannot find file: {file_path}")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(data, file_path):
    """Write Python data into a JSON file."""
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"New JSON file created: {file_path}")


def build_dashboard_json(paper_growth_data, patent_distribution_data):
    """
    Convert the current JSON files into one website-friendly JSON file.

    Output structure:
    {
      "timeline": [...],
      "defaultPatentHistogram": [...],
      "metadata": {...}
    }

    Note:
    This script uses the current patent distribution as the default/global histogram.
    It does NOT create year-by-year patent histograms because the current patent JSON
    does not contain year information.
    """

    timeline = []

    for item in paper_growth_data:
        timeline.append({
            "year": int(item["year"]),
            "paper_count": int(item["paper_count"])
        })

    # Sort timeline by year
    timeline.sort(key=lambda x: x["year"])

    default_patent_histogram = []

    for item in patent_distribution_data["histogram"]:
        default_patent_histogram.append({
            "patent_count": int(item["patent_count"]),
            "paper_count": int(item["paper_count"])
        })

    dashboard_data = {
        "metadata": {
            "title": "UW-Madison CS Paper Dashboard",
            "description": "Timeline of CS-related papers and global patent citation distribution.",
            "interaction_note": (
                "Clicking a year can update the histogram only if year-by-year "
                "patent histogram data is added later."
            ),
            "total_unique_papers": patent_distribution_data.get("total_unique_papers")
        },
        "timeline": timeline,
        "defaultPatentHistogram": default_patent_histogram
    }

    return dashboard_data


def main():
    # Step 1: read current JSON files
    paper_growth_data = read_json(PAPER_GROWTH_FILE)
    patent_distribution_data = read_json(PATENT_DISTRIBUTION_FILE)

    # Step 2: transform them into website-friendly format
    dashboard_data = build_dashboard_json(
        paper_growth_data,
        patent_distribution_data
    )

    # Step 3: output new JSON file
    write_json(dashboard_data, OUTPUT_FILE)


if __name__ == "__main__":
    main()
