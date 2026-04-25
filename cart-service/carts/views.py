from django.db.models import F, Sum
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import CartItem
from .serializers import AddToCartSerializer, CartItemSerializer, UpdateQuantitySerializer


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

        cart_item, created = CartItem.objects.get_or_create(
            user_id=payload['user_id'],
            product_id=payload['product_id'],
            defaults={
                'product_name': payload['product_name'],
                'category_name': payload.get('category_name', ''),
                'unit_price': payload['unit_price'],
                'quantity': payload.get('quantity', 1),
            },
        )

        if not created:
            cart_item.quantity += payload.get('quantity', 1)
            cart_item.product_name = payload['product_name']
            cart_item.category_name = payload.get('category_name', '')
            cart_item.unit_price = payload['unit_price']
            cart_item.save(update_fields=['quantity', 'product_name', 'category_name', 'unit_price', 'updated_at'])

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

        quantity = payload['quantity']
        if quantity <= 0:
            cart_item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        cart_item.quantity = quantity
        cart_item.save(update_fields=['quantity', 'updated_at'])
        return Response(CartItemSerializer(cart_item).data)

    def delete(self, request, item_id):
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response({'detail': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        deleted, _ = CartItem.objects.filter(id=item_id, user_id=user_id).delete()
        if not deleted:
            return Response({'detail': 'Cart item not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CartClearView(APIView):
    def delete(self, request):
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response({'detail': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        CartItem.objects.filter(user_id=user_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
