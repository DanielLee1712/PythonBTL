"""
Sequence Service — Unified next-item prediction

Priority: DL ensemble (RNN/LSTM/BiLSTM) → Legacy GRU → empty
"""
import json, logging, os
from typing import Dict, List, Tuple

import torch
import torch.nn as nn

from .kb_graph import normalize_action
from .neo4j_client import neo4j_client

logger = logging.getLogger(__name__)


class NextItemGRU(nn.Module):
    """Legacy GRU model kept for backward compatibility."""
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
        return self.head(out[:, -1, :])


class SequenceService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized") and self._initialized:
            return
        self._initialized = True
        self.device = torch.device("cpu")
        self.window = 8

        # DL service (primary)
        self._dl_service = None
        self._dl_enabled = False

        # Legacy GRU (fallback)
        self._gru_enabled = False
        self.product_to_idx: Dict[str, int] = {"<PAD>": 0, "<UNK>": 1}
        self.action_to_idx: Dict[str, int] = {"<PAD>": 0, "<UNK>": 1}
        self.idx_to_product: Dict[int, str] = {}
        self.model: NextItemGRU | None = None

        self._init_dl_service()
        if not self._dl_enabled:
            self._load_legacy_gru()

    def _init_dl_service(self):
        """Try loading DL ensemble service."""
        try:
            from .dl_service import dl_service
            if dl_service.enabled:
                self._dl_service = dl_service
                self._dl_enabled = True
                self.window = dl_service.window
                self.product_to_idx = dl_service.product_to_idx
                self.action_to_idx = dl_service.action_to_idx
                self.idx_to_product = dl_service.idx_to_product
                logger.info("SequenceService using DL ensemble (%d models)", len(dl_service.models))
            else:
                logger.info("DL models not available, will try legacy GRU.")
        except Exception as e:
            logger.warning("Failed to init DL service: %s", e)

    def _load_legacy_gru(self):
        """Fallback: load legacy GRU model from models/sequence/."""
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        assets_dir = os.path.join(base, "models", "sequence")
        meta_path = os.path.join(assets_dir, "meta.json")
        pvocab = os.path.join(assets_dir, "product_vocab.json")
        avocab = os.path.join(assets_dir, "action_vocab.json")
        weights = os.path.join(assets_dir, "sequence_gru.pt")

        if not all(os.path.exists(p) for p in [meta_path, pvocab, avocab, weights]):
            logger.warning("Legacy GRU assets not found. SequenceService disabled.")
            return

        try:
            with open(meta_path, "r", encoding="utf-8") as f: meta = json.load(f)
            with open(pvocab, "r", encoding="utf-8") as f: self.product_to_idx = json.load(f)
            with open(avocab, "r", encoding="utf-8") as f: self.action_to_idx = json.load(f)

            self.window = int(meta.get("window", 8))
            self.idx_to_product = {int(v): k for k, v in self.product_to_idx.items()}
            self.model = NextItemGRU(n_products=int(meta["n_products"]), n_actions=int(meta["n_actions"]))
            self.model.load_state_dict(torch.load(weights, map_location=self.device))
            self.model.eval()
            self._gru_enabled = True
            logger.info("SequenceService using legacy GRU. window=%d", self.window)
        except Exception as e:
            logger.error("Failed to load legacy GRU: %s", e)

    @property
    def enabled(self):
        return self._dl_enabled or self._gru_enabled

    def _fetch_user_sequence(self, user_id: str, limit: int) -> List[Tuple[str, str]]:
        rows = neo4j_client.execute_read(
            """MATCH (u:User {id: $uid})-[r:INTERACTS_WITH]->(p:Product)
            WHERE r.last_ts IS NOT NULL AND r.action IS NOT NULL
            RETURN p.id AS product_id, r.action AS action, r.last_ts AS ts
            ORDER BY ts ASC LIMIT $limit""",
            {"uid": str(user_id), "limit": int(limit)},
        )
        return [(str(r.get("product_id","")).strip(), normalize_action(r.get("action")))
                for r in rows if str(r.get("product_id","")).strip()]

    def predict_next_scores(self, user_id: str, top_k: int = 20) -> Dict[str, float]:
        # Priority 1: DL ensemble
        if self._dl_enabled and self._dl_service:
            return self._dl_service.predict_next_scores(user_id, top_k)

        # Priority 2: Legacy GRU
        if not self._gru_enabled or self.model is None:
            return {}

        events = self._fetch_user_sequence(str(user_id), limit=max(self.window, 8) * 2)
        if len(events) < self.window:
            return {}

        tail = events[-self.window:]
        p_idx = [self.product_to_idx.get(pid, self.product_to_idx["<UNK>"]) for pid, _ in tail]
        a_idx = [self.action_to_idx.get(act, self.action_to_idx["<UNK>"]) for _, act in tail]
        p_t = torch.tensor([p_idx], dtype=torch.long, device=self.device)
        a_t = torch.tensor([a_idx], dtype=torch.long, device=self.device)

        with torch.no_grad():
            logits = self.model(p_t, a_t)[0]
            probs = torch.softmax(logits, dim=-1)
            values, indices = torch.topk(probs, k=min(top_k, probs.shape[0]))

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


sequence_service = SequenceService()
