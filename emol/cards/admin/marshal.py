# -*- coding: utf-8 -*-
from django.contrib import admin

from cards.models.marshal import Marshal

__all__ = ["MarshalAdmin"]


@admin.register(Marshal)
class MarshalAdmin(admin.ModelAdmin):
    """Django Admin for Marshal model"""

    pass
