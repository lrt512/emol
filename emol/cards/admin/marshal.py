# -*- coding: utf-8 -*-
from cards.models.marshal import Marshal
from django.contrib import admin

__all__ = ["MarshalAdmin"]


@admin.register(Marshal)
class MarshalAdmin(admin.ModelAdmin):
    """Django Admin for Marshal model"""
