from django.db import models


class CartItem(models.Model):
    user_id = models.BigIntegerField(db_index=True)
    product_id = models.BigIntegerField()
    product_name = models.CharField(max_length=255)
    category_name = models.CharField(max_length=120, blank=True, default='')
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user_id', 'product_id'],
                name='unique_cart_item_per_user_and_product',
            )
        ]
        ordering = ['-updated_at']

    def __str__(self):
        return f'user={self.user_id} product={self.product_id} qty={self.quantity}'
