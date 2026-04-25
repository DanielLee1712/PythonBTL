"""
Filter Products Query - Advanced filtering by JSONB attributes.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class FilterProductsQuery:
    """Query to filter products by JSONB attributes.
    
    Example:
        attribute_filters = {"ram": "16GB", "cpu": "i7"}
    """
    category_id: Optional[int] = None
    brand_id: Optional[int] = None
    attribute_filters: Dict[str, Any] = field(default_factory=dict)
    min_price: Optional[float] = None
    max_price: Optional[float] = None
