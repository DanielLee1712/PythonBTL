"""
Brand API Views
"""
from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend

from modules.catalog.infrastructure.models.brand_model import BrandModel
from rest_framework import serializers


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = BrandModel
        fields = ['id', 'name', 'slug', 'description', 'logo_url', 'is_active', 'created_at', 'updated_at']
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


class BrandViewSet(viewsets.ModelViewSet):
    """
    Brand ViewSet - CRUD.
    
    list:   GET /api/brands/
    create: POST /api/brands/
    read:   GET /api/brands/{id}/
    update: PUT /api/brands/{id}/
    delete: DELETE /api/brands/{id}/
    """
    queryset = BrandModel.objects.all()
    serializer_class = BrandSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['is_active']
    search_fields = ['name']
