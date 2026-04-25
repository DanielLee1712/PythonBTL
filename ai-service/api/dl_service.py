"""
Câu 2a — Deep Learning Inference Service

Runtime service loading trained PyTorch RNN/LSTM/BiLSTM models
for next-item prediction and behavior classification.
Ensemble: averages predictions from all available models.
Falls back to legacy GRU if DL models not trained yet.
"""
from __future__ import annotations
import json, logging, os
from typing import Dict, List, Optional, Tuple
import torch
import torch.nn as nn
from .dl_models import build_model, MODEL_REGISTRY
from .kb_graph import normalize_action
from .neo4j_client import neo4j_client

logger = logging.getLogger(__name__)


class DLService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized") and self._initialized:
            return
        self._initialized = True
        self.enabled = False
        self.device = torch.device("cpu")
        self.window = 8
        self.models: Dict[str, nn.Module] = {}
        self.product_to_idx: Dict[str, int] = {"<PAD>": 0, "<UNK>": 1}
        self.action_to_idx: Dict[str, int] = {"<PAD>": 0, "<UNK>": 1}
        self.idx_to_product: Dict[int, str] = {}
        self._load_assets()

    def _assets_dir(self) -> str:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base, "models", "dl")

    def _load_assets(self) -> None:
        assets_dir = self._assets_dir()
        meta_path = os.path.join(assets_dir, "meta.json")
        pvocab = os.path.join(assets_dir, "product_vocab.json")
        avocab = os.path.join(assets_dir, "action_vocab.json")

        if not all(os.path.exists(p) for p in [meta_path, pvocab, avocab]):
            logger.warning("DL model assets not found at %s. DLService disabled.", assets_dir)
            return

        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            with open(pvocab, "r", encoding="utf-8") as f:
                self.product_to_idx = json.load(f)
            with open(avocab, "r", encoding="utf-8") as f:
                self.action_to_idx = json.load(f)

            self.window = int(meta.get("window", 8))
            n_products = int(meta["n_products"])
            n_actions = int(meta["n_actions"])
            self.idx_to_product = {int(v): k for k, v in self.product_to_idx.items()}

            # Load each available model
            for model_type in MODEL_REGISTRY:
                weights_path = os.path.join(assets_dir, f"{model_type}.pt")
                if not os.path.exists(weights_path):
                    continue
                model = build_model(model_type, n_products=n_products, n_actions=n_actions)
                model.load_state_dict(torch.load(weights_path, map_location=self.device, weights_only=True))
                model.eval()
                self.models[model_type] = model
                logger.info("Loaded DL model: %s", model_type)

            if self.models:
                self.enabled = True
                logger.info("DLService enabled with %d models. window=%d", len(self.models), self.window)
            else:
                logger.warning("No DL model weights found. DLService disabled.")
        except Exception as e:
            logger.error("Failed to load DL assets: %s", e)

    def _fetch_user_sequence(self, user_id: str, limit: int) -> List[Tuple[str, str]]:
        query = """
        MATCH (u:User {id: $uid})-[r:INTERACTS_WITH]->(p:Product)
        WHERE r.last_ts IS NOT NULL AND r.action IS NOT NULL
        RETURN p.id AS product_id, r.action AS action, r.last_ts AS ts
        ORDER BY ts ASC LIMIT $limit
        """
        rows = neo4j_client.execute_read(query, {"uid": str(user_id), "limit": int(limit)})
        return [(str(r.get("product_id","")).strip(), normalize_action(r.get("action")))
                for r in rows if str(r.get("product_id","")).strip()]

    def predict_next_scores(self, user_id: str, top_k: int = 20) -> Dict[str, float]:
        """Ensemble prediction from all loaded DL models."""
        if not self.enabled:
            return {}

        events = self._fetch_user_sequence(str(user_id), limit=max(self.window, 8) * 2)
        if len(events) < self.window:
            return {}

        tail = events[-self.window:]
        p_idx = [self.product_to_idx.get(pid, self.product_to_idx["<UNK>"]) for pid, _ in tail]
        a_idx = [self.action_to_idx.get(act, self.action_to_idx["<UNK>"]) for _, act in tail]
        p_t = torch.tensor([p_idx], dtype=torch.long, device=self.device)
        a_t = torch.tensor([a_idx], dtype=torch.long, device=self.device)

        # Ensemble: average softmax probabilities from all models
        all_probs = []
        for name, model in self.models.items():
            with torch.no_grad():
                logits = model(p_t, a_t)[0]
                probs = torch.softmax(logits, dim=-1)
                all_probs.append(probs)

        if not all_probs:
            return {}

        avg_probs = torch.stack(all_probs).mean(dim=0)
        values, indices = torch.topk(avg_probs, k=min(top_k, avg_probs.shape[0]))

        scores: Dict[str, float] = {}
        for score, idx in zip(values.tolist(), indices.tolist()):
            pid = self.idx_to_product.get(int(idx))
            if not pid or pid in ("<PAD>", "<UNK>"):
                continue
            scores[str(pid)] = float(score)
        return scores

    def recommend_next_items(self, user_id: str, k: int = 5) -> List[str]:
        scores = self.predict_next_scores(user_id, top_k=max(k, 20))
        if not scores:
            return []
        return [pid for pid, _ in sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:k]]


dl_service = DLService()
