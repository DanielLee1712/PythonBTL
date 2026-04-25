"""
Create Product Command
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class CreateProductCommand:
    """Command to create a new product."""
    name: str
    price: float
    description: str = ''
    category_id: Optional[int] = None
    brand_id: Optional[int] = None
    product_type_id: Optional[int] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    image_url: str = ''
    is_active: bool = True
