from django.urls import path

from .views import (
    OrderCancelView,
    OrderCollectionView,
    OrderDetailView,
    OrderPayView,
    OrderRetryPaymentView,
)

urlpatterns = [
    path('orders/', OrderCollectionView.as_view(), name='order-collection'),
    path('orders/<int:order_id>/', OrderDetailView.as_view(), name='order-detail'),
    path('orders/<int:order_id>/cancel/', OrderCancelView.as_view(), name='order-cancel'),
    path('orders/<int:order_id>/pay/', OrderPayView.as_view(), name='order-pay'),
    path('orders/<int:order_id>/retry-payment/', OrderRetryPaymentView.as_view(), name='order-retry-payment'),
]
