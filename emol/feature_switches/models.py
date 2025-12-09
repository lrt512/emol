"""Feature switch model for controlled feature rollout."""

from django.db import models


class FeatureSwitch(models.Model):
    """A feature switch for controlling feature availability.

    Attributes:
        name: Unique slug-like identifier for the switch (e.g., 'pin_required')
        description: Human-readable description of what this switch controls
        enabled: Whether the feature is currently enabled
        created_at: When this switch was created
        updated_at: When this switch was last modified
    """

    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Unique identifier for this switch (e.g., 'pin_required')",
    )
    description = models.TextField(
        blank=True,
        help_text="Description of what this feature switch controls",
    )
    enabled = models.BooleanField(
        default=False,
        help_text="Whether this feature is currently enabled",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Feature Switch"
        verbose_name_plural = "Feature Switches"

    def __str__(self) -> str:
        status = "ON" if self.enabled else "OFF"
        return f"{self.name} [{status}]"
