"""
Update Product Command
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class UpdateProductCommand:
    """Command to update an existing product."""
    id: int
    name: Optional[str] = None
    price: Optional[float] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    brand_id: Optional[int] = None
    product_type_id: Optional[int] = None
    attributes: Optional[Dict[str, Any]] = None
    image_url: Optional[str] = None
    is_active: Optional[bool] = None
