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

    def add_arguments(self, parser):
        parser.add_argument(
            "--debug",
            action="store_true",
            help="Show detailed debug information",
        )

    def handle(self, *args, **options):
        debug = options["debug"]
        now = timezone.now()
        today_str = date.today().strftime(DATE_FORMAT)
        purge_cutoff = now - timedelta(days=PURGE_AFTER_DAYS)

        if debug:
            logger.debug("Clean up OneTimeCodes - Debug mode enabled")
            logger.debug("Current time: %s", now)
            logger.debug("Purge cutoff (older than %s days): %s", PURGE_AFTER_DAYS, purge_cutoff)
            total_codes = OneTimeCode.objects.count()
            logger.debug("Total OneTimeCodes in database: %s", total_codes)

        # Clean up OneTimeCode entries (expired OR consumed)
        expired_one_time_codes = OneTimeCode.objects.filter(expires_at__lte=now)
        consumed_one_time_codes = OneTimeCode.objects.filter(consumed=True)

        expired_count = expired_one_time_codes.count()
        consumed_count = consumed_one_time_codes.count()

        if debug:
            logger.debug("Expired codes (expires_at <= %s): %s", now, expired_count)
            logger.debug("Consumed codes: %s", consumed_count)
            if expired_count > 0:
                for code in expired_one_time_codes[:5]:
                    logger.debug(
                        "  Expired code: ID=%s, created_at=%s, expires_at=%s, consumed=%s",
                        code.id,
                        code.created_at,
                        code.expires_at,
                        code.consumed,
                    )
                if expired_count > 5:
                    logger.debug("  ... and %s more expired codes", expired_count - 5)
            if consumed_count > 0:
                for code in consumed_one_time_codes[:5]:
                    logger.debug(
                        "  Consumed code: ID=%s, created_at=%s, expires_at=%s",
                        code.id,
                        code.created_at,
                        code.expires_at,
                    )
                if consumed_count > 5:
                    logger.debug("  ... and %s more consumed codes", consumed_count - 5)

        if expired_count > 0:
            logger.info(
                "Clean up OneTimeCodes (%s): Found %s expired",
                today_str,
                expired_count,
            )
            expired_one_time_codes.delete()

        if consumed_count > 0:
            logger.info(
                "Clean up OneTimeCodes (%s): Found %s consumed",
                today_str,
                consumed_count,
            )
            consumed_one_time_codes.delete()

        # Purge old codes (older than PURGE_AFTER_DAYS) regardless of status
        old_codes = OneTimeCode.objects.filter(created_at__lt=purge_cutoff)
        old_count = old_codes.count()
        if debug:
            logger.debug(
                "Old codes (created_at < %s): %s", purge_cutoff, old_count
            )
            if old_count > 0:
                for code in old_codes[:5]:
                    logger.debug(
                        "  Old code: ID=%s, created_at=%s, expires_at=%s, consumed=%s",
                        code.id,
                        code.created_at,
                        code.expires_at,
                        code.consumed,
                    )
                if old_count > 5:
                    logger.debug("  ... and %s more old codes", old_count - 5)

        if old_count > 0:
            logger.info(
                "Purge old OneTimeCodes (%s): Found %s older than %s days",
                today_str,
                old_count,
                PURGE_AFTER_DAYS,
            )
            old_codes.delete()

        total = expired_count + consumed_count + old_count
        if total == 0:
            logger.info("Clean up codes (%s): No codes to clean up", today_str)
        elif debug:
            logger.debug(
                "Total codes cleaned up: %s (expired: %s, consumed: %s, old: %s)",
                total,
                expired_count,
                consumed_count,
                old_count,
            )
