"""One-time code model for various verification purposes."""

from __future__ import annotations

import uuid
from typing import cast
from urllib.parse import urljoin

from cards.utility.time import utc_tomorrow
from django.conf import settings
from django.db import models
from django.utils import timezone


class OneTimeCodeQuerySet(models.QuerySet):
    def _get_combatant_id(self) -> int:
        """Extract combatant_id from queryset filter.

        When called through a RelatedManager (e.g., combatant.one_time_codes),
        the queryset is filtered to a single combatant_id. This method extracts
        that value from the queryset's where clause.

        Returns:
            The combatant_id from the queryset filter

        Raises:
            ValueError: If combatant_id cannot be determined from filter
        """
        where = self.query.where

        def extract_value(rhs):
            """Extract integer value from RHS node."""
            if isinstance(rhs, (int, str)):
                return int(rhs)
            if hasattr(rhs, "value"):
                return int(rhs.value)
            if hasattr(rhs, "__int__"):
                return int(rhs)
            try:
                return int(rhs)
            except (TypeError, ValueError):
                return None

        def get_field_name(lhs):
            """Extract field name from LHS node."""
            if hasattr(lhs, "target") and hasattr(lhs.target, "name"):
                return lhs.target.name
            if hasattr(lhs, "col"):
                col = lhs.col
                if hasattr(col, "target") and hasattr(col.target, "name"):
                    return col.target.name
                if hasattr(col, "field") and hasattr(col.field, "name"):
                    return col.field.name
            if hasattr(lhs, "output_field") and hasattr(lhs.output_field, "name"):
                return lhs.output_field.name
            return None

        def find_combatant_id(node):
            """Recursively search for combatant_id filter."""
            if hasattr(node, "children"):
                for child in node.children:
                    result = find_combatant_id(child)
                    if result is not None:
                        return result

            if hasattr(node, "lhs") and hasattr(node, "rhs"):
                field_name = get_field_name(node.lhs)
                if field_name == "combatant_id":
                    value = extract_value(node.rhs)
                    if value is not None:
                        return value

            return None

        combatant_id = find_combatant_id(where)
        if combatant_id is not None:
            return int(combatant_id)

        try:
            compiler = self.query.get_compiler(using=self.db)
            _sql, params = compiler.as_sql()
            if params:
                for param in params:
                    if isinstance(param, int) and param > 0:
                        return int(param)
        except Exception:
            pass

        try:
            distinct_combatant_ids = list(
                self.values_list("combatant_id", flat=True).distinct()
            )
            if len(distinct_combatant_ids) == 1:
                return int(distinct_combatant_ids[0])
        except Exception:
            pass

        raise ValueError(
            "combatant_id not found in queryset filter. "
            "This method must be called through a RelatedManager "
            "(e.g., combatant.one_time_codes.create_pin_reset_code())"
        )

    def create_info_update_code(self) -> OneTimeCode:
        """Create a one-time code for combatant info update."""
        url_template = urljoin(settings.BASE_URL, "/self-serve-update/{code}")
        combatant_id = self._get_combatant_id()
        return cast(
            OneTimeCode,
            self.model.objects.create(
                combatant_id=combatant_id,
                url_template=url_template,
            ),
        )

    def create_pin_setup_code(self) -> OneTimeCode:
        """Create a one-time code for initial PIN setup."""
        url_template = urljoin(settings.BASE_URL, "/pin/setup/{code}")
        combatant_id = self._get_combatant_id()
        return cast(
            OneTimeCode,
            self.model.objects.create(
                combatant_id=combatant_id,
                url_template=url_template,
            ),
        )

    def create_pin_reset_code(self) -> OneTimeCode:
        """Create a one-time code for PIN reset."""
        url_template = urljoin(settings.BASE_URL, "/pin/reset/{code}")
        combatant_id = self._get_combatant_id()
        return cast(
            OneTimeCode,
            self.model.objects.create(
                combatant_id=combatant_id,
                url_template=url_template,
            ),
        )


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

    objects = OneTimeCodeQuerySet.as_manager()
    combatant = models.ForeignKey(
        "Combatant",
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
