"""
List Products Query
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class ListProductsQuery:
    """Query to list products with optional filters."""
    category_id: Optional[int] = None
    brand_id: Optional[int] = None
    search: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    is_active: Optional[bool] = True
