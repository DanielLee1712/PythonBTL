import argparse
import json
import logging
import os
import sys
from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from neo4j import GraphDatabase

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api.kb_graph import normalize_action  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


DEFAULT_ACTIONS = [
    "view",
    "click",
    "search",
    "wishlist",
    "add_to_cart",
    "remove_from_cart",
    "rate",
    "purchase",
]


@dataclass
class Interaction:
    user_id: str
    product_id: str
    action: str
    ts: str


def load_interactions_from_csv(csv_path: str) -> List[Interaction]:
    df = pd.read_csv(csv_path, sep=";", encoding="utf-8-sig")
    required = {"user_id", "product_id", "action", "timestamp"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"CSV missing columns: {sorted(missing)}")

    df["user_id"] = df["user_id"].astype(str).str.strip()
    df["product_id"] = df["product_id"].astype(str).str.strip()
    df["action"] = df["action"].astype(str).map(lambda x: normalize_action(x))
    df["timestamp"] = pd.to_datetime(df["timestamp"], format="%d/%m/%Y %H:%M:%S", errors="coerce")
    df = df.dropna(subset=["user_id", "product_id", "action", "timestamp"])
    df = df.sort_values(["user_id", "timestamp"], ascending=[True, True])

    interactions: List[Interaction] = []
    for row in df.to_dict(orient="records"):
        interactions.append(
            Interaction(
                user_id=str(row["user_id"]),
                product_id=str(row["product_id"]),
                action=str(row["action"]),
                ts=row["timestamp"].strftime("%Y-%m-%dT%H:%M:%S"),
            )
        )
    return interactions


def load_interactions_from_neo4j(limit_per_user: int | None = None) -> List[Interaction]:
    uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
    user = os.environ.get("NEO4J_USER", "neo4j")
    password = os.environ.get("NEO4J_PASSWORD", "password")

    driver = GraphDatabase.driver(uri, auth=(user, password))
    try:
        driver.verify_connectivity()
        with driver.session() as session:
            query = """
            MATCH (u:User)-[r:INTERACTS_WITH]->(p:Product)
            WHERE r.last_ts IS NOT NULL AND r.action IS NOT NULL
            RETURN u.id AS user_id, p.id AS product_id, r.action AS action, r.last_ts AS ts
            ORDER BY user_id ASC, ts ASC
            """
            rows = session.run(query).data()

        interactions: List[Interaction] = []
        current_user = None
        per_user_count = 0
        for row in rows:
            user_id = str(row["user_id"])
            if current_user != user_id:
                current_user = user_id
                per_user_count = 0
            if limit_per_user is not None and per_user_count >= limit_per_user:
                continue
            interactions.append(
                Interaction(
                    user_id=user_id,
                    product_id=str(row["product_id"]),
                    action=normalize_action(row["action"]),
                    ts=str(row["ts"]),
                )
            )
            per_user_count += 1
        return interactions
    finally:
        driver.close()


def build_vocabs(interactions: Iterable[Interaction], actions: List[str]) -> Tuple[Dict[str, int], Dict[str, int]]:
    product_ids = sorted({it.product_id for it in interactions})
    product_to_idx = {"<PAD>": 0, "<UNK>": 1}
    for pid in product_ids:
        product_to_idx[pid] = len(product_to_idx)

    action_to_idx = {"<PAD>": 0, "<UNK>": 1}
    for a in actions:
        action_to_idx[a] = len(action_to_idx)
    return product_to_idx, action_to_idx


def interactions_to_user_sequences(
    interactions: List[Interaction],
) -> Dict[str, List[Tuple[str, str]]]:
    sequences: Dict[str, List[Tuple[str, str]]] = {}
    for it in interactions:
        sequences.setdefault(it.user_id, []).append((it.product_id, it.action))
    return sequences


