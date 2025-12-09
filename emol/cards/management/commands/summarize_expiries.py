import logging
from collections import defaultdict
from datetime import date, timedelta

from cards.models import Card, Waiver
from cards.utility.time import DATE_FORMAT, today
from django.conf import settings
from django.core.management.base import BaseCommand

logger = logging.getLogger("cards")


class Command(BaseCommand):
    help = "Summarize upcoming card and waiver expiries for planning purposes."

    def add_arguments(self, parser):
        parser.add_argument(
            "--period",
            choices=["day", "week", "month"],
            default="week",
            help="Time period to check for expiries (default: week)",
        )
        parser.add_argument(
            "--days",
            type=int,
            help="Custom number of days to check (overrides --period)",
        )
        parser.add_argument(
            "--detailed",
            action="store_true",
            help="Show detailed listing of each expiring item",
        )

    def handle(self, *args, **options):
        period = options["period"]
        custom_days = options["days"]
        detailed = options["detailed"]

        # Determine the number of days to check
        if custom_days:
            days_ahead = custom_days
            period_name = f"{custom_days} days"
        else:
            period_mapping = {
                "day": 1,
                "week": 7,
                "month": 30,
            }
            days_ahead = period_mapping[period]
            period_name = f"next {period}"

        end_date = today() + timedelta(days=days_ahead)

        logger.info(
            f"Expiry summary for {period_name} ({today().strftime(DATE_FORMAT)} to {end_date.strftime(DATE_FORMAT)})"
        )

        # Query for expiring cards
        expiring_cards = (
            Card.objects.filter(
                date_issued__lte=today() - timedelta(days=365 * 2 - days_ahead),
                date_issued__gt=today() - timedelta(days=365 * 2),
            )
            .select_related("combatant", "discipline")
            .order_by("date_issued")
        )

        # Query for expiring waivers
        expiring_waivers = (
            Waiver.objects.filter(
                date_signed__lte=today() - timedelta(days=365 * 7 - days_ahead),
                date_signed__gt=today() - timedelta(days=365 * 7),
            )
            .select_related("combatant")
            .order_by("date_signed")
        )

        # Summary counts
        card_count = expiring_cards.count()
        waiver_count = expiring_waivers.count()
        total_count = card_count + waiver_count

        logger.info(
            f"📊 SUMMARY: {total_count} total expiries ({card_count} cards, {waiver_count} waivers)"
        )

        if total_count == 0:
            logger.info("✅ No expiries found in the specified period")
            return

        # Card summary by discipline
        if card_count > 0:
            logger.info(f"🃏 CARDS EXPIRING: {card_count} cards")

            discipline_counts = defaultdict(int)
            cards_by_date = defaultdict(list)

            for card in expiring_cards:
                discipline_counts[card.discipline.name] += 1
                expiry_date = card.expiration_date
                cards_by_date[expiry_date].append(card)

            # Show discipline breakdown
            for discipline, count in sorted(discipline_counts.items()):
                logger.info(f"   {discipline}: {count} cards")

            # Show detailed listing if requested
            if detailed:
                logger.info("📋 Detailed card expiries:")
                for expiry_date in sorted(cards_by_date.keys()):
                    logger.info(f"   {expiry_date.strftime(DATE_FORMAT)}:")
                    for card in cards_by_date[expiry_date]:
                        logger.info(
                            f"      {card.combatant.sca_name} - {card.discipline.name}"
                        )

        # Waiver summary
        if waiver_count > 0:
            logger.info(f"📋 WAIVERS EXPIRING: {waiver_count} waivers")

            if detailed:
                waivers_by_date = defaultdict(list)
                for waiver in expiring_waivers:
                    expiry_date = waiver.expiration_date
                    waivers_by_date[expiry_date].append(waiver)

                logger.info("📋 Detailed waiver expiries:")
                for expiry_date in sorted(waivers_by_date.keys()):
                    logger.info(f"   {expiry_date.strftime(DATE_FORMAT)}:")
                    for waiver in waivers_by_date[expiry_date]:
                        logger.info(f"      {waiver.combatant.sca_name}")

        # Reminder scheduling information
        reminder_days = getattr(settings, "REMINDER_DAYS", [60, 30, 14, 0])
        logger.info(f"📅 REMINDER SCHEDULE: {reminder_days} days before expiry")

        if total_count > 0:
            # Calculate how many reminders would be sent during this period
            reminder_count = 0
            reminder_breakdown = defaultdict(
                lambda: {"total": 0, "card": 0, "waiver": 0}
            )

            # Check card reminders
            for card in expiring_cards:
                days_until_expiry = (card.expiration_date - today()).days
                for reminder_day in reminder_days:
                    days_until_reminder = days_until_expiry - reminder_day
                    # If reminder would be sent within our analysis period
                    if 0 <= days_until_reminder <= days_ahead:
                        reminder_count += 1
                        reminder_breakdown[reminder_day]["total"] += 1
                        reminder_breakdown[reminder_day]["card"] += 1

            # Check waiver reminders
            for waiver in expiring_waivers:
                days_until_expiry = (waiver.expiration_date - today()).days
                for reminder_day in reminder_days:
                    days_until_reminder = days_until_expiry - reminder_day
                    # If reminder would be sent within our analysis period
                    if 0 <= days_until_reminder <= days_ahead:
                        reminder_count += 1
                        reminder_breakdown[reminder_day]["total"] += 1
                        reminder_breakdown[reminder_day]["waiver"] += 1

            if reminder_count > 0:
                logger.info(
                    f"📬 REMINDERS TO SEND: {reminder_count} total reminders during {period_name}"
                )
                for reminder_day in sorted(reminder_breakdown.keys()):
                    counts = reminder_breakdown[reminder_day]
                    total = counts["total"]
                    card_count = counts["card"]
                    waiver_count = counts["waiver"]
                    logger.info(
                        f"   {reminder_day}-day reminders: {total} (waiver: {waiver_count}, card: {card_count})"
                    )
            else:
                logger.info(
                    f"📬 REMINDERS TO SEND: No reminders scheduled during {period_name}"
                )

        logger.info(f"✅ Expiry summary complete for {period_name}")
