"""
Product Application Service - Orchestrates use cases.
"""
from typing import List, Optional, Dict, Any
from modules.catalog.domain.entities.product import Product
from shared.utils import generate_slug


class ProductApplicationService:
    """Application service that orchestrates product-related use cases."""

    @staticmethod
    def create_product(
        name: str,
        price: float,
        description: str = '',
        category_id: Optional[int] = None,
        brand_id: Optional[int] = None,
        product_type_id: Optional[int] = None,
        attributes: Optional[Dict[str, Any]] = None,
        image_url: str = '',
    ) -> Product:
        """Create a new product domain entity with validation."""
        product = Product(
            name=name,
            slug=generate_slug(name),
            description=description,
            price=price,
            category_id=category_id,
            brand_id=brand_id,
            product_type_id=product_type_id,
            attributes=attributes or {},
            image_url=image_url,
        )
        product.validate()
        return product

    @staticmethod
    def update_product(
        product: Product,
        name: Optional[str] = None,
        price: Optional[float] = None,
        description: Optional[str] = None,
        category_id: Optional[int] = None,
        brand_id: Optional[int] = None,
        product_type_id: Optional[int] = None,
        attributes: Optional[Dict[str, Any]] = None,
        image_url: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Product:
        """Update an existing product domain entity."""
        if name is not None:
            product.name = name
            product.slug = generate_slug(name)
        if price is not None:
            product.update_price(price)
        if description is not None:
            product.description = description
        if category_id is not None:
            product.category_id = category_id
        if brand_id is not None:
            product.brand_id = brand_id
        if product_type_id is not None:
            product.product_type_id = product_type_id
        if attributes is not None:
            product.update_attributes(attributes)
        if image_url is not None:
            product.image_url = image_url
        if is_active is not None:
            if is_active:
                product.activate()
            else:
                product.deactivate()
        
        product.validate()
        return product
