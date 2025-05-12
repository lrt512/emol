# -*- coding: utf-8 -*-
from django.contrib import admin

from cards.models.discipline import Discipline


@admin.register(Discipline)
class DisciplineAdmin(admin.ModelAdmin):
    """Django Admin for Discipline model"""

    readonly_fields = ["slug"]
