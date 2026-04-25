from django.contrib import admin
from .models import CartItem


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_id', 'product_id', 'product_name', 'quantity', 'unit_price', 'updated_at')
    search_fields = ('product_name', 'user_id', 'product_id')
    list_filter = ('user_id',)
