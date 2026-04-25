"""
Variant Entity - Product variant (size, color, etc.)
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime


@dataclass
class Variant:
    """Product variant (e.g. size S Red, 128GB Black)."""
    
    product_id: int
    sku: str
    name: str
    price_override: Optional[float] = None
    stock: int = 0
    attributes: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def validate(self):
        errors = []
        if not self.sku or not self.sku.strip():
            errors.append("SKU is required.")
        if self.stock < 0:
            errors.append("Stock must be >= 0.")
        if self.price_override is not None and self.price_override < 0:
            errors.append("Price override must be >= 0.")
        if errors:
            from shared.exceptions import ValidationException
            raise ValidationException(", ".join(errors))

    def adjust_stock(self, quantity: int):
        """Adjust stock by quantity (positive = add, negative = remove)."""
        new_stock = self.stock + quantity
        if new_stock < 0:
            from shared.exceptions import ValidationException
            raise ValidationException("Insufficient stock.")
        self.stock = new_stock

    @property
    def effective_price(self):
        """Return price override if set, otherwise None (use product price)."""
        return self.price_override
