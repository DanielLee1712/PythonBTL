"""
Câu 2a — Train & Evaluate Deep Learning Classification Models
==============================================================
Pipeline: data_user500.csv → sliding-window → 8-class action classification
Models : BehaviorRNN, BehaviorLSTM, BehaviorBiLSTM (from api.dl_models)

Outputs
-------
  models/dl/rnn_classification.pt, lstm_classification.pt, bilstm_classification.pt
  models/dl/model_best.pt
  reports/deep_learning/metrics.json
  reports/deep_learning/learning_curves.png
  reports/deep_learning/metrics_comparison.png
  reports/deep_learning/confusion_matrices.png
  reports/deep_learning/radar_chart.png

Usage
-----
  python scripts/train_eval_classification.py --source csv --epochs 30
"""
from __future__ import annotations

import argparse
import copy
import json
import logging
import os
import shutil
import sys
from typing import Dict, List, Tuple

import matplotlib
matplotlib.use("Agg")  # non-interactive backend

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import torch
import torch.nn as nn
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

# ---------------------------------------------------------------------------
# Resolve project root so we can import from api.*
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICE_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, SERVICE_DIR)

from api.dl_models import build_model, MODEL_REGISTRY  # noqa: E402
from api.kb_graph import normalize_action  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
)
logger = logging.getLogger(__name__)

# 8 canonical action classes (same order used everywhere)
ACTION_LABELS: List[str] = [
    "view",
    "click",
    "search",
    "wishlist",
    "add_to_cart",
    "remove_from_cart",
    "rate",
    "purchase",
]

SEED = 42


# ===================================================================
# 1. Data loading
# ===================================================================

def load_interactions_csv(csv_path: str) -> pd.DataFrame:
    """Return a DataFrame with columns [user_id, product_id, action, timestamp]."""
    df = pd.read_csv(csv_path, sep=";", encoding="utf-8-sig")
    df["user_id"] = df["user_id"].astype(str).str.strip()
    df["product_id"] = df["product_id"].astype(str).str.strip()
    df["action"] = df["action"].astype(str).map(normalize_action)
    df["timestamp"] = pd.to_datetime(
        df["timestamp"], format="%d/%m/%Y %H:%M", errors="coerce"
    )
    df = df.dropna(subset=["user_id", "product_id", "action", "timestamp"])
    df = df.sort_values(["user_id", "timestamp"]).reset_index(drop=True)
    return df


# ===================================================================
# 2. Vocab & windowing
# ===================================================================

def build_vocabs(
    df: pd.DataFrame, actions: List[str]
) -> Tuple[Dict[str, int], Dict[str, int]]:
    pids = sorted(df["product_id"].unique())
    p2i: Dict[str, int] = {"<PAD>": 0, "<UNK>": 1}
    for p in pids:
        p2i[p] = len(p2i)

    a2i: Dict[str, int] = {"<PAD>": 0, "<UNK>": 1}
    for a in actions:
        a2i[a] = len(a2i)
    return p2i, a2i


def make_classification_windows(
    df: pd.DataFrame,
    p2i: Dict[str, int],
    a2i: Dict[str, int],
    window: int,
    min_events: int,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, List[str]]:
    """
    Slide a window over each user's timeline.
    Input  = (product_ids[t-w : t], action_ids[t-w : t])
    Label  = action_id at position t  (index into ACTION_LABELS, 0-7)

    Returns (xp, xa, y, user_ids_per_sample)
    """
    xp_list: List[List[int]] = []
    xa_list: List[List[int]] = []
    y_list: List[int] = []
    uid_list: List[str] = []

    for uid, grp in df.groupby("user_id", sort=False):
        events = list(zip(grp["product_id"], grp["action"]))
        if len(events) < max(min_events, window + 1):
            continue
        pi = [p2i.get(p, p2i["<UNK>"]) for p, _ in events]
        ai = [a2i.get(a, a2i["<UNK>"]) for _, a in events]
        for t in range(window, len(events)):
            xp_list.append(pi[t - window : t])
            xa_list.append(ai[t - window : t])
            # label = action index (0-based into ACTION_LABELS)
            action_str = events[t][1]
            label_idx = a2i.get(action_str, a2i["<UNK>"]) - 2  # offset <PAD>=0, <UNK>=1
            label_idx = max(label_idx, 0)
            y_list.append(label_idx)
            uid_list.append(str(uid))

    return (
        np.array(xp_list, dtype=np.int64),
        np.array(xa_list, dtype=np.int64),
        np.array(y_list, dtype=np.int64),
        uid_list,
    )


