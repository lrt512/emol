from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = "Ensures at least one superuser exists"

    def handle(self, *args, **options):
        UserModel = get_user_model()

        if UserModel.objects.filter(is_superuser=True).exists():
            self.stdout.write(self.style.SUCCESS("A superuser already exists."))
            return

        self.stdout.write(self.style.WARNING("No superuser found. Creating one..."))
        while True:
            email = input("Enter superuser email: ")
            if not email:
                self.stdout.write(
                    self.style.ERROR("Email is required. Please try again.")
                )
                continue
            try:
                user = UserModel.objects.create_superuser(
                    email=email, is_superuser=True, is_staff=True
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Superuser {user.email} was created successfully."
                    )
                )
                break
            except ValueError as e:
                self.stdout.write(self.style.ERROR(f"Error: {e}"))
