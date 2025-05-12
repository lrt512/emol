# -*- coding: utf-8 -*-
from django.contrib import admin

from cards.models.authorization import Authorization

__all__ = ["AuthorizationAdmin"]


@admin.register(Authorization)
class AuthorizationAdmin(admin.ModelAdmin):
    """Django Admin for Authorization model"""

    readonly_fields = ["slug"]
