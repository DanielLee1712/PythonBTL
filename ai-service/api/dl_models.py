
from __future__ import annotations

import torch
import torch.nn as nn


class BehaviorRNN(nn.Module):
    def __init__(
        self,
        n_products: int,
        n_actions: int,
        emb_dim: int = 64,
        hidden: int = 128,
        n_classes: int | None = None,
        task: str = "next_item",
    ):
        super().__init__()
        self.task = task
        self.product_emb = nn.Embedding(n_products, emb_dim, padding_idx=0)
        self.action_emb = nn.Embedding(n_actions, emb_dim // 2, padding_idx=0)
        self.rnn = nn.RNN(
            input_size=emb_dim + emb_dim // 2,
            hidden_size=hidden,
            batch_first=True,
        )
        if task == "classification" and n_classes is not None:
            self.head = nn.Linear(hidden, n_classes)
        else:
            self.head = nn.Linear(hidden, n_products)

    def forward(
        self, product_seq: torch.Tensor, action_seq: torch.Tensor
    ) -> torch.Tensor:
        p = self.product_emb(product_seq)
        a = self.action_emb(action_seq)
        x = torch.cat([p, a], dim=-1)
        out, _ = self.rnn(x)
        last = out[:, -1, :]
        return self.head(last)


class BehaviorLSTM(nn.Module):
    """LSTM: Embedding → LSTM → FC Layer"""

    def __init__(
        self,
        n_products: int,
        n_actions: int,
        emb_dim: int = 64,
        hidden: int = 128,
        n_classes: int | None = None,
        task: str = "next_item",
    ):
        super().__init__()
        self.task = task
        self.product_emb = nn.Embedding(n_products, emb_dim, padding_idx=0)
        self.action_emb = nn.Embedding(n_actions, emb_dim // 2, padding_idx=0)
        self.lstm = nn.LSTM(
            input_size=emb_dim + emb_dim // 2,
            hidden_size=hidden,
            batch_first=True,
        )
        if task == "classification" and n_classes is not None:
            self.head = nn.Linear(hidden, n_classes)
        else:
            self.head = nn.Linear(hidden, n_products)

    def forward(
        self, product_seq: torch.Tensor, action_seq: torch.Tensor
    ) -> torch.Tensor:
        p = self.product_emb(product_seq)
        a = self.action_emb(action_seq)
        x = torch.cat([p, a], dim=-1)
        out, _ = self.lstm(x)
        last = out[:, -1, :]
        return self.head(last)


class BehaviorBiLSTM(nn.Module):
    def __init__(
        self,
        n_products: int,
        n_actions: int,
        emb_dim: int = 64,
        hidden: int = 128,
        n_classes: int | None = None,
        task: str = "next_item",
    ):
        super().__init__()
        self.task = task
        self.product_emb = nn.Embedding(n_products, emb_dim, padding_idx=0)
        self.action_emb = nn.Embedding(n_actions, emb_dim // 2, padding_idx=0)
        self.bilstm = nn.LSTM(
            input_size=emb_dim + emb_dim // 2,
            hidden_size=hidden,
            batch_first=True,
            bidirectional=True,
        )
        # BiLSTM output is 2 * hidden
        fc_input = hidden * 2
        if task == "classification" and n_classes is not None:
            self.head = nn.Linear(fc_input, n_classes)
        else:
            self.head = nn.Linear(fc_input, n_products)

    def forward(
        self, product_seq: torch.Tensor, action_seq: torch.Tensor
    ) -> torch.Tensor:
        p = self.product_emb(product_seq)
        a = self.action_emb(action_seq)
        x = torch.cat([p, a], dim=-1)
        out, _ = self.bilstm(x)
        last = out[:, -1, :]
        return self.head(last)


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

MODEL_REGISTRY = {
    "rnn": BehaviorRNN,
    "lstm": BehaviorLSTM,
    "bilstm": BehaviorBiLSTM,
}


def build_model(
    model_type: str,
    n_products: int,
    n_actions: int,
    emb_dim: int = 64,
    hidden: int = 128,
    n_classes: int | None = None,
    task: str = "next_item",
) -> nn.Module:
    """Factory function to create a model by name."""
    cls = MODEL_REGISTRY.get(model_type.lower())
    if cls is None:
        raise ValueError(
            f"Unknown model_type '{model_type}'. Choose from: {list(MODEL_REGISTRY.keys())}"
        )
    return cls(
        n_products=n_products,
        n_actions=n_actions,
        emb_dim=emb_dim,
        hidden=hidden,
        n_classes=n_classes,
        task=task,
    )
