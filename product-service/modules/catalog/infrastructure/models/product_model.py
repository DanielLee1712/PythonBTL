"""
Product Django ORM Model
"""
from django.db import models
from modules.catalog.infrastructure.models.category_model import CategoryModel
from modules.catalog.infrastructure.models.brand_model import BrandModel
from modules.catalog.infrastructure.models.product_type_model import ProductTypeModel
from modules.catalog.infrastructure.querysets.product_queryset import ProductQuerySet


class ProductModel(models.Model):
    """Product model with JSONField for flexible attributes."""
    
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, allow_unicode=True)
    description = models.TextField(blank=True, default='')
    price = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    category = models.ForeignKey(
        CategoryModel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products'
    )
    brand = models.ForeignKey(
        BrandModel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products'
    )
    product_type = models.ForeignKey(
        ProductTypeModel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products'
    )
    attributes = models.JSONField(
        default=dict,
        blank=True,
        help_text='Flexible product attributes (e.g. {"ram": "16GB", "cpu": "i7"})'
    )
    image_url = models.URLField(blank=True, default='')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ProductQuerySet.as_manager()

    class Meta:
        db_table = 'products'
        ordering = ['-created_at']
        verbose_name = 'Product'
        verbose_name_plural = 'Products'

    def __str__(self):
        return self.name
