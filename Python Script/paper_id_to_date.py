import duckdb

con = duckdb.connect()

# Change these paths to your real file locations
papers_path = r"F:\學術\UW-Madison\HCI research\FSU\sciscinet_papers.parquet"
uw_ids_path = r"F:\學術\UW-Madison\HCI research\FSU\uw_madison_cs_paper_ids.csv"


uw_papers_10yr = con.execute(f"""
    SELECT 
        p.paperid,
        p.year,
        p.date,
        p.cited_by_count,
        p.reference_count,
        p.citation_count,
        p.patent_count
    FROM '{papers_path}' AS p
    INNER JOIN read_csv_auto('{uw_ids_path}') AS u
    ON p.paperid = u.paperid
    WHERE p.year >= 2014
      AND p.is_retracted = false
""").fetchdf()

uw_papers_5yr = con.execute(f"""
    SELECT 
        p.paperid,
        p.year,
        p.date,
        p.cited_by_count,
        p.reference_count,
        p.citation_count,
        p.patent_count
    FROM '{papers_path}' AS p
    INNER JOIN read_csv_auto('{uw_ids_path}') AS u
    ON p.paperid = u.paperid
    WHERE p.year >= 2019
      AND p.is_retracted = false
""").fetchdf()

uw_papers_10yr.to_csv("uw_madison_papers_10yr.csv", index=False)
uw_papers_5yr.to_csv("uw_madison_papers_5yr.csv", index=False)

print("10-year papers:", len(uw_papers_10yr))
print("5-year papers:", len(uw_papers_5yr))