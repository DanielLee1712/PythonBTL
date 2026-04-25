"""
Tests for Category model and API.
"""
from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from modules.catalog.infrastructure.models.category_model import CategoryModel


class CategoryTreeTest(TestCase):
    """Test category tree operations."""

    def setUp(self):
        # Create tree matching whiteboard
        self.electronics = CategoryModel.objects.create(
            name='Electronics', slug='electronics', sort_order=0
        )
        self.laptop = CategoryModel.objects.create(
            name='Laptop', slug='laptop', parent=self.electronics, sort_order=0
        )
        self.mobile = CategoryModel.objects.create(
            name='Mobile', slug='mobile', parent=self.electronics, sort_order=1
        )
        self.fashion = CategoryModel.objects.create(
            name='Thời trang', slug='thoi-trang', sort_order=1
        )
        self.ao = CategoryModel.objects.create(
            name='Áo', slug='ao', parent=self.fashion, sort_order=0
        )
        self.cosmetics = CategoryModel.objects.create(
            name='Mỹ phẩm', slug='my-pham', sort_order=2
        )

    def test_root_categories(self):
        roots = CategoryModel.objects.filter(parent__isnull=True)
        self.assertEqual(roots.count(), 3)

    def test_children(self):
        children = self.electronics.children.all()
        self.assertEqual(children.count(), 2)

    def test_full_path(self):
        self.assertEqual(self.laptop.get_full_path(), 'Electronics > Laptop')
        self.assertEqual(self.ao.get_full_path(), 'Thời trang > Áo')

    def test_is_root(self):
        self.assertIsNone(self.electronics.parent)
        self.assertIsNotNone(self.laptop.parent)


class CategoryTreeAPITest(APITestCase):
    """Test category tree API endpoint."""

    def setUp(self):
        self.electronics = CategoryModel.objects.create(
            name='Electronics', slug='electronics'
        )
        CategoryModel.objects.create(
            name='Laptop', slug='laptop', parent=self.electronics
        )
        CategoryModel.objects.create(
            name='Mobile', slug='mobile', parent=self.electronics
        )

    def test_tree_endpoint(self):
        response = self.client.get('/api/categories/tree/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should have 1 root with 2 children
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Electronics')
        self.assertEqual(len(response.data[0]['children']), 2)

    def test_create_category(self):
        data = {'name': 'Gaming', 'parent': self.electronics.id}
        response = self.client.post('/api/categories/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.electronics.children.count(), 3)
