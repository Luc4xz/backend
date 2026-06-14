import duckdb

con = duckdb.connect()

file_path = r"F:\學術\UW-Madison\HCI research\FSU\sciscinet_paper_author_affiliation.parquet"

target_institution_id = "I135310074"

uw_papers = con.execute(f"""
    SELECT DISTINCT paperid
    FROM '{file_path}'
    WHERE institutionid = '{target_institution_id}'
""").fetchdf()

print(uw_papers.head())
print("Number of UW–Madison papers:", len(uw_papers))

uw_papers.to_csv("uw_madison_paper_ids.csv", index=False)