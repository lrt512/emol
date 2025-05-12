# -*- coding: utf-8 -*-
from django.contrib import admin

from cards.models.waiver import Waiver

__all__ = ["WaiverAdmin"]


@admin.register(Waiver)
class WaiverAdmin(admin.ModelAdmin):
    """Django Admin for Waiver model"""

    pass
