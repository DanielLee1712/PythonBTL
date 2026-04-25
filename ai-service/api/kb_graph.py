from __future__ import annotations

from datetime import datetime

ACTION_WEIGHTS = {
    "remove_from_cart": 1.0,
    "view": 1.5,
    "click": 2.0,
    "wishlist": 2.0,
    "search": 2.5,
    "add_to_cart": 3.0,
    "rate": 3.5,
    "purchase": 4.5,
}

DEFAULT_ACTION_WEIGHT = 1.0
# Source CSV `data_user500.csv` uses `dd/mm/YYYY HH:MM:SS` (e.g. 10/01/2025 17:07:01)
TIMESTAMP_FORMAT = "%d/%m/%Y %H:%M:%S"


def normalize_action(action: str | None) -> str:
    if action is None:
        return "unknown"
    normalized = str(action).strip().lower()
    return normalized or "unknown"


def clean_identifier(raw_value: str | None) -> str:
    if raw_value is None:
        return ""
    value = str(raw_value).strip()
    value = value.encode("utf-8", errors="ignore").decode("utf-8", errors="ignore")
    return value


def action_weight(action: str | None) -> float:
    normalized = normalize_action(action)
    return ACTION_WEIGHTS.get(normalized, DEFAULT_ACTION_WEIGHT)


def parse_timestamp(raw_timestamp: str | None) -> datetime:
    if raw_timestamp is None:
        raise ValueError("timestamp is required")

    timestamp_str = str(raw_timestamp).strip()
    timestamp_str = " ".join(timestamp_str.split())
    return datetime.strptime(timestamp_str, TIMESTAMP_FORMAT)
