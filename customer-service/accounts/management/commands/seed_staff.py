from django.core.management.base import BaseCommand

from accounts.models import CustomUser


class Command(BaseCommand):
    help = "Seed a default staff/admin user"

    def add_arguments(self, parser):
        parser.add_argument("--username", type=str, default="staff1")
        parser.add_argument("--password", type=str, default="password123")
        parser.add_argument("--admin", action="store_true", help="Create as superuser (admin)")

    def handle(self, *args, **options):
        username = options["username"]
        password = options["password"]
        make_admin = bool(options.get("admin"))

        user = CustomUser.objects.filter(username=username).first()
        if user:
            # Ensure password/role stays consistent across reruns
            user.set_password(password)
            if make_admin:
                user.is_staff = True
                user.is_superuser = True
            else:
                user.is_staff = True
                user.is_superuser = False
            user.save(update_fields=["password", "is_staff", "is_superuser"])
            self.stdout.write(self.style.SUCCESS(f"Updated user: {username} (admin={make_admin})"))
        else:
            if make_admin:
                user = CustomUser.objects.create_superuser(
                    username=username,
                    email=f"{username}@example.com",
                    password=password,
                )
            else:
                user = CustomUser.objects.create_user(
                    username=username,
                    email=f"{username}@example.com",
                    password=password,
                    is_staff=True,
                )
            self.stdout.write(self.style.SUCCESS(f"Created user: {username} (admin={make_admin})"))

