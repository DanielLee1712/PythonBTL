"""
Product Entity - Core domain entity.
Pure business logic, no framework dependency.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime


@dataclass
class Product:
    """Product core entity in the Catalog bounded context."""
    
    name: str
    slug: str
    description: str = ''
    price: float = 0.0
    category_id: Optional[int] = None
    brand_id: Optional[int] = None
    product_type_id: Optional[int] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    image_url: str = ''
    is_active: bool = True
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def validate(self):
        """Validate business rules for Product."""
        errors = []
        if not self.name or not self.name.strip():
            errors.append("Product name is required.")
        if self.price < 0:
            errors.append("Product price must be >= 0.")
        if errors:
            from shared.exceptions import ValidationException
            raise ValidationException(", ".join(errors))

    def activate(self):
        self.is_active = True

    def deactivate(self):
        self.is_active = False

    def update_price(self, new_price: float):
        if new_price < 0:
            from shared.exceptions import ValidationException
            raise ValidationException("Price must be >= 0.")
        self.price = new_price

    def update_attributes(self, attrs: Dict[str, Any]):
        """Merge new attributes into existing attributes."""
        self.attributes.update(attrs)