# ===================================================================
# 3. User-based split
# ===================================================================

def split_by_user(
    xp: np.ndarray,
    xa: np.ndarray,
    y: np.ndarray,
    uids: List[str],
    train_ratio: float = 0.8,
    val_ratio: float = 0.1,
) -> dict:
    """Split samples by user to avoid data leakage."""
    rng = np.random.RandomState(SEED)
    unique_users = sorted(set(uids))
    rng.shuffle(unique_users)

    n = len(unique_users)
    n_train = int(n * train_ratio)
    n_val = int(n * val_ratio)

    train_users = set(unique_users[:n_train])
    val_users = set(unique_users[n_train : n_train + n_val])
    test_users = set(unique_users[n_train + n_val :])

    uid_arr = np.array(uids)
    train_mask = np.isin(uid_arr, list(train_users))
    val_mask = np.isin(uid_arr, list(val_users))
    test_mask = np.isin(uid_arr, list(test_users))

    return {
        "train": (xp[train_mask], xa[train_mask], y[train_mask]),
        "val": (xp[val_mask], xa[val_mask], y[val_mask]),
        "test": (xp[test_mask], xa[test_mask], y[test_mask]),
        "n_users": {"train": len(train_users), "val": len(val_users), "test": len(test_users)},
    }


# ===================================================================
# 4. Training loop
# ===================================================================

def _run_epoch(model, xp_t, xa_t, y_t, indices, batch_size, loss_fn, optimizer=None):
    """One pass over the data. If optimizer is None ⇒ eval mode."""
    is_train = optimizer is not None
    model.train() if is_train else model.eval()

    total_loss = 0.0
    correct = 0
    total = 0

    with torch.set_grad_enabled(is_train):
        for start in range(0, len(indices), batch_size):
            bi = indices[start : start + batch_size]
            logits = model(xp_t[bi], xa_t[bi])
            loss = loss_fn(logits, y_t[bi])
            if is_train:
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
            total_loss += loss.item() * len(bi)
            preds = logits.argmax(dim=-1)
            correct += (preds == y_t[bi]).sum().item()
            total += len(bi)

    return total_loss / max(total, 1), correct / max(total, 1)


