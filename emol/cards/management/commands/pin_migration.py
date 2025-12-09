"""Management command for PIN migration campaign.

This command handles sending PIN setup emails to combatants who don't have
a PIN set. It supports three stages:
- initial: First notification
- reminder: Follow-up after one week
- final: Final notice after two weeks
"""

import logging
from datetime import timedelta

from cards.mail import send_pin_migration_email
from cards.models import Combatant, OneTimeCode
from django.core.management.base import BaseCommand
from django.utils import timezone

logger = logging.getLogger("cards")


class Command(BaseCommand):
    """Send PIN setup emails to combatants without PINs."""

    help = "Send PIN setup emails to combatants as part of the migration campaign."

    def add_arguments(self, parser):
        parser.add_argument(
            "--stage",
            type=str,
            choices=["initial", "reminder", "final"],
            default="initial",
            help="The stage of the migration campaign (initial, reminder, or final)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be sent without actually sending emails",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Limit the number of emails to send (useful for testing)",
        )

    def handle(self, *args, **options):
        stage = options["stage"]
        dry_run = options["dry_run"]
        limit = options.get("limit")

        combatants = Combatant.objects.filter(
            accepted_privacy_policy=True,
            pin_hash__isnull=True,
        )

        total = combatants.count()
        self.stdout.write(f"Found {total} combatants without PINs")

        if limit:
            combatants = combatants[:limit]
            self.stdout.write(f"Limited to {limit} combatants")

        sent_count = 0
        error_count = 0

        for combatant in combatants:
            if dry_run:
                self.stdout.write(f"Would send {stage} email to: {combatant.email}")
                sent_count += 1
                continue

            try:
                one_time_code = OneTimeCode.create_for_pin_setup(combatant)
                send_pin_migration_email(combatant, one_time_code, stage=stage)
                sent_count += 1
                logger.info(f"Sent {stage} PIN migration email to {combatant.email}")
            except Exception as e:
                error_count += 1
                logger.error(f"Failed to send email to {combatant.email}: {e}")
                self.stderr.write(f"Error sending to {combatant.email}: {e}")

        self.stdout.write(
            self.style.SUCCESS(
                f"{'Would send' if dry_run else 'Sent'} {sent_count} {stage} emails"
            )
        )
        if error_count:
            self.stdout.write(self.style.ERROR(f"Errors: {error_count}"))
