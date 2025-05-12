# -*- coding: utf-8 -*-
"""Combatant database model.

Combatants are the centerpiece of eMoL. A combatant is someone who has
authorizations in a discipline and needs an authorization card to show for them.
"""

import logging
from collections import namedtuple
from datetime import date
from urllib.parse import urljoin
from uuid import uuid4

from django.conf import settings
from django.db import models
from django.dispatch import receiver
from django.urls import reverse

from cards.mail import send_card_url, send_privacy_policy
from cards.utility.names import generate_name

from .card import Card
from .discipline import Discipline
from .permissioned_db_fields import (
    PermissionedCharField,
    PermissionedDateField,
    PermissionedIntegerField,
)

__all__ = ["Combatant"]

logger = logging.getLogger("cards")


class Combatant(models.Model):
    """A combatant.

    Attributes:
        id: Identity PK for the table
        uuid: A reference to the record with no intrinsic meaning
        card_id: A slug-like identifier for URLs
        last_update: Timestamp for last update of this record
        email: The combatant's email address
        sca_name: The combatant's SCA name

    Backrefs:
        cards_set: The combatant's authorization cards
        waiver: The combatant's waiver on file
    """

    class Meta:
        indexes = [
            models.Index(fields=["uuid"]),
            models.Index(fields=["card_id"]),
        ]

    uuid = models.UUIDField(default=uuid4, null=False, editable=False)

    # Friendly identifier for the combatant's cards
    card_id = models.CharField(max_length=255)
    last_update = models.DateTimeField(auto_now=True)

    accepted_privacy_policy = models.BooleanField(default=False)
    privacy_acceptance_code = models.CharField(max_length=32, unique=True, null=True)

    # Data columns that are not encrypted
    email = models.CharField(max_length=255, unique=True)
    sca_name = models.CharField(max_length=255, null=True, blank=True)

    # Data fields for creating combatants
    # Anything marked True is required
    _combatant_info = {
        "email": True,
        "sca_name": False,
        "legal_name": True,
        "phone": True,
        "address1": True,
        "address2": False,
        "city": True,
        "province": True,
        "postal_code": True,
        "dob": False,
        "member_expiry": False,
        "member_number": False,
    }

    # Encrypted fields
    legal_name = PermissionedCharField(
        max_length=255,
        null=False,
        permissions=["read_combatant_info", "write_combatant_info"],
    )
    phone = PermissionedCharField(
        max_length=255,
        null=False,
        permissions=["read_combatant_info", "write_combatant_info"],
    )
    address1 = PermissionedCharField(
        max_length=255,
        null=False,
        permissions=["read_combatant_info", "write_combatant_info"],
    )
    address2 = PermissionedCharField(
        max_length=255,
        null=True,
        blank=True,
        permissions=["read_combatant_info", "write_combatant_info"],
    )
    city = PermissionedCharField(
        max_length=255,
        null=False,
        permissions=["read_combatant_info", "write_combatant_info"],
    )
    province = PermissionedCharField(
        max_length=2,
        null=False,
        default="ON",
        permissions=["read_combatant_info", "write_combatant_info"],
    )
    postal_code = PermissionedCharField(
        max_length=7,
        null=False,
        permissions=["read_combatant_info", "write_combatant_info"],
    )
    dob = PermissionedDateField(
        max_length=255,
        null=True,
        blank=True,
        permissions=["read_combatant_info", "write_combatant_info"],
    )
    member_number = PermissionedIntegerField(
        null=True,
        blank=True,
        permissions=["read_combatant_info", "write_combatant_info"],
    )
    member_expiry = PermissionedDateField(
        null=True,
        blank=True,
        permissions=["read_combatant_info", "write_combatant_info"],
    )

    def __str__(self):
        return f"<Combatant: {self.email} ({self.name})>"

    @property
    def name(self):
        """Get a combatant's name.

        Return the SCA name if defined, otherwise the legal name

        Returns:
            A name

        """
        return self.sca_name or self.legal_name

    # named tuple for return values from update_info
    UpdateInfoReturn = namedtuple("UpdateInfoReturn", ["sca_name", "email"])

    @property
    def card_url(self):
        """Card URL for this combatant.

        Compute the URL for this combatant's card from the combatant.view_card
        route and the combatant's card_id

        Returns:
            The URL as a string

        Raises:
            PrivacyPolicyNotAccepted if the combatant has not yet done so

        """
        if not self.accepted_privacy_policy:
            logger.error(f"Attempt to get card URL for {self} (privacy not accepted)")
            raise Exception("no")

        if self.card_id is None or len(self.card_id) == 0:
            logger.error(
                (
                    f"Attempt to get card_id for {self} but card ID has not been allocated"
                )
            )
            raise Exception("no")

        return urljoin(
            settings.BASE_URL, reverse("combatant-card", args=[self.card_id])
        )

    def accept_privacy_policy(self):
        """Combatant accepted the privacy policy"""
        self.accepted_privacy_policy = True
        self.privacy_acceptance_code = None
        while True:
            card_id = generate_name()
            if not Combatant.objects.filter(card_id=card_id).exists():
                self.card_id = card_id
                break

        self.save()
        send_card_url(self)


def membership_valid(self, on_date=None):
    """Check if the combatant's membership is valid.

    Check the combatant's membership info in the encrypted blob.
    If the membership info is empty, then no. Otherwise, based on the
    membership expiry date

    Args:
        on_date: Optional date to check against, otherwise use today

    Returns:
        Boolean

    """
    return (
        self.member_number is not None
        and self.member_expiry is not None
        and (on_date or date.today()) <= self.member_expiry
    )


@receiver(models.signals.post_save, sender=Combatant)
def send_privacy_policy_email(sender, instance, created, **kwargs):
    if created and not instance.accepted_privacy_policy:
        logger.debug(f"Sending privacy policy email to {instance} ({instance.email})")
        send_privacy_policy(instance)
