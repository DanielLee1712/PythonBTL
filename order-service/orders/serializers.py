from rest_framework import serializers

from .models import Order, OrderItem
from .services.shipping_rates import SHIPPING_OPTIONS, label_for_method


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'product_id', 'product_name', 'unit_price', 'quantity']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    shipping_method_label = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id',
            'user_id',
            'status',
            'subtotal',
            'shipping_fee',
            'shipping_method',
            'shipping_method_label',
            'shipping_address',
            'total',
            'payment_deadline',
            'created_at',
            'updated_at',
            'items',
        ]

    def get_shipping_method_label(self, obj):
        if not obj.shipping_method:
            return ''
        return label_for_method(obj.shipping_method)


class CreateOrderItemSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(min_value=1)
    product_name = serializers.CharField(max_length=255)
    unit_price = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0)
    quantity = serializers.IntegerField(min_value=1)


class CreateOrderSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(min_value=1)
    items = CreateOrderItemSerializer(many=True)
    shipping_address = serializers.CharField(min_length=8, max_length=2000)
    shipping_method = serializers.ChoiceField(
        choices=[(k, v['label']) for k, v in SHIPPING_OPTIONS.items()],
    )

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError('At least one line item is required.')
        return value
