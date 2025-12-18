# -*- coding: utf-8 -*-
from cards.models.waiver import Waiver
from django.contrib import admin

__all__ = ["WaiverAdmin"]


@admin.register(Waiver)
class WaiverAdmin(admin.ModelAdmin):
    """Django Admin for Waiver model"""
