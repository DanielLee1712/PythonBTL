import os
from datetime import timedelta

import requests
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Order, OrderItem
from .serializers import CreateOrderSerializer, OrderSerializer
from .services.product_stock import adjust_product_stock
from .services.shipping_rates import fee_for_method


def _expire_pending_orders():
    now = timezone.now()
    overdue = Order.objects.filter(
        status=Order.Status.PENDING_PAYMENT,
        payment_deadline__lt=now,
    )
    for order in overdue:
        _restore_order_stock(order)
        order.status = Order.Status.EXPIRED
        order.save(update_fields=['status', 'updated_at'])


def _restore_order_stock(order):
    for line in order.items.all():
        try:
            adjust_product_stock(int(line.product_id), int(line.quantity))
        except Exception:
            pass


def _reserve_order_stock(order):
    for line in order.items.all():
        adjust_product_stock(int(line.product_id), -int(line.quantity))


def _notify_shipping(order):
    base = os.environ.get('SHIPPING_SERVICE_BASE_URL', '').rstrip('/')
    if not base:
        return
    try:
        requests.post(
            f'{base}/api/v1/shipments/',
            json={'order_id': order.id, 'user_id': order.user_id},
            timeout=15,
        )
    except Exception:
        pass


class OrderCollectionView(APIView):
    """GET list by user_id; POST create from checkout payload (cart-service)."""

    def get(self, request):
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response({'detail': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        _expire_pending_orders()
        orders = Order.objects.filter(user_id=int(user_id))
        return Response(OrderSerializer(orders, many=True).data)

    def post(self, request):
        _expire_pending_orders()
        ser = CreateOrderSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        user_id = int(data['user_id'])
        lines = data['items']
        subtotal = sum(float(l['unit_price']) * int(l['quantity']) for l in lines)
        shipping_method = data['shipping_method']
        shipping_fee = float(fee_for_method(shipping_method))
        shipping_address = data['shipping_address'].strip()
        total = subtotal + shipping_fee
        deadline = timezone.now() + timedelta(minutes=5)

        with transaction.atomic():
            order = Order.objects.create(
                user_id=user_id,
                status=Order.Status.PENDING_PAYMENT,
                subtotal=subtotal,
                shipping_fee=shipping_fee,
                shipping_method=shipping_method,
                shipping_address=shipping_address,
                total=total,
                payment_deadline=deadline,
            )
            for l in lines:
                OrderItem.objects.create(
                    order=order,
                    product_id=l['product_id'],
                    product_name=l['product_name'],
                    unit_price=l['unit_price'],
                    quantity=l['quantity'],
                )

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class OrderDetailView(APIView):
    def get(self, request, order_id):
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response({'detail': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        _expire_pending_orders()
        try:
            order = Order.objects.get(id=order_id, user_id=int(user_id))
        except Order.DoesNotExist:
            return Response({'detail': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(OrderSerializer(order).data)


class OrderCancelView(APIView):
    def post(self, request, order_id):
        user_id = request.data.get('user_id') or request.query_params.get('user_id')
        if not user_id:
            return Response({'detail': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        _expire_pending_orders()
        try:
            order = Order.objects.get(id=order_id, user_id=int(user_id))
        except Order.DoesNotExist:
            return Response({'detail': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
        if order.status != Order.Status.PENDING_PAYMENT:
            return Response({'detail': 'Only pending orders can be cancelled'}, status=status.HTTP_400_BAD_REQUEST)
        _restore_order_stock(order)
        order.status = Order.Status.CANCELLED
        order.save(update_fields=['status', 'updated_at'])
        return Response(OrderSerializer(order).data)


class OrderPayView(APIView):
    """Mark order paid (called by payment-service after user confirms)."""

    def post(self, request, order_id):
        user_id = request.data.get('user_id') or request.query_params.get('user_id')
        if not user_id:
            return Response({'detail': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        _expire_pending_orders()
        try:
            order = Order.objects.get(id=order_id, user_id=int(user_id))
        except Order.DoesNotExist:
            return Response({'detail': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
        if order.status == Order.Status.PAID:
            return Response(OrderSerializer(order).data)
        if order.status != Order.Status.PENDING_PAYMENT:
            return Response({'detail': 'Order is not awaiting payment'}, status=status.HTTP_400_BAD_REQUEST)
        if timezone.now() > order.payment_deadline:
            _restore_order_stock(order)
            order.status = Order.Status.EXPIRED
            order.save(update_fields=['status', 'updated_at'])
            return Response({'detail': 'Payment window expired'}, status=status.HTTP_400_BAD_REQUEST)
        order.status = Order.Status.PAID
        order.save(update_fields=['status', 'updated_at'])
        _notify_shipping(order)
        return Response(OrderSerializer(order).data)


class OrderRetryPaymentView(APIView):
    def post(self, request, order_id):
        user_id = request.data.get('user_id') or request.query_params.get('user_id')
        if not user_id:
            return Response({'detail': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        _expire_pending_orders()
        try:
            order = Order.objects.get(id=order_id, user_id=int(user_id))
        except Order.DoesNotExist:
            return Response({'detail': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
        if order.status not in (Order.Status.EXPIRED, Order.Status.CANCELLED):
            return Response({'detail': 'Order cannot be re-opened for payment'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            _reserve_order_stock(order)
        except Exception as e:
            return Response(
                {'detail': 'Could not reserve stock', 'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        order.status = Order.Status.PENDING_PAYMENT
        order.payment_deadline = timezone.now() + timedelta(minutes=5)
        order.save(update_fields=['status', 'payment_deadline', 'updated_at'])
        return Response(OrderSerializer(order).data)
