from django.urls import path

from .views import (
    PaymentConfirmView,
    PaymentInitView,
    VnpayIpnView,
    VnpayReturnView,
)

urlpatterns = [
    path('payments/init/', PaymentInitView.as_view(), name='payment-init'),
    path('payments/<int:payment_id>/confirm/', PaymentConfirmView.as_view(), name='payment-confirm'),
    path('payments/vnpay/ipn/', VnpayIpnView.as_view(), name='vnpay-ipn'),
    path('payments/vnpay/return/', VnpayReturnView.as_view(), name='vnpay-return'),
]
