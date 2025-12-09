"""Seed a default privacy policy for development."""

from cards.models import PrivacyPolicy
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Create a default privacy policy if none exists."""

    help = "Create a default privacy policy for development"

    def handle(self, *args, **options):
        """Execute the command."""
        if PrivacyPolicy.objects.exists():
            self.stdout.write(self.style.SUCCESS("Privacy policy already exists"))
            return

        policy_text = """## What We Collect

We collect only the information necessary to manage your authorization card:

- Name and SCA name
- Contact email
- Authorization and warrant records
- Card expiration dates

## How We Use It

Your information is used solely to:

- Issue and manage authorization cards
- Send expiration reminders
- Verify authorizations at events

## Data Retention

Records are retained while your card is active and for a reasonable period after expiration.

## Your Rights

Contact the Kingdom Earl Marshal to request access to or deletion of your data.
"""

        PrivacyPolicy.objects.create(text=policy_text)
        self.stdout.write(self.style.SUCCESS("Privacy policy created"))
