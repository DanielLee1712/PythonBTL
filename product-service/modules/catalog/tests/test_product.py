"""
Tests for Product models and API.
"""
from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from modules.catalog.infrastructure.models.product_model import ProductModel
from modules.catalog.infrastructure.models.category_model import CategoryModel
from modules.catalog.infrastructure.models.brand_model import BrandModel
from modules.catalog.infrastructure.models.variant_model import VariantModel


class ProductModelTest(TestCase):
    """Test Product domain and ORM model."""

    def setUp(self):
        self.category = CategoryModel.objects.create(
            name='Electronics', slug='electronics'
        )
        self.brand = BrandModel.objects.create(
            name='Apple', slug='apple'
        )

    def test_create_product(self):
        product = ProductModel.objects.create(
            name='MacBook Pro',
            slug='macbook-pro',
            price=49990000,
            category=self.category,
            brand=self.brand,
            attributes={'ram': '16GB', 'cpu': 'M3'}
        )
        self.assertEqual(product.name, 'MacBook Pro')
        self.assertEqual(product.attributes['ram'], '16GB')
        self.assertTrue(product.is_active)

    def test_product_json_attributes(self):
        product = ProductModel.objects.create(
            name='Test Product',
            slug='test-product',
            price=1000,
            attributes={'ram': '16GB', 'cpu': 'i7', 'storage': '512GB'}
        )
        # Filter by JSON attribute
        found = ProductModel.objects.filter(attributes__ram='16GB')
        self.assertEqual(found.count(), 1)
        self.assertEqual(found.first().name, 'Test Product')

    def test_product_with_variants(self):
        product = ProductModel.objects.create(
            name='iPhone 15',
            slug='iphone-15',
            price=34990000,
            category=self.category,
            brand=self.brand,
        )
        variant = VariantModel.objects.create(
            product=product,
            sku='IP15-256',
            name='256GB',
            stock=100,
            attributes={'storage': '256GB'}
        )
        self.assertEqual(product.variants.count(), 1)
        self.assertEqual(variant.effective_price, product.price)


class CategoryModelTest(TestCase):
    """Test Category tree structure."""

    def test_category_tree(self):
        parent = CategoryModel.objects.create(
            name='Electronics', slug='electronics'
        )
        child = CategoryModel.objects.create(
            name='Laptop', slug='laptop', parent=parent
        )
        self.assertEqual(child.parent, parent)
        self.assertEqual(parent.children.count(), 1)
        self.assertEqual(child.get_full_path(), 'Electronics > Laptop')


class ProductAPITest(APITestCase):
    """Test Product REST API endpoints."""

    def setUp(self):
        self.category = CategoryModel.objects.create(
            name='Electronics', slug='electronics'
        )
        self.product = ProductModel.objects.create(
            name='Test Product',
            slug='test-product',
            price=1000000,
            category=self.category,
            attributes={'ram': '8GB'}
        )

    def test_list_products(self):
        response = self.client.get('/api/products/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_product_detail(self):
        response = self.client.get(f'/api/products/{self.product.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Product')

    def test_create_product(self):
        data = {
            'name': 'New Product',
            'price': 500000,
            'category': self.category.id,
            'attributes': {'color': 'red'},
        }
        response = self.client.post('/api/products/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ProductModel.objects.count(), 2)

    def test_filter_by_category(self):
        response = self.client.get(f'/api/products/by-category/{self.category.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)


class CategoryAPITest(APITestCase):
    """Test Category REST API endpoints."""

    def setUp(self):
        self.parent = CategoryModel.objects.create(
            name='Electronics', slug='electronics'
        )
        CategoryModel.objects.create(
            name='Laptop', slug='laptop', parent=self.parent
        )

    def test_list_categories(self):
        response = self.client.get('/api/categories/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_category_tree(self):
        response = self.client.get('/api/categories/tree/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # 1 root category
        self.assertEqual(len(response.data[0]['children']), 1)  # 1 child
