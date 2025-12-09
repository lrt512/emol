import logging
from datetime import date, timedelta

from cards.models import OneTimeCode
from cards.utility.time import DATE_FORMAT
from django.core.management.base import BaseCommand
from django.utils import timezone

logger = logging.getLogger("cards")

PURGE_AFTER_DAYS = 7


class Command(BaseCommand):
    """Clean up expired, consumed, and old one-time codes."""

    help = "Clean up expired, consumed, and old one-time codes."

    def handle(self, *args, **options):
        now = timezone.now()
        today_str = date.today().strftime(DATE_FORMAT)
        purge_cutoff = now - timedelta(days=PURGE_AFTER_DAYS)

        # Clean up OneTimeCode entries (expired OR consumed)
        expired_one_time_codes = OneTimeCode.objects.filter(expires_at__lte=now)
        consumed_one_time_codes = OneTimeCode.objects.filter(consumed=True)

        expired_count = expired_one_time_codes.count()
        consumed_count = consumed_one_time_codes.count()

        if expired_count > 0:
            logger.info(
                f"Clean up OneTimeCodes ({today_str}): Found {expired_count} expired"
            )
            expired_one_time_codes.delete()

        if consumed_count > 0:
            logger.info(
                f"Clean up OneTimeCodes ({today_str}): Found {consumed_count} consumed"
            )
            consumed_one_time_codes.delete()

        # Purge old codes (older than PURGE_AFTER_DAYS) regardless of status
        old_codes = OneTimeCode.objects.filter(created_at__lt=purge_cutoff)
        old_count = old_codes.count()
        if old_count > 0:
            logger.info(
                f"Purge old OneTimeCodes ({today_str}): Found {old_count} older than {PURGE_AFTER_DAYS} days"
            )
            old_codes.delete()

        total = expired_count + consumed_count + old_count
        if total == 0:
            logger.info(f"Clean up codes ({today_str}): No codes to clean up")
