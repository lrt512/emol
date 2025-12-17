"""Ensure all active cards and waivers have proper reminders."""

from cards.models import Card, Reminder, Waiver
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    """Check and fix reminder hygiene for cards and waivers."""

    help = "Ensure all active cards and waivers have reminders, report anomalies"

    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            "--fix",
            action="store_true",
            help="Create missing reminders (default is report only)",
        )

    def handle(self, *args, **options):
        """Execute the command."""
        fix = options["fix"]
        today = timezone.now().date()
        reminder_days = getattr(settings, "REMINDER_DAYS", [60, 30, 14, 0])

        self.stdout.write("Reminder hygiene check (%s)" % today)
        self.stdout.write("Expected reminder days: %s" % reminder_days)
        self.stdout.write("")

        card_ct = ContentType.objects.get_for_model(Card)
        waiver_ct = ContentType.objects.get_for_model(Waiver)

        issues_found = 0

        issues_found += self._check_model(
            Card, card_ct, "cards", reminder_days, today, fix
        )
        issues_found += self._check_model(
            Waiver, waiver_ct, "waivers", reminder_days, today, fix
        )
        issues_found += self._check_orphaned_reminders()

        self.stdout.write("")
        if issues_found == 0:
            self.stdout.write(self.style.SUCCESS("✓ No issues found"))
        else:
            action = "Fixed" if fix else "Found"
            self.stdout.write(self.style.WARNING(f"⚠ {action} {issues_found} issues"))
            if not fix:
                self.stdout.write("Run with --fix to create missing reminders")

    def _check_model(
        self,
        model_class,
        content_type,
        label: str,
        reminder_days: list[int],
        today,
        fix: bool,
    ) -> int:
        """Check a model for missing reminders.

        Args:
            model_class: The model class to check (Card or Waiver)
            content_type: ContentType for the model
            label: Human-readable label for output
            reminder_days: List of days before expiry for reminders
            today: Current date
            fix: Whether to create missing reminders

        Returns:
            Number of issues found/fixed

        """
        issues = 0
        active_items = [
            item for item in model_class.objects.all() if item.expiration_date > today
        ]

        self.stdout.write("Checking %s active %s..." % (len(active_items), label))

        for item in active_items:
            existing = set(
                Reminder.objects.filter(
                    content_type=content_type, object_id=item.id
                ).values_list("days_to_expiry", flat=True)
            )

            expected = set(reminder_days)
            missing = expected - existing

            if missing:
                issues += 1
                self.stdout.write(
                    self.style.WARNING(
                        "  %s: missing reminders for days %s" % (item, sorted(missing))
                    )
                )
                if fix:
                    Reminder.create_or_update_reminders(item)
                    self.stdout.write(self.style.SUCCESS("    → Created reminders"))

        return issues

    def _check_orphaned_reminders(self) -> int:
        """Check for orphaned reminders.

        Returns:
            Number of orphaned reminders found

        """
        self.stdout.write("Checking for orphaned reminders...")

        all_reminders = Reminder.objects.all().select_related("content_type")
        orphaned = [r for r in all_reminders if r.content_object is None]

        if orphaned:
            self.stdout.write(
                self.style.WARNING("  Found %s orphaned reminders" % len(orphaned))
            )
            for r in orphaned[:10]:
                self.stdout.write(
                    "    - Reminder ID %s (object_id=%s)" % (r.id, r.object_id)
                )
            if len(orphaned) > 10:
                self.stdout.write("    ... and %s more" % (len(orphaned) - 10))
            self.stdout.write("  (These will be cleaned up by send_reminders)")

        return len(orphaned)
