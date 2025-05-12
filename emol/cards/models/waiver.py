import logging

from dirtyfields import DirtyFieldsMixin
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from cards.mail import send_waiver_expiry, send_waiver_reminder
from cards.utility.time import DATE_FORMAT, add_years, today

from .reminder import Reminder
from .reminder_mixin import DirtyModelReminderMeta, ReminderMixin

logger = logging.getLogger("cards")


class Waiver(models.Model, DirtyFieldsMixin, ReminderMixin):
    combatant = models.OneToOneField("Combatant", on_delete=models.CASCADE)
    date_signed = models.DateField(null=False, blank=False)

    WAIVER_VALIDITY_YEARS = 7

    def __str__(self) -> str:
        return f"<Waiver: {self.combatant.name} expires {self.expiration_date}"

    @property
    def expiration_date(self):
        """Get the combatant's authorization card expiry date.

        That is, the self.card + CARD_DURATION years

        Returns:
            The card's expiry date as a datetime.date

        """
        return add_years(self.date_signed, 7)

    @property
    def expiration_date_str(self):
        """Return the expiration date as a string"""
        return self.expiration_date.strftime(DATE_FORMAT)

    def send_expiry(self, reminder):
        if not isinstance(reminder.content_object, Waiver):
            logger.error("Reminder %s is not a waiver", reminder)
            return False

        return send_waiver_expiry(reminder)

    def send_reminder(self, reminder):
        if not isinstance(reminder.content_object, Waiver):
            logger.error("Reminder %s is not a waiver", reminder)
            return False

        return send_waiver_reminder(reminder)

    @property
    def expiry_days(self):
        """Number of days until this combatan't waiver expires."""
        return (self.expiration_date - today()).days

    @property
    def is_valid(self) -> bool:
        return self.expiry_days > 0

    @property
    def expiry_or_expired(self):
        """Return the expiration date or EXPIRED"""
        return (
            self.expiration_date.strftime(DATE_FORMAT) if self.is_valid else "EXPIRED"
        )

    def renew(self, date_signed=None):
        """Renew combatant's waiver.

        Args:
            date_signed: Optional waiver date. If not specified, defaults to today

        """
        self.date_signed = date_signed or today()
        self.save()


@receiver(post_save, sender=Waiver)
def update_reminders(sender, instance, created, **kwargs):
    if created:
        Reminder.create_or_update_reminders(instance)
    elif "date_signed" in instance.get_dirty_fields(check_relationship=True):
        Reminder.create_or_update_reminders(instance)
    else:
        logger.debug("Waiver post_save signal ignored")
