from django.core.management.base import BaseCommand
from accounts.models import CustomUser

class Command(BaseCommand):
    help = 'Seed sample customers (default: customer1..customer500)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete existing customer* users before seeding',
        )
        parser.add_argument(
            '--count',
            type=int,
            default=500,
            help='Number of customers to seed (default: 500)',
        )

    def handle(self, *args, **options):
        count = options['count']
        if count < 1:
            self.stdout.write(self.style.ERROR('Count must be >= 1'))
            return

        if options.get('clear'):
            deleted, _ = CustomUser.objects.filter(username__startswith='customer').delete()
            self.stdout.write(f'Cleared existing seeded customers (deleted objects: {deleted})')

        self.stdout.write(f'Seeding customers customer1..customer{count}...')
        created_count = 0
        existing_count = 0

        for i in range(1, count + 1):
            username = f'customer{i}'
            email = f'customer{i}@example.com'
            if not CustomUser.objects.filter(username=username).exists():
                CustomUser.objects.create_user(
                    username=username,
                    email=email,
                    password='password123',
                    first_name='Customer',
                    last_name=str(i)
                )
                created_count += 1
                self.stdout.write(f'Created customer: {username}')
            else:
                existing_count += 1
                self.stdout.write(f'Customer already exists: {username}')

        self.stdout.write(self.style.SUCCESS(
            f'Done! Created: {created_count}, Existing: {existing_count}, Total Customers: {CustomUser.objects.count()}'
        ))
