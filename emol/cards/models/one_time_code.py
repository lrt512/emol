"""One-time code model for various verification purposes."""

import uuid
from urllib.parse import urljoin

from cards.utility.time import utc_tomorrow
from django.conf import settings
from django.db import models
from django.utils import timezone

from .combatant import Combatant


class OneTimeCode(models.Model):
    """A one-time use code for verification purposes.

    Used for info updates, PIN setup, PIN reset, and other verification flows.
    The url_template field contains a URL with {code} placeholder that gets
    substituted with the actual code value.

    Attributes:
        combatant: The combatant this code is associated with
        code: The unique UUID code
        url_template: URL template with {code} placeholder
        expires_at: When this code expires
        consumed: Whether this code has been used
        consumed_at: When this code was used (if consumed)
        created_at: When this code was created
    """

    combatant = models.ForeignKey(
        Combatant,
        on_delete=models.CASCADE,
        related_name="one_time_codes",
    )
    code = models.UUIDField(default=uuid.uuid4, unique=True)
    url_template = models.CharField(
        max_length=500,
        help_text="URL template with {code} placeholder, e.g., '/update/{code}/'",
    )
    expires_at = models.DateTimeField(default=utc_tomorrow)
    consumed = models.BooleanField(default=False)
    consumed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "One-Time Code"
        verbose_name_plural = "One-Time Codes"

    def __str__(self) -> str:
        email = self.combatant.email
        code_str = f"{str(self.code)[:4]}...{str(self.code)[-4:]}"
        expires_at_str = self.expires_at.astimezone(
            timezone.get_current_timezone()
        ).strftime("%Y-%m-%d %H:%M")
        if self.consumed:
            status = "USED"
        elif timezone.now() >= self.expires_at:
            status = "EXPIRED"
        else:
            status = "ACTIVE"
        return f"<OneTimeCode: {email} ({code_str}) {expires_at_str} [{status}]>"

    @property
    def url(self) -> str:
        """The resolved URL with code substituted.

        Returns:
            Full URL with the code value substituted into the template
        """
        return self.url_template.format(code=self.code)

    @property
    def is_valid(self) -> bool:
        """Check if this code is still valid (not consumed and not expired).

        Returns:
            True if the code can still be used
        """
        if self.consumed:
            return False
        return timezone.now() < self.expires_at

    def consume(self) -> bool:
        """Mark this code as consumed.

        Returns:
            True if successfully consumed, False if already consumed or expired
        """
        if not self.is_valid:
            return False
        self.consumed = True
        self.consumed_at = timezone.now()
        self.save(update_fields=["consumed", "consumed_at"])
        return True

    @classmethod
    def create_for_info_update(cls, combatant: Combatant) -> "OneTimeCode":
        """Create a one-time code for combatant info update.

        Args:
            combatant: The combatant requesting the update

        Returns:
            New OneTimeCode instance
        """
        url_template = urljoin(settings.BASE_URL, "/self-serve-update/{code}")
        return cls.objects.create(
            combatant=combatant,
            url_template=url_template,
        )

    @classmethod
    def create_for_pin_setup(cls, combatant: Combatant) -> "OneTimeCode":
        """Create a one-time code for initial PIN setup.

        Args:
            combatant: The combatant setting up their PIN

        Returns:
            New OneTimeCode instance
        """
        url_template = urljoin(settings.BASE_URL, "/pin/setup/{code}")
        return cls.objects.create(
            combatant=combatant,
            url_template=url_template,
        )

    @classmethod
    def create_for_pin_reset(cls, combatant: Combatant) -> "OneTimeCode":
        """Create a one-time code for PIN reset.

        Args:
            combatant: The combatant resetting their PIN

        Returns:
            New OneTimeCode instance
        """
        url_template = urljoin(settings.BASE_URL, "/pin/reset/{code}")
        return cls.objects.create(
            combatant=combatant,
            url_template=url_template,
        )
