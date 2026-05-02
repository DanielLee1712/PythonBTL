from django.urls import path

from .views import (
    CartClearView,
    CartItemCreateView,
    CartItemDetailView,
    CartView,
    OrderCheckoutView,
)

urlpatterns = [
    path('cart/', CartView.as_view(), name='cart-detail'),
    path('cart/items/', CartItemCreateView.as_view(), name='cart-item-create'),
    path('cart/items/<int:item_id>/', CartItemDetailView.as_view(), name='cart-item-detail'),
    path('cart/clear/', CartClearView.as_view(), name='cart-clear'),
    path('orders/checkout/', OrderCheckoutView.as_view(), name='order-checkout'),
]