def train_and_evaluate(
    model_type: str,
    splits: dict,
    n_products: int,
    n_actions: int,
    n_classes: int,
    epochs: int,
    batch_size: int,
    lr: float,
) -> dict:
    """Train one model, return history + test metrics."""
    model = build_model(
        model_type,
        n_products=n_products,
        n_actions=n_actions,
        n_classes=n_classes,
        task="classification",
    )
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    loss_fn = nn.CrossEntropyLoss()

    # Tensors
    tr_xp, tr_xa, tr_y = [torch.from_numpy(a) for a in splits["train"]]
    va_xp, va_xa, va_y = [torch.from_numpy(a) for a in splits["val"]]

    n_train = tr_xp.shape[0]
    n_val = va_xp.shape[0]
    train_idx = np.arange(n_train)
    val_idx = np.arange(n_val)

    history = {"train_loss": [], "train_acc": [], "val_loss": [], "val_acc": []}
    best_val_f1 = -1.0
    best_state = None

    for ep in range(1, epochs + 1):
        np.random.shuffle(train_idx)
        tr_loss, tr_acc = _run_epoch(
            model, tr_xp, tr_xa, tr_y, train_idx, batch_size, loss_fn, optimizer
        )
        va_loss, va_acc = _run_epoch(
            model, va_xp, va_xa, va_y, val_idx, batch_size, loss_fn, None
        )
        history["train_loss"].append(tr_loss)
        history["train_acc"].append(tr_acc)
        history["val_loss"].append(va_loss)
        history["val_acc"].append(va_acc)

        # Track best by val F1
        model.eval()
        with torch.no_grad():
            va_preds = model(va_xp, va_xa).argmax(dim=-1).numpy()
        va_f1 = f1_score(va_y.numpy(), va_preds, average="macro", zero_division=0)
        if va_f1 > best_val_f1:
            best_val_f1 = va_f1
            best_state = copy.deepcopy(model.state_dict())

        logger.info(
            "[%s] Epoch %2d/%d  train_loss=%.4f  train_acc=%.4f  val_loss=%.4f  val_acc=%.4f  val_f1=%.4f",
            model_type.upper(), ep, epochs, tr_loss, tr_acc, va_loss, va_acc, va_f1,
        )

    # Restore best checkpoint
    if best_state is not None:
        model.load_state_dict(best_state)

    # Test evaluation
    te_xp, te_xa, te_y = [torch.from_numpy(a) for a in splits["test"]]
    model.eval()
    with torch.no_grad():
        te_preds = model(te_xp, te_xa).argmax(dim=-1).numpy()
    te_y_np = te_y.numpy()

    metrics = {
        "accuracy": float(accuracy_score(te_y_np, te_preds)),
        "f1_score": float(f1_score(te_y_np, te_preds, average="macro", zero_division=0)),
        "precision": float(precision_score(te_y_np, te_preds, average="macro", zero_division=0)),
        "recall": float(recall_score(te_y_np, te_preds, average="macro", zero_division=0)),
    }
    cm = confusion_matrix(te_y_np, te_preds, labels=list(range(n_classes)))

    logger.info(
        "[%s] TEST  acc=%.4f  f1=%.4f  prec=%.4f  rec=%.4f",
        model_type.upper(), metrics["accuracy"], metrics["f1_score"],
        metrics["precision"], metrics["recall"],
    )

    return {
        "model": model,
        "history": history,
        "metrics": metrics,
        "confusion_matrix": cm.tolist(),
    }


# ===================================================================
# 5. Visualization
# ===================================================================

