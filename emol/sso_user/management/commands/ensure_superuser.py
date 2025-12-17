import os
import sys

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Ensures at least one superuser exists"

    def add_arguments(self, parser):
        parser.add_argument(
            "--email",
            type=str,
            help="Email address for the superuser",
        )
        parser.add_argument(
            "--non-interactive",
            action="store_true",
            help="Run in non-interactive mode (for containers/CI)",
        )

    def handle(self, *args, **options):
        UserModel = get_user_model()

        if UserModel.objects.filter(is_superuser=True).exists():
            self.stdout.write(self.style.SUCCESS("A superuser already exists."))
            return

        self.stdout.write(self.style.WARNING("No superuser found. Creating one..."))

        # Get email from various sources
        email = options.get("email")
        if not email:
            email = os.environ.get("SUPERUSER_EMAIL")

        # Check if we're in non-interactive mode or not connected to a terminal
        non_interactive = options.get("non_interactive") or not sys.stdin.isatty()

        if not email and non_interactive:
            # Use default email for development/containers
            if os.environ.get("EMOL_DEV"):
                email = "admin@emol.com"
                self.stdout.write("Using default development email: %s" % email)
            else:
                self.stdout.write(
                    self.style.ERROR(
                        "No email provided and running in non-interactive mode. "
                        "Use --email argument or SUPERUSER_EMAIL environment variable."
                    )
                )
                return

        # Interactive mode - prompt for email
        while not email:
            try:
                email = input("Enter superuser email: ")
                if not email:
                    self.stdout.write(
                        self.style.ERROR("Email is required. Please try again.")
                    )
                    continue
            except (EOFError, KeyboardInterrupt):
                self.stdout.write(self.style.ERROR("\nOperation cancelled."))
                return

        # Create the superuser
        try:
            user = UserModel.objects.create_superuser(
                email=email, is_superuser=True, is_staff=True
            )
            self.stdout.write(
                self.style.SUCCESS(f"Superuser {user.email} was created successfully.")
            )
        except ValueError as e:
            self.stdout.write(self.style.ERROR(f"Error: {e}"))
