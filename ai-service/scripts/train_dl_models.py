"""
Câu 2a — Train PyTorch DL Models: RNN, LSTM, BiLSTM

Architecture: Embedding Layer → Recurrent Layer → Fully Connected Layer
Data source: data_user500.csv or Neo4j
Output: models/dl/{rnn,lstm,bilstm}.pt + vocab + meta
"""
import argparse, json, logging, os, sys
from typing import Dict, List, Tuple
import numpy as np, pandas as pd, torch, torch.nn as nn
from neo4j import GraphDatabase

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api.kb_graph import normalize_action
from api.dl_models import build_model, MODEL_REGISTRY

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

DEFAULT_ACTIONS = ["view","click","search","wishlist","add_to_cart","remove_from_cart","rate","purchase"]


def load_from_csv(csv_path: str):
    df = pd.read_csv(csv_path, sep=";", encoding="utf-8-sig")
    df["user_id"] = df["user_id"].astype(str).str.strip()
    df["product_id"] = df["product_id"].astype(str).str.strip()
    df["action"] = df["action"].astype(str).map(normalize_action)
    df["timestamp"] = pd.to_datetime(df["timestamp"], format="%d/%m/%Y %H:%M:%S", errors="coerce")
    df = df.dropna(subset=["user_id","product_id","action","timestamp"])
    df = df.sort_values(["user_id","timestamp"])
    return [(str(r["user_id"]), str(r["product_id"]), str(r["action"])) for r in df.to_dict("records")]


def load_from_neo4j():
    uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
    driver = GraphDatabase.driver(uri, auth=(
        os.environ.get("NEO4J_USER","neo4j"), os.environ.get("NEO4J_PASSWORD","password")))
    try:
        driver.verify_connectivity()
        with driver.session() as session:
            rows = session.run("""
                MATCH (u:User)-[r:INTERACTS_WITH]->(p:Product)
                WHERE r.last_ts IS NOT NULL AND r.action IS NOT NULL
                RETURN u.id AS uid, p.id AS pid, r.action AS action, r.last_ts AS ts
                ORDER BY uid, ts
            """).data()
        return [(str(r["uid"]), str(r["pid"]), normalize_action(r["action"])) for r in rows]
    finally:
        driver.close()


def build_vocabs(interactions, actions):
    pids = sorted({it[1] for it in interactions})
    p2i = {"<PAD>": 0, "<UNK>": 1}
    for p in pids: p2i[p] = len(p2i)
    a2i = {"<PAD>": 0, "<UNK>": 1}
    for a in actions: a2i[a] = len(a2i)
    return p2i, a2i


def make_windows(interactions, p2i, a2i, window, min_events):
    sequences: Dict[str, List[Tuple[str,str]]] = {}
    for uid, pid, act in interactions:
        sequences.setdefault(uid, []).append((pid, act))

    xp, xa, ys = [], [], []
    for events in sequences.values():
        if len(events) < max(min_events, window + 1):
            continue
        pi = [p2i.get(p, p2i["<UNK>"]) for p, _ in events]
        ai = [a2i.get(a, a2i["<UNK>"]) for _, a in events]
        for t in range(window, len(events)):
            xp.append(pi[t-window:t])
            xa.append(ai[t-window:t])
            ys.append(pi[t])

    if not xp:
        raise ValueError("Not enough data for training windows.")
    return np.array(xp, dtype=np.int64), np.array(xa, dtype=np.int64), np.array(ys, dtype=np.int64)


def train_model(model, xp, xa, y, epochs, batch_size, lr):
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    loss_fn = nn.CrossEntropyLoss()
    xp_t, xa_t, y_t = torch.from_numpy(xp), torch.from_numpy(xa), torch.from_numpy(y)
    n = xp.shape[0]
    indices = np.arange(n)

    for ep in range(1, epochs + 1):
        np.random.shuffle(indices)
        model.train()
        total = 0.0
        for start in range(0, n, batch_size):
            bi = indices[start:start+batch_size]
            logits = model(xp_t[bi], xa_t[bi])
            loss = loss_fn(logits, y_t[bi])
            opt.zero_grad(); loss.backward(); opt.step()
            total += float(loss.item()) * len(bi)
        logger.info("Epoch %d/%d | loss=%.4f", ep, epochs, total / n)
    return model


def parse_args():
    p = argparse.ArgumentParser(description="Train PyTorch RNN/LSTM/BiLSTM models")
    p.add_argument("--source", choices=["csv","neo4j"], default="csv")
    p.add_argument("--csv", default=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data_user500.csv"))
    p.add_argument("--window", type=int, default=8)
    p.add_argument("--min-events", type=int, default=10)
    p.add_argument("--epochs", type=int, default=10)
    p.add_argument("--batch-size", type=int, default=256)
    p.add_argument("--lr", type=float, default=1e-3)
    p.add_argument("--out", default=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models", "dl"))
    p.add_argument("--models", nargs="+", default=list(MODEL_REGISTRY.keys()), help="Models to train")
    return p.parse_args()


def main():
    args = parse_args()
    if args.source == "csv":
        logger.info("Loading from CSV: %s", args.csv)
        interactions = load_from_csv(args.csv)
    else:
        logger.info("Loading from Neo4j")
        interactions = load_from_neo4j()

    logger.info("Total interactions: %d", len(interactions))
    p2i, a2i = build_vocabs(interactions, DEFAULT_ACTIONS)
    xp, xa, y = make_windows(interactions, p2i, a2i, args.window, args.min_events)
    logger.info("Training samples: %d", xp.shape[0])

    os.makedirs(args.out, exist_ok=True)
    n_products, n_actions = len(p2i), len(a2i)

    for model_type in args.models:
        logger.info("Training %s...", model_type.upper())
        model = build_model(model_type, n_products=n_products, n_actions=n_actions)
        model = train_model(model, xp, xa, y, args.epochs, args.batch_size, args.lr)
        model.eval()
        torch.save(model.state_dict(), os.path.join(args.out, f"{model_type}.pt"))
        logger.info("Saved %s.pt", model_type)

    # Save vocabs and metadata
    with open(os.path.join(args.out, "product_vocab.json"), "w", encoding="utf-8") as f:
        json.dump(p2i, f, ensure_ascii=False)
    with open(os.path.join(args.out, "action_vocab.json"), "w", encoding="utf-8") as f:
        json.dump(a2i, f, ensure_ascii=False)
    meta = {"window": args.window, "n_products": n_products, "n_actions": n_actions,
            "models": args.models, "source": args.source}
    with open(os.path.join(args.out, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    logger.info("All models saved to %s", args.out)


if __name__ == "__main__":
    main()