def plot_learning_curves(all_histories: dict, out_path: str):
    """2-panel plot: Loss (left) + Accuracy (right) for each model."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    colors = {"rnn": "#e74c3c", "lstm": "#3498db", "bilstm": "#2ecc71"}
    for name, hist in all_histories.items():
        c = colors.get(name, "#888")
        epochs = range(1, len(hist["train_loss"]) + 1)
        ax1.plot(epochs, hist["train_loss"], "-", color=c, label=f"{name.upper()} train")
        ax1.plot(epochs, hist["val_loss"], "--", color=c, label=f"{name.upper()} val")
        ax2.plot(epochs, hist["train_acc"], "-", color=c, label=f"{name.upper()} train")
        ax2.plot(epochs, hist["val_acc"], "--", color=c, label=f"{name.upper()} val")

    ax1.set_title("Cross-Entropy Loss", fontsize=13, fontweight="bold")
    ax1.set_xlabel("Epoch")
    ax1.set_ylabel("Loss")
    ax1.legend(fontsize=8)
    ax1.grid(True, alpha=0.3)

    ax2.set_title("Accuracy", fontsize=13, fontweight="bold")
    ax2.set_xlabel("Epoch")
    ax2.set_ylabel("Accuracy")
    ax2.legend(fontsize=8)
    ax2.grid(True, alpha=0.3)

    fig.suptitle("Learning Curves — 30 Epochs", fontsize=15, fontweight="bold", y=1.02)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved learning curves → %s", out_path)


def plot_metrics_comparison(all_metrics: dict, out_path: str):
    """Grouped bar chart comparing Accuracy / F1 / Precision / Recall."""
    metric_names = ["accuracy", "f1_score", "precision", "recall"]
    display_names = ["Accuracy", "F1-Score", "Precision", "Recall"]
    models = list(all_metrics.keys())
    colors = {"rnn": "#e74c3c", "lstm": "#3498db", "bilstm": "#2ecc71"}

    x = np.arange(len(metric_names))
    width = 0.25

    fig, ax = plt.subplots(figsize=(10, 5))
    for i, m in enumerate(models):
        vals = [all_metrics[m][mn] for mn in metric_names]
        bars = ax.bar(x + i * width, vals, width, label=m.upper(), color=colors.get(m, "#888"))
        for bar, v in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.005,
                    f"{v:.3f}", ha="center", va="bottom", fontsize=8)

    ax.set_xticks(x + width)
    ax.set_xticklabels(display_names)
    ax.set_ylim(0, min(1.0, max(v for m in all_metrics.values() for v in m.values()) + 0.15))
    ax.set_title("So Sánh Chỉ Số Hiệu Năng", fontsize=14, fontweight="bold")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved metrics comparison → %s", out_path)


def plot_confusion_matrices(all_cms: dict, class_labels: List[str], out_path: str):
    """1×3 confusion matrix heatmaps."""
    models = list(all_cms.keys())
    n = len(models)
    fig, axes = plt.subplots(1, n, figsize=(6 * n, 5))
    if n == 1:
        axes = [axes]

    for ax, m in zip(axes, models):
        cm = np.array(all_cms[m])
        sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", ax=ax,
                    xticklabels=class_labels, yticklabels=class_labels)
        ax.set_title(f"{m.upper()}", fontsize=12, fontweight="bold")
        ax.set_xlabel("Predicted")
        ax.set_ylabel("Actual")

    fig.suptitle("Confusion Matrices — Test Set", fontsize=15, fontweight="bold", y=1.02)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved confusion matrices → %s", out_path)


def plot_radar_chart(all_metrics: dict, out_path: str):
    """Radar chart overlaying 4 metrics for each model."""
    categories = ["Accuracy", "F1-Score", "Precision", "Recall"]
    metric_keys = ["accuracy", "f1_score", "precision", "recall"]
    N = len(categories)
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    angles += angles[:1]  # close the polygon

    colors = {"rnn": "#e74c3c", "lstm": "#3498db", "bilstm": "#2ecc71"}
    fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True))

    for model_name, mets in all_metrics.items():
        values = [mets[k] for k in metric_keys]
        values += values[:1]
        c = colors.get(model_name, "#888")
        ax.plot(angles, values, "o-", color=c, linewidth=2, label=model_name.upper())
        ax.fill(angles, values, alpha=0.15, color=c)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=11)
    ax.set_ylim(0, 1.0)
    ax.set_title("Model Performance Radar", fontsize=14, fontweight="bold", pad=20)
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1))
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved radar chart → %s", out_path)


# ===================================================================
# 6. Main
# ===================================================================

def parse_args():
    p = argparse.ArgumentParser(
        description="Train & evaluate RNN/LSTM/BiLSTM for 8-class action classification"
    )
    p.add_argument("--source", choices=["csv"], default="csv")
    p.add_argument(
        "--csv",
        default=os.path.join(SERVICE_DIR, "data_user500.csv"),
    )
    p.add_argument("--window", type=int, default=8)
    p.add_argument("--min-events", type=int, default=10)
    p.add_argument("--epochs", type=int, default=30)
    p.add_argument("--batch-size", type=int, default=256)
    p.add_argument("--lr", type=float, default=1e-3)
    p.add_argument(
        "--models",
        nargs="+",
        default=list(MODEL_REGISTRY.keys()),
        help="Models to train (default: rnn lstm bilstm)",
    )
    p.add_argument(
        "--model-out",
        default=os.path.join(SERVICE_DIR, "models", "dl"),
    )
    p.add_argument(
        "--report-out",
        default=os.path.join(SERVICE_DIR, "reports", "deep_learning"),
    )
    return p.parse_args()


def main():
    args = parse_args()
    np.random.seed(SEED)
    torch.manual_seed(SEED)

    # --- Load data ---
    logger.info("Loading CSV: %s", args.csv)
    df = load_interactions_csv(args.csv)
    logger.info("Total interactions: %d  |  Unique users: %d", len(df), df["user_id"].nunique())

    # --- Action distribution ---
    action_counts = df["action"].value_counts()
    logger.info("Action distribution:\n%s", action_counts.to_string())

    # --- Vocab ---
    p2i, a2i = build_vocabs(df, ACTION_LABELS)
    n_products = len(p2i)
    n_actions = len(a2i)
    n_classes = len(ACTION_LABELS)
    logger.info("Vocab: %d products, %d actions, %d classes", n_products, n_actions, n_classes)

    # --- Windowing ---
    xp, xa, y, uids = make_classification_windows(df, p2i, a2i, args.window, args.min_events)
    logger.info("Total samples: %d", xp.shape[0])

    # --- Label distribution ---
    unique, counts = np.unique(y, return_counts=True)
    for u, c in zip(unique, counts):
        lbl = ACTION_LABELS[u] if u < len(ACTION_LABELS) else f"idx_{u}"
        logger.info("  label %d (%s): %d samples (%.1f%%)", u, lbl, c, 100 * c / len(y))

    # --- Split ---
    splits = split_by_user(xp, xa, y, uids)
    for k in ["train", "val", "test"]:
        logger.info("  %s: %d samples (%d users)", k, splits[k][2].shape[0], splits["n_users"][k])

    # --- Train & evaluate each model ---
    all_results: Dict[str, dict] = {}
    for model_type in args.models:
        logger.info("=" * 60)
        logger.info("Training %s ...", model_type.upper())
        logger.info("=" * 60)
        result = train_and_evaluate(
            model_type=model_type,
            splits=splits,
            n_products=n_products,
            n_actions=n_actions,
            n_classes=n_classes,
            epochs=args.epochs,
            batch_size=args.batch_size,
            lr=args.lr,
        )
        all_results[model_type] = result

    # --- Determine best model by F1 ---
    best_name = max(all_results, key=lambda k: all_results[k]["metrics"]["f1_score"])
    logger.info("★ Best model: %s (F1=%.4f)", best_name.upper(), all_results[best_name]["metrics"]["f1_score"])

    # --- Save model weights ---
    os.makedirs(args.model_out, exist_ok=True)
    for name, res in all_results.items():
        path = os.path.join(args.model_out, f"{name}_classification.pt")
        torch.save(res["model"].state_dict(), path)
        logger.info("Saved %s → %s", name, path)

    best_src = os.path.join(args.model_out, f"{best_name}_classification.pt")
    best_dst = os.path.join(args.model_out, "model_best.pt")
    shutil.copy2(best_src, best_dst)
    logger.info("Copied best model → %s", best_dst)

    # --- Save reports ---
    os.makedirs(args.report_out, exist_ok=True)

    # metrics.json
    metrics_payload = {
        "best_model": best_name,
        "n_classes": n_classes,
        "class_labels": ACTION_LABELS,
        "epochs": args.epochs,
        "window": args.window,
        "total_samples": int(xp.shape[0]),
        "split_samples": {k: int(splits[k][2].shape[0]) for k in ["train", "val", "test"]},
        "split_users": splits["n_users"],
        "models": {},
    }
    all_metrics: Dict[str, dict] = {}
    all_histories: Dict[str, dict] = {}
    all_cms: Dict[str, list] = {}

    for name, res in all_results.items():
        metrics_payload["models"][name] = {
            "metrics": res["metrics"],
            "confusion_matrix": res["confusion_matrix"],
        }
        all_metrics[name] = res["metrics"]
        all_histories[name] = res["history"]
        all_cms[name] = res["confusion_matrix"]

    metrics_path = os.path.join(args.report_out, "metrics.json")
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics_payload, f, ensure_ascii=False, indent=2)
    logger.info("Saved metrics → %s", metrics_path)

    # --- Generate figures ---
    plot_learning_curves(all_histories, os.path.join(args.report_out, "learning_curves.png"))
    plot_metrics_comparison(all_metrics, os.path.join(args.report_out, "metrics_comparison.png"))
    plot_confusion_matrices(all_cms, ACTION_LABELS, os.path.join(args.report_out, "confusion_matrices.png"))
    plot_radar_chart(all_metrics, os.path.join(args.report_out, "radar_chart.png"))

    logger.info("=" * 60)
    logger.info("All done! Reports saved to %s", args.report_out)
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
