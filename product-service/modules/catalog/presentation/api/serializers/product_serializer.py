"""
Product and Variant Serializers
"""
from rest_framework import serializers
from modules.catalog.infrastructure.models.product_model import ProductModel
from modules.catalog.infrastructure.models.variant_model import VariantModel
from modules.catalog.infrastructure.models.category_model import CategoryModel
from modules.catalog.infrastructure.models.brand_model import BrandModel


class VariantSerializer(serializers.ModelSerializer):
    """Variant serializer."""
    effective_price = serializers.DecimalField(
        max_digits=15, decimal_places=2, read_only=True
    )

    class Meta:
        model = VariantModel
        fields = [
            'id', 'product', 'sku', 'name', 'price_override',
            'effective_price', 'stock', 'attributes', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class ProductListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for product listings."""
    category_name = serializers.CharField(source='category.name', read_only=True, default=None)
    brand_name = serializers.CharField(source='brand.name', read_only=True, default=None)

    class Meta:
        model = ProductModel
        fields = [
            'id', 'name', 'slug', 'price', 'category', 'category_name',
            'brand', 'brand_name', 'image_url', 'is_active', 'created_at'
        ]


class ProductDetailSerializer(serializers.ModelSerializer):
    """Full serializer for product detail with nested variants."""
    variants = VariantSerializer(many=True, read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True, default=None)
    brand_name = serializers.CharField(source='brand.name', read_only=True, default=None)
    product_type_name = serializers.CharField(source='product_type.name', read_only=True, default=None)

    class Meta:
        model = ProductModel
        fields = [
            'id', 'name', 'slug', 'description', 'price',
            'category', 'category_name',
            'brand', 'brand_name',
            'product_type', 'product_type_name',
            'attributes', 'image_url', 'is_active',
            'variants',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['slug', 'created_at', 'updated_at']

    def create(self, validated_data):
        from shared.utils import generate_slug
        validated_data['slug'] = generate_slug(validated_data['name'])
        return super().create(validated_data)

    def update(self, instance, validated_data):
        from shared.utils import generate_slug
        if 'name' in validated_data:
            validated_data['slug'] = generate_slug(validated_data['name'])
        return super().update(instance, validated_data)
