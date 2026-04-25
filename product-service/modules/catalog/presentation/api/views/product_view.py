"""
Product API Views
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from modules.catalog.infrastructure.models.product_model import ProductModel
from modules.catalog.infrastructure.models.variant_model import VariantModel
from modules.catalog.presentation.api.serializers.product_serializer import (
    ProductListSerializer,
    ProductDetailSerializer,
    VariantSerializer,
)


class ProductViewSet(viewsets.ModelViewSet):
    """
    Product ViewSet - Full CRUD with filtering and search.
    
    list:   GET /api/products/
    create: POST /api/products/
    read:   GET /api/products/{id}/
    update: PUT /api/products/{id}/
    delete: DELETE /api/products/{id}/
    """
    queryset = ProductModel.objects.select_related('category', 'brand', 'product_type').all()
    lookup_field = 'slug'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'brand', 'product_type', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'price', 'created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return ProductListSerializer
        return ProductDetailSerializer

    @action(detail=False, methods=['get'], url_path='by-category/(?P<category_id>[^/.]+)')
    def by_category(self, request, category_id=None):
        """Get products by category (including sub-categories)."""
        products = ProductModel.objects.active().by_category(int(category_id))
        products = products.select_related('category', 'brand')
        serializer = ProductListSerializer(products, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='filter-by-attributes')
    def filter_by_attributes(self, request):
        """Filter products by JSON attributes.
        
        Usage: /api/products/filter-by-attributes/?ram=16GB&cpu=i7
        """
        # Extract attribute filters from query params (exclude known params)
        known_params = {'page', 'page_size', 'ordering', 'search', 'category', 'brand',
                        'min_price', 'max_price', 'format'}
        attr_filters = {
            k: v for k, v in request.query_params.items()
            if k not in known_params
        }

        products = ProductModel.objects.active()
        
        if 'category' in request.query_params:
            products = products.by_category(int(request.query_params['category']))
        
        if attr_filters:
            products = products.by_attributes(attr_filters)

        min_price = request.query_params.get('min_price')
        max_price = request.query_params.get('max_price')
        if min_price or max_price:
            products = products.by_price_range(
                float(min_price) if min_price else None,
                float(max_price) if max_price else None,
            )

        products = products.select_related('category', 'brand')
        serializer = ProductListSerializer(products, many=True)
        return Response(serializer.data)


class VariantViewSet(viewsets.ModelViewSet):
    """
    Variant ViewSet - CRUD for product variants.
    
    list:   GET /api/variants/
    create: POST /api/variants/
    read:   GET /api/variants/{id}/
    update: PUT /api/variants/{id}/
    delete: DELETE /api/variants/{id}/
    """
    queryset = VariantModel.objects.select_related('product').all()
    serializer_class = VariantSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['product', 'is_active']
    search_fields = ['name', 'sku']
