# -*- coding: utf-8 -*-
"""Model an authorization card.

    A card represents a single martial discipline.

    Card
    |
    - Discipline (via discipline_id)
    |
    - Authorizations (Authorization model via CombatantAuthorization)
    |
    - Warrants (Marshal model via Warrant)
    |
    - Card Date (The date auths were renewed, not the expiry date)

    A combatant may hold one card for each discipline they have authorizations
    in. These show up as the `cards` relationship on the Combatant model.
"""

import logging
from uuid import uuid4

from dirtyfields import DirtyFieldsMixin
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from cards.mail import send_card_expiry, send_card_reminder
from cards.utility.named_tuples import NameSlugTuple
from cards.utility.time import DATE_FORMAT, add_years, today

from .authorization import Authorization
from .discipline import Discipline
from .marshal import Marshal
from .reminder import Reminder
from .reminder_mixin import DirtyModelReminderMeta, ReminderMixin

__all__ = ["Card"]

logger = logging.getLogger("cards")


class Card(models.Model, DirtyFieldsMixin, ReminderMixin):
    """Model an authorization card

    Card date is the date that the card was renewed.
    The card_expiry property gives the expiry date

    Attributes:
        id: Primary key in the database
        combatant_id: The combatant's id
        discipline_id: ID of the discipline this card is for
        date_issued: Date this card was last renewed
        authorizations: Authorizations attached to this card
            (Authorization model via CombatantAuthorization)
        warrants: Marshal warrants attached to this card
            (Marshal model via Warrant)

    Properties:
        expiration_date: The card's expiration date
        expiry_days: Number of days until expiry
    """

    class Meta:
        constraints = [
            models.UniqueConstraint(
                name="combatant_card", fields=["combatant", "discipline"]
            )
        ]

    combatant = models.ForeignKey(
        "Combatant", on_delete=models.CASCADE, related_name="cards"
    )
    discipline = models.ForeignKey(Discipline, on_delete=models.CASCADE)
    authorizations = models.ManyToManyField(
        Authorization, through="CombatantAuthorization"
    )
    warrants = models.ManyToManyField(Marshal, through="CombatantWarrant")
    uuid = models.UUIDField(default=uuid4)

    date_issued = models.DateField()

    def __str__(self) -> str:
        return f"<Card: {self.combatant.sca_name}/{self.discipline.name}>"

    @property
    def expiration_date(self):
        """Get the combatant's authorization card expiry date.

        That is, the self.card + CARD_DURATION years

        Returns:
            Card's expiry date as a datetime.date

        """
        return add_years(self.date_issued, 2)

    @property
    def expiration_date_str(self):
        """Return the expiration date as a string"""
        return self.expiration_date.strftime(DATE_FORMAT)

    def send_expiry(self, reminder):
        if not isinstance(reminder.content_object, Card):
            logger.error("Reminder %s is not a card", reminder)
            return False

        return send_card_expiry(reminder)

    def send_reminder(self, reminder):
        if not isinstance(reminder.content_object, Card):
            logger.error("Reminder %s is not a card", reminder)
            return False

        return send_card_reminder(reminder)

    @property
    def expiry_or_expired(self):
        """Return the expiration date or EXPIRED"""
        return (
            self.expiration_date.strftime(DATE_FORMAT) if self.is_valid else "EXPIRED"
        )

    @property
    def is_valid(self) -> bool:
        """Card is not past its expiration date"""
        return self.expiry_days > 0

    @property
    def expiry_days(self):
        """Number of days until this card expires."""
        return (self.expiration_date - today()).days

    def renew(self, renew_date=None):
        """Renew this card with a new card_date"""
        self.date_issued = renew_date or today()
        self.save()

    def has_authorization(self, authorization):
        """Does this card have a given authorization?"""
        try:
            a = Authorization.find(self.discipline, authorization)
            return a in self.authorizations.all()
        except Authorization.DoesNotExist:
            return False

    def has_warrant(self, marshal):
        """Does this card have a given marshal warrant?"""
        try:
            m = Marshal.find(self.discipline, marshal)
            return m in self.warrants.all()
        except Marshal.DoesNotExist:
            return False

    @property
    def card_ordered_authorizations(self):
        """
        Model ordering can be a bit wonky, so let's
        1 - split out into lists of primary and secondary auths
        2 - sort those lists in place on name
        3 - return them combined

        We'll also return NamedTuples rather than objects for convenience
        """
        auths = self.discipline.authorizations.all()
        primary = [
            NameSlugTuple(name=a.name, slug=a.slug) for a in auths if a.is_primary
        ]
        secondary = [
            NameSlugTuple(name=a.name, slug=a.slug) for a in auths if not a.is_primary
        ]
        return sorted(primary, key=lambda x: x.name) + sorted(
            secondary, key=lambda x: x.name
        )

    @property
    def card_ordered_marshals(self):
        """
        Model ordering can be a bit wonky, so let's just sort our marshal types
        alphabetically and return

        We'll also return NamedTuples rather than objects for convenience
        """
        marshals = self.discipline.marshals.all()
        tuples = [NameSlugTuple(name=m.name, slug=m.slug) for m in marshals]
        return tuples

    @property
    def authorizations_list(self):
        """
        Return a list of tuples of authorization names and whether
        or not the authorization is primary.
        """
        return [
            (a.name, a.is_primary) for a in self.authorizations.order_by("name").all()
        ]

    @property
    def warrants_list(self):
        """
        Return a list of tuples of warrant names and whether
        or not the warrant is expired.
        """
        return [
            (w.marshal.name, w.expiry_date < today())
            for w in self.warrants.order_by("marshal__name").all()
        ]


@receiver(post_save, sender=Card)
def update_reminders(sender, instance, created, **kwargs):
    """Manage reminders when the card date is updated"""
    if created:
        Reminder.create_or_update_reminders(instance)
    else:
        if "date_issued" in instance.get_dirty_fields(check_relationship=True):
            Reminder.create_or_update_reminders(instance)
