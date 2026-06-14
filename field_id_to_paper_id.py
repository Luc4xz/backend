import duckdb

con = duckdb.connect()

paperfields_path = r"F:\學術\UW-Madison\HCI research\FSU\sciscinet_paperfields.parquet"
uw_paper_ids_path = r"F:\學術\UW-Madison\HCI research\FSU\uw_madison_paper_ids.csv"

cs_field_id = "C41008148"

uw_cs_paper_ids = con.execute(f"""
    SELECT DISTINCT pf.paperid
    FROM '{paperfields_path}' AS pf
    INNER JOIN read_csv_auto('{uw_paper_ids_path}') AS uw
    ON pf.paperid = uw.paperid
    WHERE pf.fieldid = '{cs_field_id}'
""").fetchdf()

print(uw_cs_paper_ids.head())
print("Number of UW–Madison CS papers:", len(uw_cs_paper_ids))

uw_cs_paper_ids.to_csv("uw_madison_cs_paper_ids.csv", index=False)