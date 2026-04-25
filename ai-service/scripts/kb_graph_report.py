import argparse
import os
from collections import defaultdict

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import networkx as nx
from neo4j import GraphDatabase
from pyvis.network import Network


ACTION_COLOR = {
    "view": "#1f77b4",  # blue
    "click": "#d62728",  # red
    "add_to_cart": "#2ca02c",  # green
    "purchase": "#ffcc00",  # yellow
    "search": "#ff7f0e",  # orange
    "wishlist": "#7f7f7f",  # gray
    "remove_from_cart": "#f7b6d2",  # light pink
    "rate": "#e377c2",  # magenta
    "unknown": "#999999",
}

USER_COLOR = "#8a2be2"  # purple
PRODUCT_COLOR = "#2ca02c"  # green


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate KB_Graph report (figures + markdown) from Neo4j")
    parser.add_argument("--out", default=os.path.join("reports", "kb_graph"), help="Output directory")
    parser.add_argument("--uri", default=os.environ.get("NEO4J_URI", "bolt://localhost:7687"))
    parser.add_argument("--user", default=os.environ.get("NEO4J_USER", "neo4j"))
    parser.add_argument("--password", default=os.environ.get("NEO4J_PASSWORD", "password"))
    parser.add_argument("--network-users", type=int, default=30, help="Users to include in network figure")
    parser.add_argument("--network-products", type=int, default=34, help="Products to include in network figure")
    parser.add_argument("--edge-limit", type=int, default=300, help="Max edges in network figure")
    return parser.parse_args()


def ensure_dirs(out_dir: str) -> dict:
    out_dir = os.path.abspath(out_dir)
    plots_dir = os.path.join(out_dir, "plots")
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(plots_dir, exist_ok=True)
    return {"out_dir": out_dir, "plots_dir": plots_dir}


def neo4j_driver(uri: str, user: str, password: str):
    return GraphDatabase.driver(uri, auth=(user, password))


def fetch_df(session, query: str, **params) -> pd.DataFrame:
    rows = session.run(query, **params).data()
    return pd.DataFrame(rows)


def compute_graph_stats(session) -> dict:
    counts = session.run(
        """
        MATCH (u:User) WITH count(u) AS users
        MATCH (p:Product) WITH users, count(p) AS products
        MATCH (:User)-[r:INTERACTS_WITH]->(:Product) WITH users, products, count(r) AS relationships
        RETURN users, products, relationships
        """
    ).single()

    return {
        "users": int(counts["users"]),
        "products": int(counts["products"]),
        "relationships": int(counts["relationships"]),
    }


def fetch_edge_matrix_top20(session) -> pd.DataFrame:
    df = fetch_df(
        session,
        """
        MATCH (u:User)-[r:INTERACTS_WITH]->(p:Product)
        RETURN
          u.id AS source_user,
          p.id AS target_product,
          r.weight AS weight,
          r.action AS edge_type,
          r.count AS count,
          r.last_ts AS last_ts
        ORDER BY r.weight DESC
        LIMIT 20
        """,
    )
    return df


def fetch_action_frequency(session) -> pd.DataFrame:
    df = fetch_df(
        session,
        """
        MATCH (:User)-[r:INTERACTS_WITH]->(:Product)
        RETURN r.action AS action, sum(r.count) AS total_count, sum(r.weight) AS total_weight
        ORDER BY total_count DESC
        """,
    )
    return df


def fetch_degree_distributions(session) -> tuple[pd.DataFrame, pd.DataFrame]:
    user_deg = fetch_df(
        session,
        """
        MATCH (u:User)-[:INTERACTS_WITH]->(p:Product)
        RETURN u.id AS user_id, count(DISTINCT p) AS product_out_degree
        """,
    )
    prod_deg = fetch_df(
        session,
        """
        MATCH (u:User)-[:INTERACTS_WITH]->(p:Product)
        RETURN p.id AS product_id, count(DISTINCT u) AS user_in_degree
        """,
    )
    return user_deg, prod_deg


