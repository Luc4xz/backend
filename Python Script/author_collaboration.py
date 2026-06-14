import duckdb
import pandas as pd
import json

selected_papers_path = r"F:\學術\UW-Madison\HCI research\FSU\csv&json\csv\uw_madison_cs_paper_ids.csv"
papers_meta_path = r"F:\學術\UW-Madison\HCI research\FSU\sciscinet_papers.parquet"
paperrefs_path = r"F:\學術\UW-Madison\HCI research\FSU\sciscinet_paperrefs.parquet"

START_YEAR = 2019
END_YEAR = 2024

selected_df = pd.read_csv(selected_papers_path)
selected_df["paperid"] = selected_df["paperid"].astype(str)

con = duckdb.connect()
con.register("selected_papers", selected_df)

# Step 1: keep ALL selected UW-Madison CS papers in the year range
nodes = con.execute(f"""
    SELECT
        p.paperid AS id,
        p.year,
        p.citation_count,
        p.reference_count,
        p.patent_count,
        p.doctype,
        p.team_size,
        p.institution_count
    FROM read_parquet('{papers_meta_path}') p
    INNER JOIN selected_papers s
        ON p.paperid = s.paperid
    WHERE p.year BETWEEN {START_YEAR} AND {END_YEAR}
""").df()

nodes["id"] = nodes["id"].astype(str)

print("Selected nodes:", len(nodes))

con.register("nodes", nodes)

# Step 2: find citation edges among ALL selected papers
edges = con.execute(f"""
    SELECT
        r.citing_paperid AS source,
        r.cited_paperid AS target,
        r.year,
        r.ref_year,
        r.year_diff
    FROM read_parquet('{paperrefs_path}') r
    INNER JOIN nodes n1
        ON r.citing_paperid = n1.id
    INNER JOIN nodes n2
        ON r.cited_paperid = n2.id
    WHERE r.year BETWEEN {START_YEAR} AND {END_YEAR}
""").df()

edges["source"] = edges["source"].astype(str)
edges["target"] = edges["target"].astype(str)
edges["type"] = "citation"

print("Edges:", len(edges))

# Step 3: optional degree information for tooltips
in_degree = edges.groupby("target").size().reset_index(name="in_degree")
out_degree = edges.groupby("source").size().reset_index(name="out_degree")

nodes = nodes.merge(in_degree, left_on="id", right_on="target", how="left")
nodes = nodes.merge(out_degree, left_on="id", right_on="source", how="left")

nodes = nodes.drop(columns=["target", "source"], errors="ignore")

nodes["in_degree"] = nodes["in_degree"].fillna(0).astype(int)
nodes["out_degree"] = nodes["out_degree"].fillna(0).astype(int)
nodes["total_degree"] = nodes["in_degree"] + nodes["out_degree"]

# Step 4: export
nodes.to_csv("paper_citation_nodes_2019_2024.csv", index=False)
edges.to_csv("paper_citation_edges_2019_2024.csv", index=False)

graph = {
    "nodes": nodes.to_dict(orient="records"),
    "links": edges.to_dict(orient="records")
}

with open("paper_citation_network_2019_2024.json", "w", encoding="utf-8") as f:
    json.dump(graph, f, ensure_ascii=False, indent=2)

print("Done.")
print("Final nodes:", len(nodes))
print("Final edges:", len(edges))