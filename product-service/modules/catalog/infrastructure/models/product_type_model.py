"""
ProductType Django ORM Model
"""
from django.db import models


class ProductTypeModel(models.Model):
    """ProductType model - defines attribute schema for categories of products."""
    
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, allow_unicode=True)
    attribute_schema = models.JSONField(
        default=dict,
        blank=True,
        help_text='JSON schema defining valid attributes for this product type'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'product_types'
        ordering = ['name']
        verbose_name = 'Product Type'
        verbose_name_plural = 'Product Types'

    def __str__(self):
        return self.name