def fetch_user_action_heatmap(session, top_n: int = 20) -> pd.DataFrame:
    df = fetch_df(
        session,
        """
        MATCH (u:User)-[r:INTERACTS_WITH]->(:Product)
        WITH u, sum(r.count) AS total_events
        ORDER BY total_events DESC
        LIMIT $top_n
        MATCH (u)-[r:INTERACTS_WITH]->(:Product)
        RETURN u.id AS user_id, r.action AS action, sum(r.count) AS action_events
        ORDER BY user_id, action
        """,
        top_n=top_n,
    )
    if df.empty:
        return df
    pivot = df.pivot_table(index="user_id", columns="action", values="action_events", fill_value=0, aggfunc="sum")
    pivot = pivot.sort_values(by=list(pivot.columns), ascending=False)
    return pivot


def fetch_network_subgraph(session, n_users: int, n_products: int, edge_limit: int) -> pd.DataFrame:
    # Pick most active users (by total events), then expand products they touched,
    # then cap products and edges for a readable visualization.
    df = fetch_df(
        session,
        """
        MATCH (u:User)-[r:INTERACTS_WITH]->(:Product)
        WITH u, sum(r.count) AS total_events
        ORDER BY total_events DESC, u.id ASC
        LIMIT $n_users
        MATCH (u)-[r:INTERACTS_WITH]->(p:Product)
        WITH u, p, sum(r.weight) AS weight, sum(r.count) AS count,
             collect(DISTINCT r.action) AS actions
        RETURN u.id AS user_id, p.id AS product_id,
               weight AS weight, count AS count,
               actions[0] AS action
        ORDER BY weight DESC
        LIMIT $edge_limit
        """,
        n_users=n_users,
        edge_limit=edge_limit,
    )
    if df.empty:
        return df

    # Keep top products by total weight inside this subgraph
    prod_scores = df.groupby("product_id")["weight"].sum().sort_values(ascending=False)
    keep_products = set(prod_scores.head(n_products).index.astype(str))
    df = df[df["product_id"].astype(str).isin(keep_products)].copy()
    return df


def build_bipartite_nx(df_edges: pd.DataFrame) -> nx.Graph:
    G = nx.Graph()
    for row in df_edges.to_dict(orient="records"):
        u = f"User_{row['user_id']}"
        p = f"Product_{row['product_id']}"
        action = (row.get("action") or "unknown").strip().lower()
        weight = float(row.get("weight") or 0.0)

        G.add_node(u, bipartite=0, node_type="user", label=str(row["user_id"]), color=USER_COLOR)
        G.add_node(p, bipartite=1, node_type="product", label=str(row["product_id"]), color=PRODUCT_COLOR)
        G.add_edge(u, p, action=action, weight=weight)
    return G


def render_network_png(G: nx.Graph, out_png: str) -> None:
    plt.figure(figsize=(14, 9), dpi=180)
    pos = nx.spring_layout(G, seed=42, k=0.7)

    user_nodes = [n for n, d in G.nodes(data=True) if d.get("node_type") == "user"]
    prod_nodes = [n for n, d in G.nodes(data=True) if d.get("node_type") == "product"]

    nx.draw_networkx_nodes(G, pos, nodelist=user_nodes, node_color=USER_COLOR, node_size=260, alpha=0.85)
    nx.draw_networkx_nodes(G, pos, nodelist=prod_nodes, node_color=PRODUCT_COLOR, node_size=260, alpha=0.85)

    weights = np.array([max(0.1, float(d.get("weight", 1.0))) for _, _, d in G.edges(data=True)])
    widths = np.clip(weights / (weights.max() if weights.max() else 1.0) * 4.0, 0.8, 4.5)
    edge_colors = [ACTION_COLOR.get(d.get("action", "unknown"), ACTION_COLOR["unknown"]) for _, _, d in G.edges(data=True)]
    nx.draw_networkx_edges(G, pos, width=widths, edge_color=edge_colors, alpha=0.7)

    plt.axis("off")
    plt.tight_layout()
    plt.savefig(out_png, bbox_inches="tight")
    plt.close()


def render_network_pyvis(G: nx.Graph, out_html: str) -> None:
    net = Network(height="780px", width="100%", bgcolor="#111111", font_color="white", notebook=False)
    net.force_atlas_2based(gravity=-50, central_gravity=0.01, spring_length=150, spring_strength=0.02, damping=0.4)

    for n, d in G.nodes(data=True):
        net.add_node(
            n,
            label=f"{d.get('node_type')} {d.get('label')}",
            color=d.get("color"),
            title=f"{d.get('node_type')} | id={d.get('label')}",
        )

    if G.number_of_edges() > 0:
        w_max = max(float(d.get("weight", 1.0)) for _, _, d in G.edges(data=True))
    else:
        w_max = 1.0

    for u, v, d in G.edges(data=True):
        w = float(d.get("weight", 1.0))
        width = float(np.clip((w / (w_max or 1.0)) * 10.0, 1.0, 12.0))
        action = d.get("action", "unknown")
        color = ACTION_COLOR.get(action, ACTION_COLOR["unknown"])
        net.add_edge(u, v, value=width, color=color, title=f"action={action}<br>weight={w:.2f}")

    # `show()` defaults to notebook mode on some environments and can fail with template issues.
    net.write_html(out_html, open_browser=False, notebook=False)


