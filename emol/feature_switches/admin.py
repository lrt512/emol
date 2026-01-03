"""Admin configuration for feature switches."""

from django.contrib import admin
from feature_switches.helpers import clear_cache
from feature_switches.models import FeatureSwitch


@admin.register(FeatureSwitch)
class FeatureSwitchAdmin(admin.ModelAdmin):
    """Admin interface for FeatureSwitch model."""

    list_display = ["name", "access_mode", "description", "updated_at"]
    list_filter = ["access_mode"]
    search_fields = ["name", "description"]
    readonly_fields = ["created_at", "updated_at"]
    ordering = ["name"]
    filter_horizontal = ["allowed_users"]

    fieldsets = [
        (
            None,
            {
                "fields": ["name", "description", "access_mode", "allowed_users"],
            },
        ),
        (
            "Timestamps",
            {"fields": ["created_at", "updated_at"], "classes": ["collapse"]},
        ),
    ]

    def save_model(self, request, obj, form, change):
        """Clear cache when a switch is saved."""
        super().save_model(request, obj, form, change)
        clear_cache(obj.name)

    def delete_model(self, request, obj):
        """Clear cache when a switch is deleted."""
        switch_name = obj.name
        super().delete_model(request, obj)
        clear_cache(switch_name)
