"""
Seed Categories - Management command to populate category tree.

Category tree (from whiteboard):
  Electronics (Điện tử)
    ├── Laptop
    ├── Mobile (Điện thoại)
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
from django.core.management.base import BaseCommand
from modules.catalog.infrastructure.models.category_model import CategoryModel
from shared.utils import generate_slug


CATEGORY_TREE = {
    'Electronics': {
        'description': 'Thiết bị điện tử',
        'children': [
            {'name': 'Laptop', 'description': 'Máy tính xách tay'},
            {'name': 'Mobile', 'description': 'Điện thoại di động'},
            {'name': 'Điều hòa', 'description': 'Máy điều hòa không khí'},
            {'name': 'Tủ lạnh', 'description': 'Tủ lạnh gia đình'},
        ]
    },
    'Thời trang': {
        'description': 'Quần áo và phụ kiện thời trang',
        'children': [
            {'name': 'Áo', 'description': 'Áo thời trang nam nữ'},
            {'name': 'Quần', 'description': 'Quần thời trang nam nữ'},
            {'name': 'Giày dép', 'description': 'Giày dép thời trang'},
        ]
    },
    'Mỹ phẩm': {
        'description': 'Sản phẩm làm đẹp và chăm sóc da',
        'children': [
            {'name': 'Son môi', 'description': 'Son môi các loại'},
            {'name': 'Kem nền', 'description': 'Kem nền trang điểm'},
        ]
    },
}


class Command(BaseCommand):
    help = 'Seed categories with tree structure'

    def handle(self, *args, **options):
        self.stdout.write('Seeding categories...')
        
        order = 0
        for parent_name, data in CATEGORY_TREE.items():
            parent, created = CategoryModel.objects.get_or_create(
                slug=generate_slug(parent_name),
                defaults={
                    'name': parent_name,
                    'description': data['description'],
                    'parent': None,
                    'sort_order': order,
                }
            )
            status = 'Created' if created else 'Already exists'
            self.stdout.write(f'  {status}: {parent_name}')

            for child_order, child in enumerate(data['children']):
                child_cat, child_created = CategoryModel.objects.get_or_create(
                    slug=generate_slug(child['name']),
                    defaults={
                        'name': child['name'],
                        'description': child['description'],
                        'parent': parent,
                        'sort_order': child_order,
                    }
                )
                c_status = 'Created' if child_created else 'Already exists'
                self.stdout.write(f'    {c_status}: {child["name"]}')

            order += 1

        total = CategoryModel.objects.count()
        self.stdout.write(self.style.SUCCESS(f'Done! Total categories: {total}'))
