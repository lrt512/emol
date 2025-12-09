# -*- coding: utf-8 -*-
"""Combatant database model.

Combatants are the centerpiece of eMoL. A combatant is someone who has
authorizations in a discipline and needs an authorization card to show for them.
"""

import logging
import re
from collections import namedtuple
from datetime import date, timedelta
from urllib.parse import urljoin
from uuid import uuid4

from cards.mail import send_card_url, send_privacy_policy
from cards.utility.names import generate_name
from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.db import models
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone

from .permissioned_db_fields import (PermissionedCharField,
                                     PermissionedDateField,
                                     PermissionedIntegerField)

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

    # PIN authentication fields
    pin_hash = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        help_text="Hashed PIN for card access verification",
    )
    pin_failed_attempts = models.IntegerField(
        default=0,
        help_text="Number of consecutive failed PIN attempts",
    )
    pin_locked_until = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Datetime when PIN lockout expires",
    )

    # Data columns that are not encrypted
    email = models.CharField(max_length=255, db_index=True)
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
        help_text="Region code (state/province)",
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

    @property
    def privacy_policy_code(self):
        """Generate a privacy policy code from the combatant's SCA name.
        
        Returns the first letter of each word in the SCA name.
        
        Returns:
            String containing initials
        """
        if not self.sca_name:
            return ""
        
        words = self.sca_name.split()
        return "".join(word[0] for word in words if word)

    @property
    def waiver_date(self):
        """Get the waiver date signed.
        
        Returns:
            Date when waiver was signed, or None if no waiver exists
        """
        try:
            return self.waiver.date_signed
        except AttributeError:
            return None
    
    @waiver_date.setter
    def waiver_date(self, value):
        """Set the waiver date signed.
        
        Creates a new waiver if one doesn't exist, or updates the existing one.
        
        Args:
            value: Date when waiver was signed
        """
        from .waiver import Waiver  # Import here to avoid circular imports
        
        try:
            # Update existing waiver
            self.waiver.date_signed = value
            self.waiver.save()
        except AttributeError:
            # Create new waiver
            Waiver.objects.create(combatant=self, date_signed=value)

    @property 
    def waiver_duration(self):
        """Get the waiver validity duration.
        
        Returns:
            Timedelta representing actual waiver validity period
        """
        if self.waiver_date and self.waiver_expires:
            return self.waiver_expires - self.waiver_date
        else:
            # Default 7-year duration if no waiver exists
            return timedelta(days=365 * 7)
    
    @property
    def waiver_expires(self):
        """Get the waiver expiration date.
        
        Returns:
            Date when waiver expires, or None if no waiver exists
        """
        try:
            return self.waiver.expiration_date
        except AttributeError:
            return None

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
        return send_card_url(self)

    # PIN Authentication Methods

    PIN_LOCKOUT_DURATION = timedelta(minutes=15)
    PIN_MAX_ATTEMPTS = 5

    @property
    def has_pin(self) -> bool:
        """Check if combatant has set a PIN.

        Returns:
            True if PIN is set, False otherwise
        """
        return self.pin_hash is not None and len(self.pin_hash) > 0

    @property
    def is_locked_out(self) -> bool:
        """Check if combatant is currently locked out due to failed PIN attempts.

        Returns:
            True if locked out, False otherwise
        """
        if self.pin_locked_until is None:
            return False
        return timezone.now() < self.pin_locked_until

    def set_pin(self, raw_pin: str) -> bool:
        """Set the combatant's PIN.

        Validates that the PIN is 4-6 numeric digits and stores it hashed.

        Args:
            raw_pin: The plain text PIN to set

        Returns:
            True if PIN was set successfully

        Raises:
            ValueError: If PIN is not 4-6 numeric digits
        """
        if not raw_pin or not re.match(r"^\d{4,6}$", raw_pin):
            raise ValueError("PIN must be 4-6 numeric digits")

        self.pin_hash = make_password(raw_pin)
        self.pin_failed_attempts = 0
        self.pin_locked_until = None
        self.save(update_fields=["pin_hash", "pin_failed_attempts", "pin_locked_until"])
        return True

    def check_pin(self, raw_pin: str) -> bool:
        """Check if the provided PIN matches the stored PIN.

        Handles lockout logic: increments failed attempts on failure,
        locks account after PIN_MAX_ATTEMPTS failures, clears attempts on success.

        Args:
            raw_pin: The plain text PIN to check

        Returns:
            True if PIN matches, False otherwise (including when locked out)
        """
        if self.is_locked_out:
            logger.warning(f"PIN check attempted for locked out combatant {self.email}")
            return False

        if not self.has_pin:
            logger.warning(f"PIN check attempted for combatant {self.email} with no PIN set")
            return False

        if check_password(raw_pin, self.pin_hash):
            if self.pin_failed_attempts > 0:
                self.pin_failed_attempts = 0
                self.save(update_fields=["pin_failed_attempts"])
            return True

        self.pin_failed_attempts += 1
        if self.pin_failed_attempts >= self.PIN_MAX_ATTEMPTS:
            self.pin_locked_until = timezone.now() + self.PIN_LOCKOUT_DURATION
            logger.warning(f"Combatant {self.email} locked out after {self.pin_failed_attempts} failed PIN attempts")
            self._send_lockout_notification()

        self.save(update_fields=["pin_failed_attempts", "pin_locked_until"])
        return False

    def clear_lockout(self) -> None:
        """Clear the lockout state for this combatant.

        Resets failed attempts and lockout timestamp.
        """
        self.pin_failed_attempts = 0
        self.pin_locked_until = None
        self.save(update_fields=["pin_failed_attempts", "pin_locked_until"])

    def clear_pin(self) -> None:
        """Clear the PIN for this combatant (for PIN reset flow).

        Clears the PIN hash and lockout state.
        """
        self.pin_hash = None
        self.pin_failed_attempts = 0
        self.pin_locked_until = None
        self.save(update_fields=["pin_hash", "pin_failed_attempts", "pin_locked_until"])

    def initiate_pin_reset(self) -> "OneTimeCode":
        """Initiate a PIN reset for this combatant.

        Clears the existing PIN and creates a one-time code for setting a new PIN.

        Returns:
            OneTimeCode instance for the PIN reset flow
        """
        from .one_time_code import OneTimeCode

        self.clear_pin()
        return OneTimeCode.create_for_pin_reset(self)

    def _send_lockout_notification(self) -> None:
        """Send an email notification that the account has been locked out."""
        from cards.mail import send_pin_lockout_notification

        try:
            send_pin_lockout_notification(self)
        except Exception as e:
            logger.error(f"Failed to send lockout notification to {self.email}: {e}")


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
