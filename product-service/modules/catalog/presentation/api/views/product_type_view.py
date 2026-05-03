"""
ProductType API Views
"""
from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend

from modules.catalog.infrastructure.models.product_type_model import ProductTypeModel
from modules.catalog.presentation.api.serializers.product_type_serializer import ProductTypeSerializer


class ProductTypeViewSet(viewsets.ModelViewSet):
    """
    ProductType ViewSet - CRUD.

    list:   GET /api/product-types/
    create: POST /api/product-types/
    read:   GET /api/product-types/{id}/
    update: PUT /api/product-types/{id}/
    delete: DELETE /api/product-types/{id}/
    """

    queryset = ProductTypeModel.objects.all()
    serializer_class = ProductTypeSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = []
    search_fields = ["name"]

