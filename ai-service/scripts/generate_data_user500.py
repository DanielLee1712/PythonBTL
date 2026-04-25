import argparse
import csv
import random
from datetime import datetime, timedelta
from pathlib import Path


ACTIONS = [
    "view",
    "click",
    "add_to_cart",
    "purchase",
    "search",
    "wishlist",
    "rate",
    "remove_from_cart",
]


DEFAULT_START_PROBS = {
    "view": 0.35,
    "search": 0.25,
    "click": 0.15,
    "wishlist": 0.10,
    "add_to_cart": 0.07,
    "purchase": 0.03,
    "rate": 0.03,
    "remove_from_cart": 0.02,
}

TRANSITIONS = {
    "view": {
        "view": 0.22,
        "search": 0.18,
        "click": 0.25,
        "wishlist": 0.12,
        "add_to_cart": 0.10,
        "purchase": 0.05,
        "rate": 0.03,
        "remove_from_cart": 0.05,
    },
    "search": {
        "search": 0.20,
        "view": 0.25,
        "click": 0.20,
        "wishlist": 0.10,
        "add_to_cart": 0.10,
        "purchase": 0.05,
        "rate": 0.03,
        "remove_from_cart": 0.07,
    },
    "click": {
        "view": 0.25,
        "search": 0.12,
        "click": 0.20,
        "wishlist": 0.10,
        "add_to_cart": 0.16,
        "purchase": 0.08,
        "rate": 0.03,
        "remove_from_cart": 0.06,
    },
    "wishlist": {
        "view": 0.18,
        "search": 0.10,
        "click": 0.14,
        "wishlist": 0.20,
        "add_to_cart": 0.18,
        "purchase": 0.12,
        "rate": 0.04,
        "remove_from_cart": 0.04,
    },
    "add_to_cart": {
        "view": 0.12,
        "search": 0.08,
        "click": 0.10,
        "wishlist": 0.06,
        "add_to_cart": 0.24,
        "purchase": 0.28,
        "rate": 0.06,
        "remove_from_cart": 0.06,
    },
    "purchase": {
        "view": 0.32,
        "search": 0.16,
        "click": 0.12,
        "wishlist": 0.08,
        "add_to_cart": 0.06,
        "purchase": 0.06,
        "rate": 0.16,
        "remove_from_cart": 0.04,
    },
    "rate": {
        "view": 0.30,
        "search": 0.20,
        "click": 0.18,
        "wishlist": 0.10,
        "add_to_cart": 0.08,
        "purchase": 0.05,
        "rate": 0.05,
        "remove_from_cart": 0.04,
    },
    "remove_from_cart": {
        "view": 0.33,
        "search": 0.20,
        "click": 0.15,
        "wishlist": 0.11,
        "add_to_cart": 0.08,
        "purchase": 0.03,
        "rate": 0.03,
        "remove_from_cart": 0.07,
    },
}


def weighted_choice(rng: random.Random, probs: dict[str, float]) -> str:
    labels = list(probs.keys())
    weights = [probs[k] for k in labels]
    return rng.choices(labels, weights=weights, k=1)[0]


def sample_action(rng: random.Random, previous_action: str | None) -> str:
    if previous_action is None:
        return weighted_choice(rng, DEFAULT_START_PROBS)

    # Small exploration noise prevents degenerate trajectories.
    if rng.random() < 0.12:
        return rng.choice(ACTIONS)
    return weighted_choice(rng, TRANSITIONS[previous_action])


def generate_rows(
    n_users: int,
    n_products: int,
    interactions_per_user: int,
    start_time: datetime,
    end_time: datetime,
    seed: int,
):
    rng = random.Random(seed)
    total_seconds = int((end_time - start_time).total_seconds())

    rows = []
    for user_id in range(1, n_users + 1):
        # Keep per-user interactions in chronological order
        offsets = sorted(rng.randint(0, total_seconds) for _ in range(interactions_per_user))
        previous_action = None
        for i, offset in enumerate(offsets):
            action = sample_action(rng, previous_action)
            # Blend stable user preference with global randomness.
            base_product = ((user_id * 7 + i * 11) % n_products) + 1
            if rng.random() < 0.65:
                product_id = base_product
            else:
                product_id = rng.randint(1, n_products)
            event_time = start_time + timedelta(seconds=offset)
            rows.append(
                {
                    "user_id": user_id,
                    "product_id": product_id,
                    "action": action,
                    "timestamp": event_time.strftime("%d/%m/%Y %H:%M:%S"),
                }
            )
            previous_action = action
    return rows


def parse_args():
    parser = argparse.ArgumentParser(description="Generate normalized data_user500.csv")
    parser.add_argument(
        "--output",
        default=str(Path(__file__).resolve().parents[1] / "data_user500.csv"),
        help="Output CSV path (default: ai-service/data_user500.csv)",
    )
    parser.add_argument("--users", type=int, default=500, help="Number of users (default: 500)")
    parser.add_argument("--products", type=int, default=50, help="Number of products (default: 50)")
    parser.add_argument(
        "--interactions-per-user",
        type=int,
        default=26,
        help="Interactions per user (default: 26, ~12,725 total with exploration)",
    )
    parser.add_argument(
        "--start",
        default="2025-01-01 00:00:00",
        help="Start timestamp (YYYY-MM-DD HH:MM:SS)",
    )
    parser.add_argument(
        "--end",
        default="2025-12-31 23:59:59",
        help="End timestamp (YYYY-MM-DD HH:MM:SS)",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    return parser.parse_args()


def main():
    args = parse_args()
    if args.users < 1 or args.products < 1 or args.interactions_per_user < 1:
        raise ValueError("users, products, and interactions-per-user must be >= 1")

    start_time = datetime.strptime(args.start, "%Y-%m-%d %H:%M:%S")
    end_time = datetime.strptime(args.end, "%Y-%m-%d %H:%M:%S")
    if end_time <= start_time:
        raise ValueError("end must be greater than start")

    rows = generate_rows(
        n_users=args.users,
        n_products=args.products,
        interactions_per_user=args.interactions_per_user,
        start_time=start_time,
        end_time=end_time,
        seed=args.seed,
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["user_id", "product_id", "action", "timestamp"], delimiter=";")
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {output_path}")


if __name__ == "__main__":
    main()
