# -*- coding: utf-8 -*-
from django.contrib import admin

from cards.models import UpdateCode

__all__ = ["UpdateCodeAdmin"]


@admin.register(UpdateCode)
class UpdateCodeAdmin(admin.ModelAdmin):
    """Django Admin for UpdateCode model"""

    readonly_fields = ["combatant", "code", "expires_at"]
