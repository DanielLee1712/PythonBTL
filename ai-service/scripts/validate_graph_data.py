import argparse
import logging
import os

import pandas as pd
from neo4j import GraphDatabase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
AUTH = (
    os.environ.get("NEO4J_USER", "neo4j"),
    os.environ.get("NEO4J_PASSWORD", "password"),
)


def parse_args():
    parser = argparse.ArgumentParser(description="Validate KB graph data quality in Neo4j")
    parser.add_argument(
        "--csv",
        default=os.path.join(os.path.dirname(os.path.dirname(__file__)), "data_user500.csv"),
        help="Path to source CSV file used for comparison",
    )
    return parser.parse_args()


def expected_counts(csv_path):
    df = pd.read_csv(csv_path, sep=";", encoding="utf-8-sig")
    df["user_id"] = df["user_id"].astype(str).str.strip()
    df["product_id"] = df["product_id"].astype(str).str.strip()
    df["action"] = df["action"].astype(str).str.strip().str.lower()
    df["timestamp"] = pd.to_datetime(df["timestamp"], format="%d/%m/%Y %H:%M:%S", errors="coerce")
    df = df.dropna(subset=["user_id", "product_id", "action", "timestamp"])

    aggregate = df.groupby(["user_id", "product_id", "action"], as_index=False).size()
    return {
        "users": int(df["user_id"].nunique()),
        "products": int(df["product_id"].nunique()),
        "relationships": int(len(aggregate)),
        "interaction_rows": int(len(df)),
    }


def graph_counts(driver):
    with driver.session() as session:
        users = session.run("MATCH (u:User) RETURN count(u) AS c").single()["c"]
        products = session.run("MATCH (p:Product) RETURN count(p) AS c").single()["c"]
        relationships = session.run("MATCH (:User)-[r:INTERACTS_WITH]->(:Product) RETURN count(r) AS c").single()["c"]
        missing_props = session.run(
            """
            MATCH (:User)-[r:INTERACTS_WITH]->(:Product)
            WHERE r.action IS NULL OR r.count IS NULL OR r.first_ts IS NULL OR r.last_ts IS NULL OR r.weight IS NULL
            RETURN count(r) AS c
            """
        ).single()["c"]
        invalid_counts = session.run(
            "MATCH (:User)-[r:INTERACTS_WITH]->(:Product) WHERE r.count < 1 RETURN count(r) AS c"
        ).single()["c"]
        return {
            "users": int(users),
            "products": int(products),
            "relationships": int(relationships),
            "missing_properties": int(missing_props),
            "invalid_counts": int(invalid_counts),
        }


def print_top_actions(driver):
    with driver.session() as session:
        results = session.run(
            """
            MATCH (:User)-[r:INTERACTS_WITH]->(:Product)
            RETURN r.action AS action, sum(r.count) AS total_count, sum(r.weight) AS total_weight
            ORDER BY total_count DESC
            LIMIT 10
            """
        ).data()
    logger.info("Top actions by total_count: %s", results)


def main():
    args = parse_args()
    expected = expected_counts(args.csv)
    logger.info("Expected counts from CSV: %s", expected)

    driver = GraphDatabase.driver(URI, auth=AUTH)
    try:
        driver.verify_connectivity()
        actual = graph_counts(driver)
        logger.info("Actual counts from Neo4j: %s", actual)
        print_top_actions(driver)

        errors = []
        for key in ("users", "products", "relationships"):
            if expected[key] != actual[key]:
                errors.append(f"Mismatch for {key}: expected={expected[key]}, actual={actual[key]}")
        if actual["missing_properties"] > 0:
            errors.append(f"Relationships missing required properties: {actual['missing_properties']}")
        if actual["invalid_counts"] > 0:
            errors.append(f"Relationships with invalid count<1: {actual['invalid_counts']}")

        if errors:
            for err in errors:
                logger.error(err)
            raise SystemExit(1)

        logger.info("Validation passed.")
    finally:
        driver.close()


if __name__ == "__main__":
    main()
