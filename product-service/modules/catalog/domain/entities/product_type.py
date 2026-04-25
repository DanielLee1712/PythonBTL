"""
ProductType Entity - Defines attribute schema for product types.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime


@dataclass
class ProductType:
    """ProductType defines the attribute schema for a category of products.
    
    Example:
        name: "Laptop"
        attribute_schema: {
            "ram": {"type": "string", "required": true},
            "cpu": {"type": "string", "required": true},
            "storage": {"type": "string", "required": false}
        }
    """
    
    name: str
    slug: str
    attribute_schema: Dict[str, Any] = field(default_factory=dict)
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def validate(self):
        if not self.name or not self.name.strip():
            from shared.exceptions import ValidationException
            raise ValidationException("ProductType name is required.")
