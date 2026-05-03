"""
API URL Configuration for Catalog module.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from modules.catalog.presentation.api.views.product_view import ProductViewSet, VariantViewSet
from modules.catalog.presentation.api.views.category_view import CategoryViewSet
from modules.catalog.presentation.api.views.brand_view import BrandViewSet
from modules.catalog.presentation.api.views.product_type_view import ProductTypeViewSet

router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'brands', BrandViewSet, basename='brand')
router.register(r'product-types', ProductTypeViewSet, basename='product-type')
router.register(r'variants', VariantViewSet, basename='variant')

urlpatterns = [
    path('', include(router.urls)),
]
