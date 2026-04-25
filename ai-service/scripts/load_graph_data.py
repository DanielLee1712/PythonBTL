import argparse
import logging
import os
import sys

import pandas as pd
from neo4j import GraphDatabase

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api.kb_graph import action_weight, clean_identifier, normalize_action, parse_timestamp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
AUTH = (
    os.environ.get("NEO4J_USER", "neo4j"),
    os.environ.get("NEO4J_PASSWORD", "password"),
)

REQUIRED_COLUMNS = {"user_id", "product_id", "action", "timestamp"}


def create_schema(session):
    def drop_conflicting_node_indexes(label: str, prop: str) -> None:
        # On some Neo4j setups, a pre-existing non-unique index on (:Label {prop})
        # can block creating a uniqueness constraint. For reset/reload workflows we
        # drop such indexes if present.
        indexes = session.run(
            """
            SHOW INDEXES
            YIELD name, labelsOrTypes, properties, owningConstraint
            WHERE labelsOrTypes = [$label] AND properties = [$prop] AND owningConstraint IS NULL
            RETURN name
            """,
            label=label,
            prop=prop,
        ).data()
        for row in indexes:
            session.run(f"DROP INDEX {row['name']} IF EXISTS")

    drop_conflicting_node_indexes("User", "id")
    drop_conflicting_node_indexes("Product", "id")

    session.run("CREATE CONSTRAINT user_id_unique IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE")
    session.run("CREATE CONSTRAINT product_id_unique IF NOT EXISTS FOR (p:Product) REQUIRE p.id IS UNIQUE")
    session.run("CREATE INDEX interaction_action IF NOT EXISTS FOR ()-[r:INTERACTS_WITH]-() ON (r.action)")
    session.run("CREATE INDEX interaction_last_ts IF NOT EXISTS FOR ()-[r:INTERACTS_WITH]-() ON (r.last_ts)")


def normalize_dataframe(df):
    missing_columns = REQUIRED_COLUMNS - set(df.columns)
    if missing_columns:
        raise ValueError(f"Missing required columns: {sorted(missing_columns)}")

    normalized_rows = []
    for row in df.to_dict(orient="records"):
        user_id = clean_identifier(row.get("user_id"))
        product_id = clean_identifier(row.get("product_id"))
        action = normalize_action(row.get("action"))
        if not user_id or not product_id or not action:
            continue
        try:
            timestamp = parse_timestamp(row.get("timestamp"))
        except ValueError:
            continue

        normalized_rows.append(
            {
                "user_id": user_id,
                "product_id": product_id,
                "action": action,
                "timestamp_dt": timestamp,
            }
        )

    normalized_df = pd.DataFrame(normalized_rows)
    if normalized_df.empty:
        raise ValueError("No valid rows after cleaning input data")
    return normalized_df


def build_aggregates(df):
    grouped = (
        df.groupby(["user_id", "product_id", "action"], as_index=False)
        .agg(count=("timestamp_dt", "size"), first_ts=("timestamp_dt", "min"), last_ts=("timestamp_dt", "max"))
        .sort_values(["user_id", "product_id", "action"])
    )
    grouped["base_weight"] = grouped["action"].map(action_weight).astype(float)
    grouped["weight"] = grouped["base_weight"] * grouped["count"]
    grouped["first_ts"] = grouped["first_ts"].dt.strftime("%Y-%m-%dT%H:%M:%S")
    grouped["last_ts"] = grouped["last_ts"].dt.strftime("%Y-%m-%dT%H:%M:%S")
    return grouped


def load_data(driver, csv_path, reset=False):
    logger.info("Loading data from CSV: %s", csv_path)
    df = pd.read_csv(csv_path, sep=";", encoding="utf-8-sig")
    logger.info("Raw interactions: %s", len(df))

    normalized_df = normalize_dataframe(df)
    aggregates = build_aggregates(normalized_df)
    logger.info("Aggregated relationships: %s", len(aggregates))

    with driver.session() as session:
        if reset:
            logger.warning("Reset enabled: deleting existing graph data")
            session.run("MATCH (n) DETACH DELETE n")

        create_schema(session)
        logger.info("Schema constraints and indexes are ready")

        query = """
        UNWIND $rows AS row
        MERGE (u:User {id: row.user_id})
        MERGE (p:Product {id: row.product_id})
        MERGE (u)-[r:INTERACTS_WITH {action: row.action}]->(p)
        SET r.count = row.count,
            r.first_ts = row.first_ts,
            r.last_ts = row.last_ts,
            r.weight = row.weight
        """
        payload = aggregates.to_dict(orient="records")
        session.execute_write(lambda tx: tx.run(query, rows=payload).consume())

    return {
        "raw_interactions": int(len(df)),
        "valid_interactions": int(len(normalized_df)),
        "invalid_interactions": int(len(df) - len(normalized_df)),
        "relationships_loaded": int(len(aggregates)),
        "unique_users": int(normalized_df["user_id"].nunique()),
        "unique_products": int(normalized_df["product_id"].nunique()),
    }


def parse_args():
    parser = argparse.ArgumentParser(description="Load aggregated KB graph data into Neo4j")
    parser.add_argument(
        "--csv",
        default=os.path.join(os.path.dirname(os.path.dirname(__file__)), "data_user500.csv"),
        help="Path to source CSV file",
    )
    parser.add_argument("--reset", action="store_true", help="Delete all graph data before loading")
    return parser.parse_args()


def main():
    args = parse_args()
    driver = GraphDatabase.driver(URI, auth=AUTH)
    try:
        driver.verify_connectivity()
        logger.info("Connected to Neo4j successfully")
        summary = load_data(driver, args.csv, reset=args.reset)
        logger.info("Load summary: %s", summary)
    except Exception as exc:
        logger.error("Failed to load graph data: %s", exc)
        raise
    finally:
        driver.close()


if __name__ == "__main__":
    main()