def make_training_windows(
    sequences: Dict[str, List[Tuple[str, str]]],
    product_to_idx: Dict[str, int],
    action_to_idx: Dict[str, int],
    window: int,
    min_events: int,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    x_products: List[List[int]] = []
    x_actions: List[List[int]] = []
    y_next: List[int] = []

    for _, events in sequences.items():
        if len(events) < max(min_events, window + 1):
            continue
        p_idx = [product_to_idx.get(pid, product_to_idx["<UNK>"]) for pid, _ in events]
        a_idx = [action_to_idx.get(act, action_to_idx["<UNK>"]) for _, act in events]
        for t in range(window, len(events)):
            x_products.append(p_idx[t - window : t])
            x_actions.append(a_idx[t - window : t])
            y_next.append(p_idx[t])

    if not x_products:
        raise ValueError("Not enough sequence data to build training windows. Add more interactions first.")

    return (
        np.array(x_products, dtype=np.int64),
        np.array(x_actions, dtype=np.int64),
        np.array(y_next, dtype=np.int64),
    )


class NextItemGRU(nn.Module):
    def __init__(self, n_products: int, n_actions: int, emb_dim: int = 64, hidden: int = 128):
        super().__init__()
        self.product_emb = nn.Embedding(n_products, emb_dim, padding_idx=0)
        self.action_emb = nn.Embedding(n_actions, emb_dim // 2, padding_idx=0)
        self.gru = nn.GRU(input_size=emb_dim + emb_dim // 2, hidden_size=hidden, batch_first=True)
        self.head = nn.Linear(hidden, n_products)

    def forward(self, product_seq: torch.Tensor, action_seq: torch.Tensor) -> torch.Tensor:
        p = self.product_emb(product_seq)
        a = self.action_emb(action_seq)
        x = torch.cat([p, a], dim=-1)
        out, _ = self.gru(x)
        last = out[:, -1, :]
        return self.head(last)


def train(
    x_p: np.ndarray,
    x_a: np.ndarray,
    y: np.ndarray,
    n_products: int,
    n_actions: int,
    epochs: int,
    batch_size: int,
    lr: float,
) -> NextItemGRU:
    device = torch.device("cpu")
    model = NextItemGRU(n_products=n_products, n_actions=n_actions).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    loss_fn = nn.CrossEntropyLoss()

    x_p_t = torch.from_numpy(x_p).to(device)
    x_a_t = torch.from_numpy(x_a).to(device)
    y_t = torch.from_numpy(y).to(device)

    n = x_p.shape[0]
    indices = np.arange(n)

    for ep in range(1, epochs + 1):
        np.random.shuffle(indices)
        model.train()
        total = 0.0
        for start in range(0, n, batch_size):
            batch_idx = indices[start : start + batch_size]
            logits = model(x_p_t[batch_idx], x_a_t[batch_idx])
            loss = loss_fn(logits, y_t[batch_idx])
            opt.zero_grad()
            loss.backward()
            opt.step()
            total += float(loss.item()) * len(batch_idx)
        logger.info("Epoch %s/%s | loss=%.4f", ep, epochs, total / n)

    return model


def parse_args():
    p = argparse.ArgumentParser(description="Train next-item GRU sequence model (CPU)")
    p.add_argument("--source", choices=["neo4j", "csv"], default="neo4j")
    p.add_argument("--csv", default=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data_user500.csv"))
    p.add_argument("--limit-per-user", type=int, default=50, help="Only for neo4j source. Limit last_ts events per user.")
    p.add_argument("--window", type=int, default=8)
    p.add_argument("--min-events", type=int, default=10)
    p.add_argument("--epochs", type=int, default=6)
    p.add_argument("--batch-size", type=int, default=256)
    p.add_argument("--lr", type=float, default=1e-3)
    p.add_argument("--out", default=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models", "sequence"))
    return p.parse_args()


def main():
    args = parse_args()
    if args.source == "csv":
        logger.info("Loading interactions from CSV: %s", args.csv)
        interactions = load_interactions_from_csv(args.csv)
    else:
        logger.info("Loading interactions from Neo4j (using r.last_ts order)")
        interactions = load_interactions_from_neo4j(limit_per_user=args.limit_per_user)

    logger.info("Interactions loaded: %s", len(interactions))
    product_to_idx, action_to_idx = build_vocabs(interactions, DEFAULT_ACTIONS)
    sequences = interactions_to_user_sequences(interactions)

    x_p, x_a, y = make_training_windows(
        sequences=sequences,
        product_to_idx=product_to_idx,
        action_to_idx=action_to_idx,
        window=args.window,
        min_events=args.min_events,
    )
    logger.info("Training samples: %s", x_p.shape[0])

    model = train(
        x_p=x_p,
        x_a=x_a,
        y=y,
        n_products=len(product_to_idx),
        n_actions=len(action_to_idx),
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
    )

    out_dir = args.out
    os.makedirs(out_dir, exist_ok=True)
    torch.save(model.state_dict(), os.path.join(out_dir, "sequence_gru.pt"))
    with open(os.path.join(out_dir, "product_vocab.json"), "w", encoding="utf-8") as f:
        json.dump(product_to_idx, f, ensure_ascii=False)
    with open(os.path.join(out_dir, "action_vocab.json"), "w", encoding="utf-8") as f:
        json.dump(action_to_idx, f, ensure_ascii=False)
    meta = {
        "model": "NextItemGRU",
        "window": int(args.window),
        "n_products": int(len(product_to_idx)),
        "n_actions": int(len(action_to_idx)),
    }
    with open(os.path.join(out_dir, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    logger.info("Saved sequence model assets to %s", out_dir)


if __name__ == "__main__":
    main()

