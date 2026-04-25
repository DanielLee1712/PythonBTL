"""
Product Repository Implementation - Concrete implementation using Django ORM.
"""
from typing import List, Optional
from modules.catalog.domain.entities.product import Product
from modules.catalog.domain.repositories.product_repository import ProductRepository
from modules.catalog.infrastructure.models.product_model import ProductModel


class DjangoProductRepository(ProductRepository):
    """Concrete product repository using Django ORM."""

    def _to_entity(self, model: ProductModel) -> Product:
        """Convert Django model to domain entity."""
        return Product(
            id=model.id,
            name=model.name,
            slug=model.slug,
            description=model.description,
            price=float(model.price),
            category_id=model.category_id,
            brand_id=model.brand_id,
            product_type_id=model.product_type_id,
            attributes=model.attributes or {},
            image_url=model.image_url,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def get_by_id(self, product_id: int) -> Optional[Product]:
        try:
            model = ProductModel.objects.get(id=product_id)
            return self._to_entity(model)
        except ProductModel.DoesNotExist:
            return None

    def list_all(
        self,
        category_id=None,
        brand_id=None,
        search=None,
        min_price=None,
        max_price=None,
        is_active=None,
    ) -> List[Product]:
        qs = ProductModel.objects.all()
        if is_active is not None:
            qs = qs.active() if is_active else qs.filter(is_active=False)
        if category_id:
            qs = qs.by_category(category_id)
        if brand_id:
            qs = qs.by_brand(brand_id)
        if search:
            qs = qs.search(search)
        if min_price is not None or max_price is not None:
            qs = qs.by_price_range(min_price, max_price)
        return [self._to_entity(m) for m in qs]

    def save(self, product: Product) -> Product:
        if product.id:
            ProductModel.objects.filter(id=product.id).update(
                name=product.name,
                slug=product.slug,
                description=product.description,
                price=product.price,
                category_id=product.category_id,
                brand_id=product.brand_id,
                product_type_id=product.product_type_id,
                attributes=product.attributes,
                image_url=product.image_url,
                is_active=product.is_active,
            )
            return self.get_by_id(product.id)
        else:
            model = ProductModel.objects.create(
                name=product.name,
                slug=product.slug,
                description=product.description,
                price=product.price,
                category_id=product.category_id,
                brand_id=product.brand_id,
                product_type_id=product.product_type_id,
                attributes=product.attributes,
                image_url=product.image_url,
                is_active=product.is_active,
            )
            return self._to_entity(model)

    def delete(self, product_id: int) -> bool:
        deleted, _ = ProductModel.objects.filter(id=product_id).delete()
        return deleted > 0
