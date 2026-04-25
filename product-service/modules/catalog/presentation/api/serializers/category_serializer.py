"""
Category Serializer
"""
from rest_framework import serializers
from modules.catalog.infrastructure.models.category_model import CategoryModel


class CategoryChildSerializer(serializers.ModelSerializer):
    """Serializer for child categories (one level)."""

    class Meta:
        model = CategoryModel
        fields = ['id', 'name', 'slug', 'description', 'is_active', 'sort_order']


class CategorySerializer(serializers.ModelSerializer):
    """Category serializer with parent info."""
    parent_name = serializers.CharField(source='parent.name', read_only=True, default=None)

    class Meta:
        model = CategoryModel
        fields = [
            'id', 'name', 'slug', 'description', 'parent', 'parent_name',
            'is_active', 'sort_order', 'created_at', 'updated_at'
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


class CategoryTreeSerializer(serializers.ModelSerializer):
    """Recursive serializer for category tree."""
    children = serializers.SerializerMethodField()

    class Meta:
        model = CategoryModel
        fields = ['id', 'name', 'slug', 'description', 'is_active', 'sort_order', 'children']

    def get_children(self, obj):
        children = obj.children.filter(is_active=True).order_by('sort_order', 'name')
        return CategoryTreeSerializer(children, many=True).data
