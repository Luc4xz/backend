import duckdb
import pandas as pd
import json

# ============================================================
# File paths
# ============================================================

selected_papers_path = r"F:\學術\UW-Madison\HCI research\FSU\uw_madison_cs_paper_ids.csv"
paperrefs_path = r"F:\學術\UW-Madison\HCI research\FSU\sciscinet_paperrefs.parquet"
papers_meta_path = r"F:\學術\UW-Madison\HCI research\FSU\sciscinet_papers.parquet"

# Past 10 years
# Change these if your dataset ends in a different year.
START_YEAR = 2016
END_YEAR = 2025

# Output files
nodes_output_csv = "paper_citation_nodes_10years.csv"
edges_output_csv = "paper_citation_edges_10years.csv"
json_output = "paper_citation_network_10years.json"


# ============================================================
# Step 1: Load selected UW–Madison CS paper IDs
# ============================================================

selected_df = pd.read_csv(selected_papers_path)

# Make sure your CSV column is named "paperid"
# If your column is named "paper_id", change this line.
selected_df["paperid"] = selected_df["paperid"].astype(str)

print(f"Selected papers from CSV: {len(selected_df)}")


# ============================================================
# Step 2: Connect to DuckDB
# ============================================================

con = duckdb.connect()
con.register("selected_papers", selected_df)


# ============================================================
# Step 3: Filter selected papers by year using sciscinet_papers.parquet
# ============================================================
# This step gives you the actual node details.
# We keep only selected UW–Madison CS papers from the past 10 years.

selected_papers_with_meta = con.execute(f"""
    SELECT
        p.paperid,
        p.year,
        p.citation_count,
        p.reference_count,
        p.patent_count,
        p.doctype,
        p.is_retracted,
        p.team_size,
        p.institution_count
    FROM read_parquet('{papers_meta_path}') p
    INNER JOIN selected_papers s
        ON p.paperid = s.paperid
    WHERE p.year BETWEEN {START_YEAR} AND {END_YEAR}
""").df()

selected_papers_with_meta["paperid"] = selected_papers_with_meta["paperid"].astype(str)

print(f"Selected papers after year filter: {len(selected_papers_with_meta)}")

con.register("selected_papers_10years", selected_papers_with_meta)


# ============================================================
# Step 4: Build citation edges from sciscinet_paperrefs.parquet
# ============================================================
# Internal citation network:
# source = citing paper
# target = cited paper
#
# Both source and target must be selected UW–Madison CS papers
# from the past 10 years.

edges = con.execute(f"""
    SELECT
        r.citing_paperid AS source,
        r.cited_paperid AS target,
        r.year,
        r.ref_year,
        r.year_diff
    FROM read_parquet('{paperrefs_path}') r
    INNER JOIN selected_papers_10years source_nodes
        ON r.citing_paperid = source_nodes.paperid
    INNER JOIN selected_papers_10years target_nodes
        ON r.cited_paperid = target_nodes.paperid
    WHERE r.year BETWEEN {START_YEAR} AND {END_YEAR}
""").df()

edges["source"] = edges["source"].astype(str)
edges["target"] = edges["target"].astype(str)
edges["type"] = "citation"

print(f"Citation edges: {len(edges)}")


# ============================================================
# Step 5: Build nodes with detailed information
# ============================================================
# Only keep papers that actually appear in the citation network.

node_ids = pd.DataFrame({
    "id": pd.unique(pd.concat([edges["source"], edges["target"]]))
})

con.register("node_ids", node_ids)

nodes = con.execute("""
    SELECT
        n.id,
        m.year,
        m.citation_count,
        m.reference_count,
        m.patent_count,
        m.doctype,
        m.is_retracted,
        m.team_size,
        m.institution_count
    FROM node_ids n
    LEFT JOIN selected_papers_10years m
        ON n.id = m.paperid
""").df()

print(f"Citation nodes: {len(nodes)}")


# ============================================================
# Step 6: Optional node statistics for visualization
# ============================================================
# in_degree = how many selected papers cite this paper
# out_degree = how many selected papers this paper cites

in_degree = edges.groupby("target").size().reset_index(name="in_degree")
out_degree = edges.groupby("source").size().reset_index(name="out_degree")

nodes = nodes.merge(in_degree, left_on="id", right_on="target", how="left")
nodes = nodes.merge(out_degree, left_on="id", right_on="source", how="left")

nodes = nodes.drop(columns=["target", "source"], errors="ignore")

nodes["in_degree"] = nodes["in_degree"].fillna(0).astype(int)
nodes["out_degree"] = nodes["out_degree"].fillna(0).astype(int)
nodes["total_degree"] = nodes["in_degree"] + nodes["out_degree"]


# ============================================================
# Step 7: Export CSV files
# ============================================================

nodes.to_csv(nodes_output_csv, index=False)
edges.to_csv(edges_output_csv, index=False)

print(f"Saved {nodes_output_csv}")
print(f"Saved {edges_output_csv}")


# ============================================================
# Step 8: Export D3-friendly JSON
# ============================================================

graph = {
    "nodes": nodes.to_dict(orient="records"),
    "links": edges.to_dict(orient="records")
}

with open(json_output, "w", encoding="utf-8") as f:
    json.dump(graph, f, ensure_ascii=False, indent=2)

print(f"Saved {json_output}")


# ============================================================
# Step 9: Quick preview
# ============================================================

print("\nNode preview:")
print(nodes.head())

print("\nEdge preview:")
print(edges.head())