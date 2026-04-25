"""
Category API Views
"""
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from modules.catalog.infrastructure.models.category_model import CategoryModel
from modules.catalog.presentation.api.serializers.category_serializer import (
    CategorySerializer,
    CategoryTreeSerializer,
)


class CategoryViewSet(viewsets.ModelViewSet):
    """
    Category ViewSet - CRUD with tree endpoint.
    
    list:   GET /api/categories/
    create: POST /api/categories/
    read:   GET /api/categories/{id}/
    update: PUT /api/categories/{id}/
    delete: DELETE /api/categories/{id}/
    tree:   GET /api/categories/tree/
    """
    queryset = CategoryModel.objects.all()
    serializer_class = CategorySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['parent', 'is_active']
    search_fields = ['name']

    @action(detail=False, methods=['get'])
    def tree(self, request):
        """Get full category tree structure.
        
        Returns nested categories:
        Electronics
          ├── Laptop
          ├── Mobile
          ├── Điều hòa
          └── Tủ lạnh
        Thời trang
          ├── Áo
          ├── Quần
          └── Giày dép
        Mỹ phẩm
          ├── Son môi
          └── Kem nền
        """
        root_categories = CategoryModel.objects.filter(
            parent__isnull=True, is_active=True
        ).order_by('sort_order', 'name')
        serializer = CategoryTreeSerializer(root_categories, many=True)
        return Response(serializer.data)
