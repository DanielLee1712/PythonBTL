"""
Product Custom QuerySet with filter methods.
"""
from django.db import models


class ProductQuerySet(models.QuerySet):
    """Custom QuerySet providing reusable filter methods for products."""

    def active(self):
        return self.filter(is_active=True)

    def by_category(self, category_id):
        """Filter by category (including child categories)."""
        from modules.catalog.infrastructure.models.category_model import CategoryModel
        # Get all descendant category IDs
        category_ids = [category_id]
        children = CategoryModel.objects.filter(parent_id=category_id).values_list('id', flat=True)
        category_ids.extend(children)
        # Recursively get grandchildren (2 levels deep)
        for child_id in children:
            grandchildren = CategoryModel.objects.filter(parent_id=child_id).values_list('id', flat=True)
            category_ids.extend(grandchildren)
        return self.filter(category_id__in=category_ids)

    def by_brand(self, brand_id):
        return self.filter(brand_id=brand_id)

    def by_price_range(self, min_price=None, max_price=None):
        qs = self
        if min_price is not None:
            qs = qs.filter(price__gte=min_price)
        if max_price is not None:
            qs = qs.filter(price__lte=max_price)
        return qs

    def search(self, query):
        """Search by name or description."""
        return self.filter(
            models.Q(name__icontains=query) |
            models.Q(description__icontains=query)
        )

    def by_attributes(self, attribute_filters: dict):
        """Filter by JSON attributes.
        
        Example: {"ram": "16GB", "cpu": "i7"}
        """
        qs = self
        for key, value in attribute_filters.items():
            qs = qs.filter(**{f'attributes__{key}': value})
        return qs