def plot_stats(user_deg: pd.DataFrame, prod_deg: pd.DataFrame, action_freq: pd.DataFrame, out_png: str) -> None:
    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(1, 3, figsize=(18, 5), dpi=180)

    axes[0].hist(user_deg["product_out_degree"], bins=20, color=USER_COLOR, alpha=0.85)
    axes[0].set_title("User Out-Degree (Distinct Products)")
    axes[0].set_xlabel("Distinct products per user")
    axes[0].set_ylabel("Users")

    axes[1].hist(prod_deg["user_in_degree"], bins=20, color=PRODUCT_COLOR, alpha=0.85)
    axes[1].set_title("Product In-Degree (Distinct Users)")
    axes[1].set_xlabel("Distinct users per product")
    axes[1].set_ylabel("Products")

    action_freq_sorted = action_freq.sort_values("total_count", ascending=False)
    axes[2].bar(action_freq_sorted["action"], action_freq_sorted["total_count"], color="#4c78a8", alpha=0.9)
    axes[2].set_title("Action Frequency (Sum of r.count)")
    axes[2].set_xlabel("Action")
    axes[2].set_ylabel("Total events")
    axes[2].tick_params(axis="x", rotation=45)

    plt.tight_layout()
    plt.savefig(out_png, bbox_inches="tight")
    plt.close(fig)


def plot_heatmap(pivot: pd.DataFrame, out_png: str) -> None:
    if pivot.empty:
        return
    sns.set_theme(style="white")
    plt.figure(figsize=(14, 8), dpi=180)
    sns.heatmap(pivot, cmap="YlOrBr", linewidths=0.3, linecolor="#222222")
    plt.title("User × Action Heatmap (Top 20 Users by total events)")
    plt.xlabel("Action")
    plt.ylabel("User")
    plt.tight_layout()
    plt.savefig(out_png, bbox_inches="tight")
    plt.close()


