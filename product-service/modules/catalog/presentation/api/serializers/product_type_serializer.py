"""
ProductType Serializer
"""
from rest_framework import serializers

from modules.catalog.infrastructure.models.product_type_model import ProductTypeModel


class ProductTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductTypeModel
        fields = [
            "id",
            "name",
            "slug",
            "attribute_schema",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["slug", "created_at", "updated_at"]

    def create(self, validated_data):
        from shared.utils import generate_slug

        validated_data["slug"] = generate_slug(validated_data["name"])
        return super().create(validated_data)

    def update(self, instance, validated_data):
        from shared.utils import generate_slug

        if "name" in validated_data:
            validated_data["slug"] = generate_slug(validated_data["name"])
        return super().update(instance, validated_data)

