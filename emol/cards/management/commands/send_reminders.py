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
        due_reminders = Reminder.objects.filter(due_date__lte=now)
        total_count = due_reminders.count()
        
        if dry_run:
            logger.info("🔍 DRY RUN MODE - No emails will be sent, no reminders will be deleted")
        
        # Clean up orphaned reminders (where content_object is None)
        orphaned_reminders = []
        valid_reminders = []
        
        for reminder in due_reminders:
            if reminder.content_object is None:
                orphaned_reminders.append(reminder)
            else:
                valid_reminders.append(reminder)
        
        # Delete orphaned reminders
        if orphaned_reminders:
            orphaned_count = len(orphaned_reminders)
            if dry_run:
                logger.info(f"🗑️  Would clean up {orphaned_count} orphaned reminders")
                for orphaned in orphaned_reminders:
                    logger.info(f"   Would delete orphaned reminder ID {orphaned.id} (object_id={orphaned.object_id})")
            else:
                logger.info(f"Cleaning up {orphaned_count} orphaned reminders")
                for orphaned in orphaned_reminders:
                    orphaned.delete()
        
        valid_count = len(valid_reminders)
        logger.info(
            f"Reminders for {date.today().strftime(DATE_FORMAT)}: Found {total_count} total, {valid_count} valid to process"
        )

        if valid_count == 0:
            return

        # Group reminders by content object to avoid sending multiple reminders for the same item
        content_object_reminders = {}
        for reminder in valid_reminders:
            key = (reminder.content_type.id, reminder.object_id)
            if key not in content_object_reminders:
                content_object_reminders[key] = []
            content_object_reminders[key].append(reminder)
        
        sent_count = 0
        expired_count = 0
        
        for reminders_group in content_object_reminders.values():
            # Sort by days_to_expiry (ascending) - most urgent first regardless of REMINDER_DAYS values
            # e.g., [0, 14, 30, 60] or [0, 7, 21, 45, 90] - always send the lowest number (most urgent)
            reminders_group.sort(key=lambda r: r.days_to_expiry)
            
            # Send only the most urgent reminder
            most_urgent = reminders_group[0]
            
            if dry_run:
                # Dry run logging - show what would happen
                if most_urgent.should_send_email:
                    logger.info(f"📧 Would send {most_urgent.days_to_expiry}-day reminder for {most_urgent.content_object}")
                    sent_count += 1
                else:
                    logger.info(f"⏭️  Would skip {most_urgent.days_to_expiry}-day reminder for {most_urgent.content_object} (email criteria not met)")
                
                # Show what older reminders would be deleted
                older_reminders = reminders_group[1:]
                for older_reminder in older_reminders:
                    logger.info(f"🗑️  Would expire older {older_reminder.days_to_expiry}-day reminder for {older_reminder.content_object}")
                    expired_count += 1
                    
            else:
                # Actual execution
                if most_urgent.should_send_email:
                    most_urgent.send_email()
                    sent_count += 1
                    logger.info(f"Sent {most_urgent.days_to_expiry}-day reminder for {most_urgent.content_object}")
                
                # Clean up the older, less urgent reminders for this content object
                older_reminders = reminders_group[1:]  # All except the first (most urgent)
                for older_reminder in older_reminders:
                    logger.info(f"Expiring older {older_reminder.days_to_expiry}-day reminder for {older_reminder.content_object}")
                    older_reminder.delete()
                    expired_count += 1

        if dry_run:
            logger.info(f"🔍 DRY RUN SUMMARY: Would send {sent_count} reminders, would expire {expired_count} older reminders")
        else:
            logger.info(f"Sent {sent_count} reminders, expired {expired_count} older reminders")
