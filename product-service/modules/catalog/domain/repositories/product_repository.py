"""
Product Repository Interface - Abstract repository.
Infrastructure layer provides concrete implementation.
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from modules.catalog.domain.entities.product import Product


class ProductRepository(ABC):
    """Abstract repository interface for Product aggregate."""

    @abstractmethod
    def get_by_id(self, product_id: int) -> Optional[Product]:
        """Get a product by its ID."""
        pass

    @abstractmethod
    def list_all(
        self,
        category_id: Optional[int] = None,
        brand_id: Optional[int] = None,
        search: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        is_active: Optional[bool] = None,
    ) -> List[Product]:
        """List products with optional filters."""
        pass

    @abstractmethod
    def save(self, product: Product) -> Product:
        """Create or update a product."""
        pass

    @abstractmethod
    def delete(self, product_id: int) -> bool:
        """Delete a product by ID."""
        pass
