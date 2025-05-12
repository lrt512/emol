import logging
from datetime import date

from django.core.management.base import BaseCommand
from django.utils import timezone

from cards.models.reminder import Reminder
from cards.utility.time import DATE_FORMAT

logger = logging.getLogger("cards")


class Command(BaseCommand):
    help = "Send reminders for expiring Cards and Waivers."

    def handle(self, *args, **options):
        now = timezone.now()
        due_reminders = Reminder.objects.filter(due_date__lte=now)
        count = due_reminders.count()
        logger.info(
            f"Reminders for {date.today().strftime(DATE_FORMAT)}: Found {count} to send"
        )

        if count == 0:
            return

        for reminder in due_reminders:
            if reminder.should_send_email:
                if reminder.send_email():
                    reminder.delete()

        logger.info("Reminders sent")