def md_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "_(No rows)_"
    cols = list(df.columns)
    lines = []
    lines.append("| " + " | ".join(cols) + " |")
    lines.append("| " + " | ".join(["---"] * len(cols)) + " |")
    for _, row in df.iterrows():
        vals = [str(row[c]) for c in cols]
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def write_report(out_dir: str, stats: dict, paths: dict, edge_top20: pd.DataFrame) -> None:
    report_path = os.path.join(out_dir, "KB_Graph_Report.md")

    edge_table_df = edge_top20[["source_user", "target_product", "weight", "edge_type"]].copy()
    edge_table_df["source_user"] = edge_table_df["source_user"].astype(str).apply(lambda x: f"User {x}")
    edge_table_df["target_product"] = edge_table_df["target_product"].astype(str).apply(lambda x: f"Product {x}")
    edge_table_df["weight"] = edge_table_df["weight"].astype(float).round(2)

    content = f"""\
## 4. Câu 2b — Knowledge Base Graph (KB_Graph)

### 4.1 Giải Thích Kiến Trúc KB Graph

KB_Graph mô hình hóa hệ thống E‑Commerce dưới dạng một **đồ thị tri thức (Knowledge Graph) bipartite**, gồm hai loại node `User` và `Product`, được liên kết bởi cạnh `INTERACTS_WITH` mang thông tin hành vi (`action`) và trọng số (`weight`) tương ứng với mức độ tương tác.

- **Node Users (tím)**: Đại diện cho khách hàng trong hệ thống (hiện có {stats['users']} users trong Neo4j).
- **Node Products (xanh lá)**: Đại diện cho sản phẩm trong catalog (hiện có {stats['products']} products trong Neo4j).
- **Edges (màu theo loại hành vi)**: `view`, `click`, `add_to_cart`, `purchase`, `search`, `wishlist`, `remove_from_cart`, `rate`.
- **Edge Weight**: Tổng điểm tương tác tích lũy theo thời gian (aggregate theo `(user_id, product_id, action)`), được dùng cho các thuật toán gợi ý (collaborative filtering / scoring).

**Schema Neo4j (production)**

- `(:User {{id}})`
- `(:Product {{id}})`
- `(u)-[:INTERACTS_WITH {{action, count, first_ts, last_ts, weight}}]->(p)`

### 4.2 Biểu Đồ KB Graph — User-Product Interaction Network

**Hình 5.1**: KB_Graph Network — {paths['network_users']} users × {paths['network_products']} products (subgraph) và các cạnh tương tác nổi bật. Độ dày cạnh phản ánh tổng `weight`.

- Static PNG: `plots/kb_graph_network.png`
- Interactive HTML: `kb_graph.html`

![KB_Graph Network](plots/kb_graph_network.png)

### 4.3 Thống Kê Topology Đồ Thị

**Hình 5.2**: KB_Graph Statistics — phân phối User Out‑Degree (distinct products), Product In‑Degree (distinct users), và Action Frequency (sum(r.count)).

![KB_Graph Statistics](plots/kb_graph_stats.png)

### 4.4 User × Action Heatmap (Top 20 Users)

**Hình 5.3**: Heatmap hành vi của 20 users hoạt động nhiều nhất. Màu vàng = cao nhất.

![User×Action Heatmap](plots/kb_graph_heatmap.png)

### 4.5 Dữ Liệu Mẫu 20 Cạnh (Edge Matrix)

Bảng 5.1: 20 cạnh mẫu từ KB_Graph (top theo `weight`).

{md_table(edge_table_df)}

### 4.6 Cypher Query Mẫu (Neo4j)

#### Tạo node và edge (theo API realtime)

```cypher
MERGE (u:User {{id: $user_id}})
MERGE (p:Product {{id: $product_id}})
MERGE (u)-[r:INTERACTS_WITH {{action: $action}}]->(p)
ON CREATE SET
  r.count = 1,
  r.first_ts = $event_ts,
  r.last_ts = $event_ts,
  r.weight = $action_weight
ON MATCH SET
  r.count = r.count + 1,
  r.last_ts = $event_ts,
  r.weight = r.weight + $action_weight;
```

#### Truy vấn sản phẩm tương tự (collaborative filtering theo shared users)

```cypher
MATCH (u:User)-[:INTERACTS_WITH]->(p:Product {{id: $product_id}})
MATCH (u)-[:INTERACTS_WITH]->(similar:Product)
WHERE similar.id <> $product_id
RETURN similar.id AS product_id, COUNT(DISTINCT u) AS shared_users
ORDER BY shared_users DESC
LIMIT 5;
```
"""

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(content)


def main():
    args = parse_args()
    dirs = ensure_dirs(args.out)
    out_dir = dirs["out_dir"]
    plots_dir = dirs["plots_dir"]

    with neo4j_driver(args.uri, args.user, args.password) as driver:
        with driver.session() as session:
            stats = compute_graph_stats(session)

            edge_top20 = fetch_edge_matrix_top20(session)
            edge_top20.to_csv(os.path.join(out_dir, "edge_matrix_top20.csv"), index=False, encoding="utf-8-sig")

            action_freq = fetch_action_frequency(session)
            user_deg, prod_deg = fetch_degree_distributions(session)
            pivot = fetch_user_action_heatmap(session, top_n=20)

            stats_png = os.path.join(plots_dir, "kb_graph_stats.png")
            plot_stats(user_deg, prod_deg, action_freq, stats_png)

            heat_png = os.path.join(plots_dir, "kb_graph_heatmap.png")
            plot_heatmap(pivot, heat_png)

            network_edges = fetch_network_subgraph(
                session, n_users=args.network_users, n_products=args.network_products, edge_limit=args.edge_limit
            )
            G = build_bipartite_nx(network_edges)

    network_png = os.path.join(plots_dir, "kb_graph_network.png")
    render_network_png(G, network_png)

    network_html = os.path.join(out_dir, "kb_graph.html")
    render_network_pyvis(G, network_html)

    write_report(
        out_dir,
        stats=stats,
        paths={"network_users": args.network_users, "network_products": args.network_products},
        edge_top20=edge_top20,
    )

    print("Report generated at:", os.path.join(out_dir, "KB_Graph_Report.md"))


if __name__ == "__main__":
    main()

