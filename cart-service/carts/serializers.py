from rest_framework import serializers

from .models import CartItem


class CartItemSerializer(serializers.ModelSerializer):
    line_total = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = [
            'id',
            'user_id',
            'product_id',
            'product_name',
            'category_name',
            'unit_price',
            'quantity',
            'line_total',
            'updated_at',
        ]
        read_only_fields = ['id', 'line_total', 'updated_at']

    def get_line_total(self, obj):
        return float(obj.unit_price) * obj.quantity


class AddToCartSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(min_value=1)
    product_id = serializers.IntegerField(min_value=1)
    product_name = serializers.CharField(max_length=255)
    category_name = serializers.CharField(max_length=120, required=False, allow_blank=True, default='')
    unit_price = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0)
    quantity = serializers.IntegerField(min_value=1, required=False, default=1)


class UpdateQuantitySerializer(serializers.Serializer):
    user_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=0)
