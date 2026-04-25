"""
Get Product Query
"""
from dataclasses import dataclass


@dataclass
class GetProductQuery:
    """Query to get a single product by ID."""
    product_id: int
