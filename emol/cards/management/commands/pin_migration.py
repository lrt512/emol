"""Management command for PIN migration campaign.

This command handles sending PIN setup emails to combatants who don't have
a PIN set. It supports three stages:
- initial: First notification
- reminder: Follow-up after one week
- final: Final notice after two weeks
"""

import logging

from cards.mail import send_pin_migration_email
from cards.models import Combatant
from django.core.management.base import BaseCommand

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
        self.stdout.write("Found %s combatants without PINs" % total)

        if limit:
            combatants = combatants[:limit]
            self.stdout.write("Limited to %s combatants" % limit)

        sent_count = 0
        error_count = 0

        for combatant in combatants:
            if dry_run:
                self.stdout.write(
                    "Would send %s email to: %s" % (stage, combatant.email)
                )
                sent_count += 1
                continue

            try:
                one_time_code = combatant.one_time_codes.create_pin_reset_code()
                send_pin_migration_email(combatant, one_time_code, stage=stage)
                sent_count += 1
                logger.info("Sent %s PIN migration email to %s", stage, combatant.email)
            except Exception as e:
                error_count += 1
                logger.error("Failed to send email to %s: %s", combatant.email, e)
                self.stderr.write("Error sending to %s: %s" % (combatant.email, e))

        action = "Would send" if dry_run else "Sent"
        self.stdout.write(
            self.style.SUCCESS("%s %s %s emails" % (action, sent_count, stage))
        )
        if error_count:
            self.stdout.write(self.style.ERROR("Errors: %s", error_count))
