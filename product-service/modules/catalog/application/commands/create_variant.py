"""
Create Variant Command
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class CreateVariantCommand:
    """Command to create a product variant."""
    product_id: int
    sku: str
    name: str
    price_override: Optional[float] = None
    stock: int = 0
    attributes: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True
