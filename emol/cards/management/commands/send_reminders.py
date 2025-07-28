import logging
from datetime import date

from cards.models.reminder import Reminder
from cards.utility.time import DATE_FORMAT
from django.core.management.base import BaseCommand
from django.utils import timezone

logger = logging.getLogger("cards")


class Command(BaseCommand):
    help = "Send reminders for expiring Cards and Waivers."

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would happen without actually sending emails or deleting reminders',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        now = timezone.now()

        if dry_run:
            logger.info("🔍 DRY RUN MODE - No emails will be sent, no reminders will be deleted")

        # 1. Clean up ALL orphaned reminders first
        all_reminders = Reminder.objects.all().select_related('content_type')
        orphaned_reminders = [r for r in all_reminders if r.content_object is None]

        if orphaned_reminders:
            orphaned_count = len(orphaned_reminders)
            if dry_run:
                logger.info(f"🗑️  Would clean up {orphaned_count} orphaned reminders")
                for orphaned in orphaned_reminders:
                    logger.info(f"   - Would delete orphaned reminder ID {orphaned.id} (object_id={orphaned.object_id})")
            else:
                logger.info(f"Cleaning up {orphaned_count} orphaned reminders...")
                count, _ = Reminder.objects.filter(id__in=[r.id for r in orphaned_reminders]).delete()
                logger.info(f"Deleted {count} orphaned reminders.")

        # 2. Process DUE reminders
        due_reminders = Reminder.objects.filter(due_date__lte=now)
        due_count = due_reminders.count()

        logger.info(
            f"Processing reminders for {date.today().strftime(DATE_FORMAT)}: Found {due_count} due reminders to process."
        )

        if due_count == 0:
            return

        # Group reminders by content object to avoid sending multiple reminders for the same item
        content_object_reminders = {}
        for reminder in due_reminders:
            # This check is technically redundant given the cleanup above, but safe to keep
            if reminder.content_object is None:
                continue
            key = (reminder.content_type_id, reminder.object_id)
            if key not in content_object_reminders:
                content_object_reminders[key] = []
            content_object_reminders[key].append(reminder)

        sent_count = 0
        expired_count = 0

        for key, reminders_group in content_object_reminders.items():
            # Sort by days_to_expiry (ascending) - most urgent first
            reminders_group.sort(key=lambda r: r.days_to_expiry)

            # The first reminder in the sorted group is the most urgent one to send
            most_urgent = reminders_group[0]

            if most_urgent.should_send_email:
                if not dry_run:
                    most_urgent.send_email()
                sent_count += 1
                logger.info(
                    f"{'[DRY RUN] Would send' if dry_run else 'Sent'} {most_urgent.days_to_expiry}-day "
                    f"reminder for {most_urgent.content_object}"
                )
            else:
                logger.info(
                    f"{'[DRY RUN] Would skip' if dry_run else 'Skipped'} {most_urgent.days_to_expiry}-day "
                    f"reminder for {most_urgent.content_object} (email criteria not met)."
                )

            # 3. Clean up ALL reminders for this object now that the most urgent has been handled
            if dry_run:
                # In a dry run, just calculate what would be deleted.
                # All reminders in the group would be deleted.
                expired_count += len(reminders_group)
                logger.info(f"   - [DRY RUN] Would delete {len(reminders_group)} reminders for this object.")
            else:
                content_type_id, object_id = key
                deleted_count, _ = Reminder.objects.filter(
                    content_type_id=content_type_id, object_id=object_id
                ).delete()
                expired_count += deleted_count
                logger.info(f"   - Cleaned up {deleted_count} reminders for this object.")

        if dry_run:
            logger.info(f"🔍 DRY RUN SUMMARY: Would send {sent_count} reminders and delete {expired_count} total reminders.")
        else:
            logger.info(f"✅ Sent {sent_count} reminders and cleaned up {expired_count} total reminders.")
