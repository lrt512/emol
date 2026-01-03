"""Ensure all active cards and waivers have proper reminders."""

from datetime import timedelta

from cards.models import Card, Reminder, Waiver
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.db.models import QuerySet
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
        parser.add_argument(
            "--debug",
            action="store_true",
            help="Show detailed debug information",
        )

    def handle(self, *args, **options):
        """Execute the command."""
        fix = options["fix"]
        debug = options["debug"]
        today = timezone.now().date()
        reminder_days = getattr(settings, "REMINDER_DAYS", [60, 30, 14, 0])

        self.stdout.write("Reminder hygiene check (%s)" % today)
        self.stdout.write("Expected reminder days: %s" % reminder_days)
        if debug:
            self.stdout.write("[DEBUG] Fix mode: %s" % fix)
        self.stdout.write("")

        card_ct = ContentType.objects.get_for_model(Card)
        waiver_ct = ContentType.objects.get_for_model(Waiver)

        issues_found = 0

        issues_found += self._check_model(
            Card, card_ct, "cards", reminder_days, today, fix, debug
        )
        issues_found += self._check_model(
            Waiver, waiver_ct, "waivers", reminder_days, today, fix, debug
        )
        issues_found += self._check_orphaned_reminders(debug)

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
        debug: bool,
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
            if debug:
                self.stdout.write(
                    "[DEBUG] Checking %s (ID: %s, expires: %s)"
                    % (item, item.id, item.expiration_date)
                )

            existing = set(
                Reminder.objects.filter(
                    content_type=content_type, object_id=item.id
                ).values_list("days_to_expiry", flat=True)
            )

            if debug:
                self.stdout.write(
                    "[DEBUG]   Existing reminders: %s" % sorted(existing)
                )

            expected = set(reminder_days)
            missing = expected - existing

            if debug:
                self.stdout.write(
                    "[DEBUG]   Expected reminders: %s" % sorted(expected)
                )
                self.stdout.write(
                    "[DEBUG]   Missing reminders: %s" % sorted(missing)
                )

            if not missing:
                if debug:
                    self.stdout.write("[DEBUG]   ✓ All reminders present")
                continue

            if not existing:
                issues += 1
                self.stdout.write(
                    self.style.WARNING(
                        "  %s: missing all reminders (creating all)" % item
                    )
                )
                if fix:
                    Reminder.create_or_update_reminders(item)
                    self.stdout.write(self.style.SUCCESS("    → Created all reminders"))
                continue

            expiration_date = item.expiration_date
            days_until_expiry = (expiration_date - today).days

            if debug:
                self.stdout.write(
                    "[DEBUG]   Days until expiry: %s" % days_until_expiry
                )

            missing_that_should_exist = []
            for days in sorted(missing, reverse=True):
                should_exist = days_until_expiry > days
                if debug:
                    self.stdout.write(
                        "[DEBUG]   %s-day reminder: days_until_expiry (%s) > days (%s) = %s"
                        % (days, days_until_expiry, days, should_exist)
                    )
                if should_exist:
                    missing_that_should_exist.append(days)

            if missing_that_should_exist:
                issues += 1
                self.stdout.write(
                    self.style.WARNING(
                        "  %s: missing reminders for days %s (still >%s days from expiry)"
                        % (
                            item,
                            sorted(missing_that_should_exist),
                            min(missing_that_should_exist),
                        )
                    )
                )
                if fix:
                    for days in missing_that_should_exist:
                        due_date = expiration_date - timedelta(days=days)
                        if debug:
                            self.stdout.write(
                                "[DEBUG]   Creating %s-day reminder with due_date: %s"
                                % (days, due_date)
                            )
                        Reminder.objects.create(
                            content_type=content_type,
                            object_id=item.id,
                            days_to_expiry=days,
                            due_date=due_date,
                        )
                    self.stdout.write(
                        self.style.SUCCESS(
                            "    → Created %s missing reminder(s)"
                            % len(missing_that_should_exist)
                        )
                    )
            elif debug:
                self.stdout.write(
                    "[DEBUG]   ✓ Missing reminders were already sent (not recreating)"
                )

        return issues

    def _check_orphaned_reminders(self, debug: bool = False) -> int:
        """Check for orphaned reminders.

        Args:
            debug: Whether to show debug output

        Returns:
            Number of orphaned reminders found

        """
        self.stdout.write("Checking for orphaned reminders...")

        reminders: QuerySet[Reminder, Reminder] = Reminder.objects.all().select_related(
            "content_type"
        )
        if debug:
            self.stdout.write(
                "[DEBUG] Checking %s total reminders for orphaned status"
                % reminders.count()
            )

        orphaned = [r for r in reminders if r.content_object is None]

        if orphaned:
            self.stdout.write(
                self.style.WARNING("  Found %s orphaned reminders" % len(orphaned))
            )
            for r in orphaned[:10]:
                self.stdout.write(
                    "    - Reminder ID %s (object_id=%s)" % (r.id, r.object_id)
                )
                if debug:
                    self.stdout.write(
                        "[DEBUG]     Content type: %s, Days to expiry: %s, Due date: %s"
                        % (r.content_type, r.days_to_expiry, r.due_date)
                    )
            if len(orphaned) > 10:
                self.stdout.write("    ... and %s more" % (len(orphaned) - 10))
            self.stdout.write("  (These will be cleaned up by send_reminders)")
        elif debug:
            self.stdout.write("[DEBUG]   ✓ No orphaned reminders found")

        return len(orphaned)
