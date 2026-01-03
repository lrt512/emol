"""Feature switch model for controlled feature rollout."""

from django.db import models

ACCESS_MODE_DISABLED = "disabled"
ACCESS_MODE_GLOBAL = "global"
ACCESS_MODE_LIST = "list"

ACCESS_MODE_CHOICES = [
    (ACCESS_MODE_DISABLED, "Disabled - Off for everyone"),
    (ACCESS_MODE_GLOBAL, "Global - Enabled for everyone"),
    (ACCESS_MODE_LIST, "List - Enabled only for selected users"),
]


class FeatureSwitch(models.Model):
    """A feature switch for controlling feature availability.

    Attributes:
        name: Unique slug-like identifier for the switch (e.g., 'pin_required')
        description: Human-readable description of what this switch controls
        access_mode: How the feature is accessed (disabled/global/list)
        allowed_users: Combatants who can access the feature when mode is 'list'
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
    access_mode = models.CharField(
        max_length=20,
        choices=ACCESS_MODE_CHOICES,
        default=ACCESS_MODE_DISABLED,
        help_text="Control who can access this feature",
    )
    allowed_users = models.ManyToManyField(
        "cards.Combatant",
        blank=True,
        help_text="Combatants who can access this feature when mode is 'List'",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Feature Switch"
        verbose_name_plural = "Feature Switches"

    def __str__(self) -> str:
        mode_display = dict(ACCESS_MODE_CHOICES).get(self.access_mode, self.access_mode)
        return f"{self.name} [{mode_display}]"
