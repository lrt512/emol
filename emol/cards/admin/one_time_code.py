"""Admin configuration for OneTimeCode model."""

from cards.models import OneTimeCode
from django.contrib import admin


@admin.register(OneTimeCode)
class OneTimeCodeAdmin(admin.ModelAdmin):
    """Admin interface for OneTimeCode model."""

    list_display = [
        "combatant",
        "code_preview",
        "consumed",
        "expires_at",
        "created_at",
    ]
    list_filter = ["consumed", "created_at"]
    search_fields = ["combatant__email", "combatant__sca_name"]
    readonly_fields = ["code", "created_at", "consumed_at"]
    raw_id_fields = ["combatant"]
    ordering = ["-created_at"]

    fieldsets = [
        (None, {"fields": ["combatant", "code", "url_template"]}),
        ("Status", {"fields": ["consumed", "consumed_at", "expires_at"]}),
        ("Timestamps", {"fields": ["created_at"], "classes": ["collapse"]}),
    ]

    def code_preview(self, obj) -> str:
        """Show truncated code for display."""
        code_str = str(obj.code)
        return f"{code_str[:4]}...{code_str[-4:]}"

    code_preview.short_description = "Code"
