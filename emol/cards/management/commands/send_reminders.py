import logging
from datetime import date

from cards.models.reminder import Reminder
from cards.utility.time import DATE_FORMAT, today
from django.core.management.base import BaseCommand

logger = logging.getLogger("cards")


class Command(BaseCommand):
    help = "Send reminders for expiring Cards and Waivers."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would happen, do not send emails or delete reminders",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        if dry_run:
            logger.info(
                "🔍 DRY RUN MODE - No emails will be sent, no reminders will be deleted"
            )

        # 1. Clean up ALL orphaned reminders first
        all_reminders = Reminder.objects.all().select_related("content_type")
        orphaned_reminders = [r for r in all_reminders if r.content_object is None]

        if orphaned_reminders:
            orphaned_count = len(orphaned_reminders)
            if dry_run:
                logger.info("🗑️  Would clean up %s orphaned reminders", orphaned_count)
                for orphaned in orphaned_reminders:
                    logger.info(
                        "   - Would delete orphaned reminder ID %s (object_id=%s)",
                        orphaned.id,
                        orphaned.object_id,
                    )
            else:
                logger.info("Cleaning up %s orphaned reminders...", orphaned_count)
                count, _ = Reminder.objects.filter(
                    id__in=[r.id for r in orphaned_reminders]
                ).delete()
                logger.info("Deleted %s orphaned reminders.", count)

        # 2. Process DUE reminders
        # Compare against today's date using the same helper used to set due_date
        current_date = today()
        due_reminders = Reminder.objects.filter(due_date__lte=current_date)
        due_count = due_reminders.count()

        logger.info(
            "Processing reminders for %s: Found %s due reminders to process.",
            date.today().strftime(DATE_FORMAT),
            due_count,
        )

        if due_count == 0:
            return

        content_object_reminders = {}
        for reminder in due_reminders:
            if reminder.content_object is None:
                continue
            key = (reminder.content_type_id, reminder.object_id)
            if key not in content_object_reminders:
                content_object_reminders[key] = []
            content_object_reminders[key].append(reminder)

        sent_count = 0
        expired_count = 0

        for key, reminders_group in content_object_reminders.items():
            reminders_group.sort(key=lambda r: r.days_to_expiry)
            most_urgent = reminders_group[0]

            email_sent = False
            if most_urgent.should_send_email:
                if dry_run:
                    email_sent = True
                    logger.info(
                        "[DRY RUN] Would send %s-day reminder for %s",
                        most_urgent.days_to_expiry,
                        most_urgent.content_object,
                    )
                else:
                    email_sent = most_urgent.send_email()
                    if email_sent:
                        logger.info(
                            "Sent %s-day reminder for %s",
                            most_urgent.days_to_expiry,
                            most_urgent.content_object,
                        )
                    else:
                        logger.warning(
                            "Failed to send %s-day reminder for %s",
                            most_urgent.days_to_expiry,
                            most_urgent.content_object,
                        )
                sent_count += 1 if email_sent else 0
            else:
                email_sent = True
                logger.info(
                    "%s %s-day reminder for %s (email criteria not met).",
                    "[DRY RUN] Would skip" if dry_run else "Skipped",
                    most_urgent.days_to_expiry,
                    most_urgent.content_object,
                )

            if not email_sent:
                logger.info("   - Keeping reminders for retry tomorrow.")
                continue

            if dry_run:
                expired_count += len(reminders_group)
                logger.info(
                    "   - [DRY RUN] Would delete %s reminders for this object.",
                    len(reminders_group),
                )
            else:
                content_type_id, object_id = key
                deleted_count, _ = Reminder.objects.filter(
                    content_type_id=content_type_id, object_id=object_id
                ).delete()
                expired_count += deleted_count
                logger.info(
                    "   - Cleaned up %s reminders for this object.",
                    deleted_count,
                )

        if dry_run:
            logger.info(
                "🔍 DRY RUN: Would send %s reminders and delete %s total reminders.",
                sent_count,
                expired_count,
            )
        else:
            logger.info(
                "✅ Sent %s reminders and cleaned up %s total reminders.",
                sent_count,
                expired_count,
            )
