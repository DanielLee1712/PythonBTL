from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator

class CustomUser(AbstractUser):
    username = models.CharField(
        "username",
        max_length=150,
        unique=True,
        help_text="Required. 150 characters or fewer. Letters, digits and spaces allowed.",
        validators=[RegexValidator(r'^[\w.@+-/ ]+$', "Enter a valid username.")],
        error_messages={
            "unique": "A user with that username already exists.",
        },
    )


class WishlistItem(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="wishlist_items")
    product_id = models.BigIntegerField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (("user", "product_id"),)
        ordering = ["-created_at"]

    def __str__(self):
        return f"user={self.user_id} product={self.product_id}"


class ProductRating(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="product_ratings")
    product_id = models.BigIntegerField(db_index=True)
    rating = models.PositiveSmallIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (("user", "product_id"),)
        ordering = ["-updated_at"]

    def __str__(self):
        return f"user={self.user_id} product={self.product_id} rating={self.rating}"

