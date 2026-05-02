"""
Product API Views
"""
from django.db import transaction
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
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

    def get_queryset(self):
        qs = super().get_queryset()
        ids_param = self.request.query_params.get('ids')
        if self.action == 'list' and ids_param:
            id_list = []
            for part in ids_param.split(','):
                part = part.strip()
                if not part:
                    continue
                try:
                    id_list.append(int(part))
                except ValueError:
                    continue
            if id_list:
                return qs.filter(id__in=id_list)
        return qs

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

    @action(
        detail=False,
        methods=['post'],
        url_path='adjust-stock',
        permission_classes=[AllowAny],
    )
    def adjust_stock(self, request):
        """Adjust product stock by delta (negative decreases, positive increases)."""
        product_id = request.data.get('product_id')
        delta = request.data.get('delta')
        if product_id is None or delta is None:
            return Response(
                {'detail': 'product_id and delta are required'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            product_id = int(product_id)
            delta = int(delta)
        except (TypeError, ValueError):
            return Response(
                {'detail': 'product_id and delta must be integers'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        with transaction.atomic():
            product = (
                ProductModel.objects.select_for_update()
                .filter(id=product_id)
                .first()
            )
            if not product:
                return Response({'detail': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
            new_qty = int(product.stock_quantity) + delta
            if new_qty < 0:
                return Response(
                    {'detail': 'Insufficient stock', 'stock_quantity': product.stock_quantity},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            product.stock_quantity = new_qty
            product.save(update_fields=['stock_quantity', 'updated_at'])
        return Response(
            {'id': product.id, 'stock_quantity': product.stock_quantity},
            status=status.HTTP_200_OK,
        )


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
