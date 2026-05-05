"""
Seed Categories - Management command to populate category tree.

This project is an electronics store. Seed only electronics categories.
"""
from django.core.management.base import BaseCommand
from modules.catalog.infrastructure.models.category_model import CategoryModel
from shared.utils import generate_slug


CATEGORY_TREE = {
    'Electronics': {
        'description': 'Thiết bị điện tử',
        'children': [
            {'name': 'Laptop', 'slug': 'laptop', 'description': 'Máy tính xách tay'},
            {'name': 'Điện thoại', 'slug': 'dien-thoai', 'description': 'Điện thoại di động'},
            {'name': 'Phụ kiện', 'slug': 'phu-kien', 'description': 'Phụ kiện điện tử'},
            {'name': 'Đồng hồ', 'slug': 'dong-ho', 'description': 'Đồng hồ thông minh'},
        ],
    },
}


class Command(BaseCommand):
    help = 'Seed categories with tree structure'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing categories before seeding',
        )

    def handle(self, *args, **options):
        self.stdout.write('Seeding categories...')

        if options.get('clear'):
            self.stdout.write('Clearing existing categories...')
            CategoryModel.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Cleared!'))
        
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
                    slug=child.get('slug') or generate_slug(child['name']),
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
