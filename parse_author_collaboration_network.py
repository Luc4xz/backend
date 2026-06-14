import duckdb
from pathlib import Path


# ============================================================
# Filter author-paper Parquet by selected UW-Madison recent 5-year papers
# Then output a smaller CSV for author collaboration network
# ============================================================

AUTHOR_PAPER_PARQUET = r"F:\學術\UW-Madison\HCI research\FSU\uw_madison_5yr_authors_paperid"

# This CSV should contain paper IDs from UW-Madison in recent 5 years
SELECTED_PAPERS_CSV = r"F:\學術\UW-Madison\HCI research\FSU\csv&json\csv\uw_madison_cs_papers_unique_recent_5yr.csv"

OUTPUT_CSV = "uw_madison_5yr_authors_paperid.csv"


def filter_authors_by_selected_papers(
    author_paper_parquet,
    selected_papers_csv,
    output_csv
):
    author_path = Path(author_paper_parquet)
    selected_path = Path(selected_papers_csv)
    output_path = Path(output_csv)

    if not author_path.exists():
        raise FileNotFoundError(f"Cannot find author-paper file: {author_paper_parquet}")

    if not selected_path.exists():
        raise FileNotFoundError(f"Cannot find selected paper CSV: {selected_papers_csv}")

    con = duckdb.connect()

    con.execute(f"""
        COPY (
            SELECT DISTINCT
                CAST(ap.authorid AS VARCHAR) AS authorid,
                CAST(ap.display_name AS VARCHAR) AS display_name,
                CAST(ap.paperid AS VARCHAR) AS paperid
            FROM read_parquet('{author_path.as_posix()}') AS ap
            INNER JOIN read_csv_auto('{selected_path.as_posix()}') AS sp
                ON CAST(ap.paperid AS VARCHAR) = CAST(sp.paperid AS VARCHAR)
            WHERE ap.authorid IS NOT NULL
              AND ap.paperid IS NOT NULL
              AND ap.display_name IS NOT NULL
        )
        TO '{output_path.as_posix()}'
        WITH (
            HEADER true,
            DELIMITER ','
        )
    """)

    print(f"Created filtered author-paper CSV: {output_csv}")


if __name__ == "__main__":
    filter_authors_by_selected_papers(
        AUTHOR_PAPER_PARQUET,
        SELECTED_PAPERS_CSV,
        OUTPUT_CSV
    )