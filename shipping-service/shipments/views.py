from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Shipment
from .serializers import ShipmentSerializer


class ShipmentCreateView(APIView):
    """Called by order-service after payment (idempotent per order_id)."""

    def post(self, request):
        order_id = request.data.get('order_id')
        user_id = request.data.get('user_id')
        if order_id is None or user_id is None:
            return Response(
                {'detail': 'order_id and user_id are required'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        order_id = int(order_id)
        user_id = int(user_id)

        shipment, created = Shipment.objects.get_or_create(
            order_id=order_id,
            defaults={
                'user_id': user_id,
                'status': 'created',
                'tracking_code': f'TRK-{order_id}-{user_id}',
            },
        )
        code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(ShipmentSerializer(shipment).data, status=code)
