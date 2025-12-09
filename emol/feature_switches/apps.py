"""App configuration for feature_switches."""

from django.apps import AppConfig


class FeatureSwitchesConfig(AppConfig):
    """Configuration for the feature_switches app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "feature_switches"
    verbose_name = "Feature Switches"
