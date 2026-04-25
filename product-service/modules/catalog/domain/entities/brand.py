"""
Brand Entity
"""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class Brand:
    """Brand entity."""
    
    name: str
    slug: str
    description: str = ''
    logo_url: str = ''
    is_active: bool = True
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def validate(self):
        if not self.name or not self.name.strip():
            from shared.exceptions import ValidationException
            raise ValidationException("Brand name is required.")
