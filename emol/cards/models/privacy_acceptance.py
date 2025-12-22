# -*- coding: utf-8 -*-
"""Model to record combatants' acceptance of the privacy policy."""
import logging
from datetime import datetime
from urllib.parse import urljoin

from cards.mail import send_card_url, send_privacy_policy
from cards.utility.names import generate_name
from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import get_random_string

__all__ = ["PrivacyAcceptance"]

logger = logging.getLogger("cards")


class PrivacyPolicyNotAccepted(Exception):
    pass


class PrivacyAcceptance(models.Model):
    """Record indicating acceptance of the privacy policy.

    When a Combatant record is inserted into the database, the listener
    event creates a matching PrivacyAcceptance record. Any combatant who has
    a PrivacyAcceptance record that is not resolved cannot use the system
    until they accept the privacy policy

    When the combatant accepts the privacy policy, the PrivacyAcceptance record
    is resolved by noting the datetime that the privacy policy was accepted

    If the combatant declines the privacy policy, the Combatant record and the
    related PrivacyAcceptance is deleted from the database and the MoL is
    informed

    Attributes:
        id: Identity PK for the table
        uuid: A reference to the record with no intrinsic meaning
        accepted: Date the combatant accepted the privacy policy
        combatant: One-to-one to the Combatant

    """

    combatant = models.OneToOneField(
        "Combatant", on_delete=models.CASCADE, related_name="privacy_acceptance"
    )
    code = models.CharField(max_length=32, unique=True)
    accepted = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["code"])]

    @classmethod
    def create(cls, combatant, force_new=False):
        if force_new:
            cls.objects.filter(combatant=combatant).delete()

        code = get_random_string(length=32)
        pa = cls.objects.create(combatant=combatant, code=code)
        send_privacy_policy(pa)

    def accept(self):
        self.accepted = timezone.now()
        self.save()
        # send_privacy_policy_accepted(self.combatant)

    def decline(self):
        self.combatant.delete()
        # send_privacy_policy_declined(self.combatant)

    def __str__(self):
        return f"<PrivacyAcceptance: {self.combatant.name}>"

    @property
    def privacy_policy_url(self):
        """Generate the URL for a user to visit to accept the privacy policy.

        Uses the uuid member to uniquely identify this privacy accepted record,
        and through it the combatant.

        Returns:
            String containing the URL

        """
        return urljoin(settings.BASE_URL, reverse("privacy-policy", args=[self.uuid]))

    def resolve(self, accepted):
        if self.accepted is not None:
            logger.warning(
                "Combatant %s already accepted the privacy policy", self.combatant
            )
            return {
                "accepted": True,
                "card_url": self.combatant.card_url,
                "sent_email": False,
            }

        if accepted:
            # Combatant accepted the privacy policy. Note the time of
            # acceptance, generate their card_id and email them the
            # link to their card
            self.accepted = datetime.utcnow()
            self.generate_card_id()
            self.save()

            send_card_url(self.combatant)
            logger.debug("Sent card request email to %s", self.combatant.email)
            return {
                "accepted": True,
                "card_url": self.combatant.card_url,
                "sent_email": True,
            }

        # Combatant declined the privacy policy, delete the Combatant
        # record for them and notify the MoL
        logger.info("Deleting combatant %s", self.combatant)
        self.combatant.delete()
        # TODO: Notify the MoL

        return {"accepted": False}

    def generate_card_id(self):
        """
        Get a generated name and make sure it is unique across Combatant records.
        The given name length is a passthrough value

        This shou

        params:
            length - the maximum number of words in the generated name (default 3)
        """
        if self.combatant.card_id:
            logging.warning("Combatant %s already has a card ID", self.combatant)
            return

        combatant_class = self.combatant.__class__
        while True:
            name = generate_name()
            if not combatant_class.objects.filter(card_id=name).exists():
                break

        logger.debug("Add card_id %s to combatant %s", name, self)
        self.combatant.card_id = name
        self.combatant.save()
