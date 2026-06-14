import duckdb
import json
from pathlib import Path


# ============================================================
# Build author collaboration network JSON
# Excluding huge-author papers!!!
# ============================================================

INPUT_CSV = r"F:\學術\UW-Madison\HCI research\FSU\csv&json\csv\uw_madison_5yr_authors_paperid.csv"
OUTPUT_JSON = "uw_madison_5yr_author_collaboration_no_huge_papers.json"

# Important setting:
# Papers with more than this number of authors will be excluded.
# Recommended:
# 20 = safest and most readable
# 50 = larger graph
# 100 = very large
MAX_AUTHORS_PER_PAPER = 60

MIN_SHARED_PAPERS = 1
MIN_AUTHOR_PAPERS = 1


def build_author_collaboration_network(input_csv, output_json):
    input_path = Path(input_csv)
    output_path = Path(output_json)

    if not input_path.exists():
        raise FileNotFoundError(f"Cannot find input CSV: {input_csv}")

    con = duckdb.connect("author_network.duckdb")

    # Optional but helpful for large files
    con.execute("PRAGMA memory_limit='8GB'")
    con.execute("PRAGMA threads=4")
    con.execute("PRAGMA temp_directory='duckdb_temp'")
    con.execute("PRAGMA max_temp_directory_size='100GiB'")

    print("Reading author-paper CSV...")

    con.execute(f"""
        CREATE OR REPLACE TABLE author_papers AS
        SELECT DISTINCT
            CAST(authorid AS VARCHAR) AS authorid,
            CAST(display_name AS VARCHAR) AS display_name,
            CAST(paperid AS VARCHAR) AS paperid
        FROM read_csv_auto('{input_path.as_posix()}')
        WHERE authorid IS NOT NULL
          AND display_name IS NOT NULL
          AND paperid IS NOT NULL
    """)

    print("Counting authors per paper...")

    con.execute("""
        CREATE OR REPLACE TABLE paper_author_counts AS
        SELECT
            paperid,
            COUNT(DISTINCT authorid) AS author_count
        FROM author_papers
        GROUP BY paperid
    """)

    total_papers = con.execute("""
        SELECT COUNT(*)
        FROM paper_author_counts
    """).fetchone()[0]

    excluded_papers = con.execute(f"""
        SELECT COUNT(*)
        FROM paper_author_counts
        WHERE author_count > {MAX_AUTHORS_PER_PAPER}
    """).fetchone()[0]

    kept_papers = total_papers - excluded_papers

    print(f"Total papers: {total_papers}")
    print(f"Kept papers: {kept_papers}")
    print(f"Excluded huge-author papers: {excluded_papers}")

    print("Filtering out huge-author papers...")

    con.execute(f"""
        CREATE OR REPLACE TABLE filtered_author_papers AS
        SELECT ap.*
        FROM author_papers ap
        INNER JOIN paper_author_counts pac
            ON ap.paperid = pac.paperid
        WHERE pac.author_count >= 2
          AND pac.author_count <= {MAX_AUTHORS_PER_PAPER}
    """)

    print("Building collaboration links...")

    con.execute(f"""
        CREATE OR REPLACE TABLE author_links AS
        SELECT
            ap1.authorid AS source,
            ap2.authorid AS target,
            COUNT(DISTINCT ap1.paperid) AS weight,
            LIST(DISTINCT ap1.paperid) AS shared_papers
        FROM filtered_author_papers ap1
        INNER JOIN filtered_author_papers ap2
            ON ap1.paperid = ap2.paperid
           AND ap1.authorid < ap2.authorid
        GROUP BY ap1.authorid, ap2.authorid
        HAVING COUNT(DISTINCT ap1.paperid) >= {MIN_SHARED_PAPERS}
    """)

    print("Building author nodes...")

    con.execute("""
        CREATE OR REPLACE TABLE connected_authors AS
        SELECT source AS authorid FROM author_links
        UNION
        SELECT target AS authorid FROM author_links
    """)

    con.execute(f"""
        CREATE OR REPLACE TABLE author_nodes AS
        SELECT
            ap.authorid AS id,
            ANY_VALUE(ap.display_name) AS name,
            COUNT(DISTINCT ap.paperid) AS paper_count
        FROM filtered_author_papers ap
        INNER JOIN connected_authors ca
            ON ap.authorid = ca.authorid
        GROUP BY ap.authorid
        HAVING COUNT(DISTINCT ap.paperid) >= {MIN_AUTHOR_PAPERS}
    """)

    print("Counting collaborators...")

    con.execute("""
        CREATE OR REPLACE TABLE collaborator_counts AS
        SELECT
            authorid,
            COUNT(DISTINCT collaboratorid) AS collaborator_count
        FROM (
            SELECT source AS authorid, target AS collaboratorid
            FROM author_links

            UNION ALL

            SELECT target AS authorid, source AS collaboratorid
            FROM author_links
        )
        GROUP BY authorid
    """)

    print("Exporting nodes...")

    node_rows = con.execute("""
        SELECT
            n.id,
            n.name,
            n.paper_count,
            COALESCE(c.collaborator_count, 0) AS collaborator_count
        FROM author_nodes n
        LEFT JOIN collaborator_counts c
            ON n.id = c.authorid
        ORDER BY n.paper_count DESC, collaborator_count DESC
    """).fetchall()

    nodes = [
        {
            "id": authorid,
            "name": name,
            "paper_count": int(paper_count),
            "collaborator_count": int(collaborator_count),
            "type": "author"
        }
        for authorid, name, paper_count, collaborator_count in node_rows
    ]

    print("Exporting links...")

    link_rows = con.execute("""
        SELECT
            source,
            target,
            weight,
            shared_papers
        FROM author_links
        ORDER BY weight DESC
    """).fetchall()

    links = [
        {
            "source": source,
            "target": target,
            "weight": int(weight),
            "shared_paper_count": int(weight),
            "shared_papers": list(shared_papers),
            "type": "collaboration"
        }
        for source, target, weight, shared_papers in link_rows
    ]

    output_data = {
        "metadata": {
            "title": "UW-Madison 5-Year Author Collaboration Network",
            "description": "Authors are nodes. Two authors are connected if they wrote at least one paper together. Huge-author papers are excluded to avoid pair explosion.",
            "source_file": str(input_csv),
            "total_papers_before_filter": int(total_papers),
            "kept_papers": int(kept_papers),
            "excluded_huge_author_papers": int(excluded_papers),
            "max_authors_per_paper": MAX_AUTHORS_PER_PAPER,
            "total_nodes": len(nodes),
            "total_links": len(links),
            "min_shared_papers": MIN_SHARED_PAPERS,
            "min_author_papers": MIN_AUTHOR_PAPERS
        },
        "nodes": nodes,
        "links": links
    }

    print("Writing JSON file...")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False)

    print(f"Created: {output_json}")
    print(f"Nodes: {len(nodes)}")
    print(f"Links: {len(links)}")


if __name__ == "__main__":
    build_author_collaboration_network(INPUT_CSV, OUTPUT_JSON)