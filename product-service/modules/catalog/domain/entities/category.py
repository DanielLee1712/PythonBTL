"""
Category Entity - Category tree structure.
"""
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime


@dataclass
class Category:
    """Category entity forming a tree structure.
    
    Examples:
        Electronics -> Laptop, Mobile, Điều hòa, Tủ lạnh
        Thời trang -> Áo, Quần, Giày dép
        Mỹ phẩm -> Son môi, Kem nền
    """
    
    name: str
    slug: str
    description: str = ''
    parent_id: Optional[int] = None
    is_active: bool = True
    sort_order: int = 0
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    children: List['Category'] = field(default_factory=list)

    def validate(self):
        if not self.name or not self.name.strip():
            from shared.exceptions import ValidationException
            raise ValidationException("Category name is required.")

    @property
    def is_root(self) -> bool:
        return self.parent_id is None

    @property
    def has_children(self) -> bool:
        return len(self.children) > 0
