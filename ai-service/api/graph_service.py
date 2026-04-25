"""
Câu 2b — Knowledge Base Graph Service

Collaborative Filtering, User Context for RAG, Visualization.
Model: (User)-[ACTION]->(Product) via NetworkX + Neo4j + pyvis
"""
from __future__ import annotations
import logging, os, tempfile
from typing import Any, Dict, List
import networkx as nx
from .neo4j_client import neo4j_client

logger = logging.getLogger(__name__)

ACTION_COLOR = {
    "view": "#1f77b4", "click": "#d62728", "add_to_cart": "#2ca02c",
    "purchase": "#ffcc00", "search": "#ff7f0e", "wishlist": "#7f7f7f",
    "remove_from_cart": "#f7b6d2", "rate": "#e377c2", "unknown": "#999999",
}
USER_COLOR = "#8a2be2"
PRODUCT_COLOR = "#2ca02c"


def get_similar_products(product_id: str, k: int = 5) -> List[Dict[str, Any]]:
    """Collaborative Filtering: similar products by shared users."""
    query = """
    MATCH (u:User)-[:INTERACTS_WITH]->(p:Product {id: $pid})
    MATCH (u)-[r:INTERACTS_WITH]->(similar:Product)
    WHERE similar.id <> $pid
    RETURN similar.id AS product_id, COUNT(DISTINCT u) AS shared_users,
           SUM(r.weight) AS total_weight
    ORDER BY shared_users DESC, total_weight DESC LIMIT $k
    """
    try:
        records = neo4j_client.execute_read(query, {"pid": str(product_id), "k": int(k)})
        return [{"product_id": str(r["product_id"]), "shared_users": int(r["shared_users"]),
                 "score": float(r.get("total_weight", 0))} for r in records]
    except Exception as e:
        logger.error("get_similar_products failed: %s", e)
        return []


def get_user_graph_context(user_id: str, limit: int = 10) -> Dict[str, Any]:
    """Full user context from KB Graph for RAG pipeline."""
    interactions = neo4j_client.execute_read(
        """MATCH (u:User {id: $uid})-[r:INTERACTS_WITH]->(p:Product)
        RETURN p.id AS product_id, r.action AS action, r.weight AS weight,
               r.count AS count ORDER BY r.weight DESC LIMIT $limit""",
        {"uid": str(user_id), "limit": int(limit)},
    )
    purchases = neo4j_client.execute_read(
        """MATCH (u:User {id: $uid})-[r:INTERACTS_WITH {action:'purchase'}]->(p:Product)
        RETURN p.id AS product_id, r.count AS times ORDER BY r.weight DESC LIMIT 10""",
        {"uid": str(user_id)},
    )
    action_summary = neo4j_client.execute_read(
        """MATCH (u:User {id: $uid})-[r:INTERACTS_WITH]->(:Product)
        RETURN r.action AS action, SUM(r.count) AS total_count ORDER BY total_count DESC""",
        {"uid": str(user_id)},
    )
    cf_recs = neo4j_client.execute_read(
        """MATCH (u:User {id: $uid})-[:INTERACTS_WITH]->(p:Product)<-[:INTERACTS_WITH]-(o:User)
        MATCH (o)-[r:INTERACTS_WITH]->(rec:Product) WHERE NOT (u)-[:INTERACTS_WITH]->(rec)
        RETURN rec.id AS product_id, COUNT(DISTINCT o) AS recommenders,
               SUM(r.weight) AS score ORDER BY recommenders DESC LIMIT 5""",
        {"uid": str(user_id)},
    )
    return {
        "interactions": [{"product_id": str(r.get("product_id","")), "action": str(r.get("action","")),
                          "weight": float(r.get("weight",0)), "count": int(r.get("count",0))} for r in interactions],
        "purchases": [{"product_id": str(r.get("product_id","")), "times": int(r.get("times",0))} for r in purchases],
        "action_summary": [{"action": str(r.get("action","")), "total_count": int(r.get("total_count",0))} for r in action_summary],
        "cf_recommendations": [{"product_id": str(r.get("product_id","")), "score": float(r.get("score",0))} for r in cf_recs],
    }


def build_user_subgraph(user_id: str, max_edges: int = 50) -> nx.Graph:
    """Build NetworkX graph for user interactions."""
    records = neo4j_client.execute_read(
        """MATCH (u:User {id: $uid})-[r:INTERACTS_WITH]->(p:Product)
        RETURN u.id AS user_id, p.id AS product_id, r.action AS action,
               r.weight AS weight ORDER BY r.weight DESC LIMIT $lim""",
        {"uid": str(user_id), "lim": int(max_edges)},
    )
    G = nx.Graph()
    for row in records:
        u_n = f"User_{row['user_id']}"
        p_n = f"Product_{row['product_id']}"
        G.add_node(u_n, node_type="user", label=str(row["user_id"]), color=USER_COLOR)
        G.add_node(p_n, node_type="product", label=str(row["product_id"]), color=PRODUCT_COLOR)
        G.add_edge(u_n, p_n, action=str(row.get("action","unknown")).lower(), weight=float(row.get("weight",1)))
    return G


def render_pyvis_html(user_id: str, max_edges: int = 50) -> str:
    """Render interactive HTML visualization via pyvis."""
    try:
        import numpy as np
        from pyvis.network import Network
    except ImportError:
        return "<p>pyvis not available</p>"

    G = build_user_subgraph(user_id, max_edges)
    if G.number_of_nodes() == 0:
        return "<p>No data found for this user.</p>"

    net = Network(height="600px", width="100%", bgcolor="#111111", font_color="white", notebook=False)
    net.force_atlas_2based(gravity=-50, central_gravity=0.01, spring_length=150, spring_strength=0.02, damping=0.4)
    for n, d in G.nodes(data=True):
        net.add_node(n, label=f"{d.get('node_type','')} {d.get('label','')}", color=d.get("color","#999"))
    w_max = max((float(d.get("weight",1)) for _,_,d in G.edges(data=True)), default=1.0)
    for u, v, d in G.edges(data=True):
        w = float(d.get("weight",1))
        action = d.get("action","unknown")
        color = ACTION_COLOR.get(action, ACTION_COLOR["unknown"])
        net.add_edge(u, v, value=max(1, w/w_max*10), color=color, title=f"{action} w={w:.1f}")

    tmp = tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8")
    try:
        net.write_html(tmp.name, open_browser=False, notebook=False)
        tmp.close()
        with open(tmp.name, "r", encoding="utf-8") as f:
            return f.read()
    finally:
        try: os.unlink(tmp.name)
        except OSError: pass
