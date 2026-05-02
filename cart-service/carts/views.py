import os

import requests
from django.db.models import F, Sum
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import CartItem
from .serializers import (
    AddToCartSerializer,
    CartItemSerializer,
    UpdateQuantitySerializer,
)
from .services.product_stock import adjust_product_stock


class CartView(APIView):
    def get(self, request):
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response({'detail': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        items = CartItem.objects.filter(user_id=user_id)
        serializer = CartItemSerializer(items, many=True)
        total = items.aggregate(total=Sum(F('unit_price') * F('quantity')))['total'] or 0
        return Response(
            {
                'user_id': int(user_id),
                'items': serializer.data,
                'total': float(total),
            }
        )


class CartItemCreateView(APIView):
    def post(self, request):
        serializer = AddToCartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data

        add_qty = int(payload.get('quantity', 1))
        user_id = int(payload['user_id'])
        product_id = int(payload['product_id'])

        try:
            adjust_product_stock(product_id, -add_qty)
        except Exception as e:
            return Response(
                {'detail': 'Insufficient stock or product unavailable', 'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            cart_item, created = CartItem.objects.get_or_create(
                user_id=user_id,
                product_id=product_id,
                defaults={
                    'product_name': payload['product_name'],
                    'category_name': payload.get('category_name', ''),
                    'unit_price': payload['unit_price'],
                    'quantity': add_qty,
                },
            )

            if not created:
                cart_item.quantity += add_qty
                cart_item.product_name = payload['product_name']
                cart_item.category_name = payload.get('category_name', '')
                cart_item.unit_price = payload['unit_price']
                cart_item.save(
                    update_fields=['quantity', 'product_name', 'category_name', 'unit_price', 'updated_at']
                )
        except Exception:
            try:
                adjust_product_stock(product_id, add_qty)
            except Exception:
                pass
            return Response(
                {'detail': 'Could not save cart item'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(CartItemSerializer(cart_item).data, status=status.HTTP_201_CREATED)


class CartItemDetailView(APIView):
    def patch(self, request, item_id):
        serializer = UpdateQuantitySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data

        try:
            cart_item = CartItem.objects.get(id=item_id, user_id=payload['user_id'])
        except CartItem.DoesNotExist:
            return Response({'detail': 'Cart item not found'}, status=status.HTTP_404_NOT_FOUND)

        old_qty = int(cart_item.quantity)
        quantity = int(payload['quantity'])
        delta = quantity - old_qty

        if quantity <= 0:
            try:
                adjust_product_stock(int(cart_item.product_id), old_qty)
            except Exception:
                pass
            cart_item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        if delta != 0:
            try:
                adjust_product_stock(int(cart_item.product_id), -delta)
            except Exception:
                return Response(
                    {'detail': 'Insufficient stock for requested quantity'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        cart_item.quantity = quantity
        cart_item.save(update_fields=['quantity', 'updated_at'])
        return Response(CartItemSerializer(cart_item).data)

    def delete(self, request, item_id):
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response({'detail': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            cart_item = CartItem.objects.get(id=item_id, user_id=user_id)
        except CartItem.DoesNotExist:
            return Response({'detail': 'Cart item not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            adjust_product_stock(int(cart_item.product_id), int(cart_item.quantity))
        except Exception:
            pass
        cart_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CartClearView(APIView):
    def delete(self, request):
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response({'detail': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        items = list(CartItem.objects.filter(user_id=user_id))
        for cart_item in items:
            try:
                adjust_product_stock(int(cart_item.product_id), int(cart_item.quantity))
            except Exception:
                pass
        CartItem.objects.filter(user_id=user_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class OrderCheckoutView(APIView):
    """Create order in order-service from cart; clear cart only after success."""

    def post(self, request):
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({'detail': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        user_id = int(user_id)

        items = list(CartItem.objects.filter(user_id=user_id))
        if not items:
            return Response({'detail': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)

        shipping_address = (request.data.get('shipping_address') or '').strip()
        shipping_method = (request.data.get('shipping_method') or '').strip()
        if not shipping_address or len(shipping_address) < 8:
            return Response(
                {'detail': 'shipping_address is required (at least 8 characters)'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if shipping_method not in ('standard', 'express', 'same_day'):
            return Response(
                {'detail': 'shipping_method must be one of: standard, express, same_day'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        payload = {
            'user_id': user_id,
            'shipping_address': shipping_address,
            'shipping_method': shipping_method,
            'items': [
                {
                    'product_id': int(i.product_id),
                    'product_name': i.product_name,
                    'unit_price': str(i.unit_price),
                    'quantity': int(i.quantity),
                }
                for i in items
            ],
        }

        base = os.environ.get('ORDER_SERVICE_BASE_URL', 'http://127.0.0.1:8005').rstrip('/')
        try:
            r = requests.post(f'{base}/api/v1/orders/', json=payload, timeout=60)
        except requests.RequestException as e:
            return Response(
                {'detail': 'Order service unreachable', 'error': str(e)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        if r.status_code >= 400:
            try:
                detail = r.json()
            except Exception:
                detail = {'detail': r.text}
            return Response(detail, status=r.status_code)

        CartItem.objects.filter(user_id=user_id).delete()
        return Response(r.json(), status=status.HTTP_201_CREATED)
