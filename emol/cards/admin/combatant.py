# -*- coding: utf-8 -*-
from django.contrib import admin

from cards.models.combatant import Combatant

__all__ = ["CombatantAdmin"]


@admin.register(Combatant)
class CombatantAdmin(admin.ModelAdmin):
    """Django Admin for Combatant model"""

    readonly_fields = ("uuid", "last_update")
