"""
Variant Django ORM Model
"""
from django.db import models
from modules.catalog.infrastructure.models.product_model import ProductModel


class VariantModel(models.Model):
    """Product variant model (e.g. size, color combinations)."""
    
    product = models.ForeignKey(
        ProductModel,
        on_delete=models.CASCADE,
        related_name='variants'
    )
    sku = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    price_override = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True,
        help_text='Override product price for this variant'
    )
    stock = models.PositiveIntegerField(default=0)
    attributes = models.JSONField(
        default=dict,
        blank=True,
        help_text='Variant-specific attributes (e.g. {"size": "L", "color": "Red"})'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'variants'
        ordering = ['name']
        verbose_name = 'Variant'
        verbose_name_plural = 'Variants'

    def __str__(self):
        return f"{self.product.name} - {self.name}"

    @property
    def effective_price(self):
        """Return variant price if overridden, otherwise product price."""
        return self.price_override if self.price_override is not None else self.product.price
