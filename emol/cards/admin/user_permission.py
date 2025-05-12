# -*- coding: utf-8 -*-
from django.contrib import admin

from cards.models.user_permission import UserPermission


@admin.register(UserPermission)
class UserPermissionAdmin(admin.ModelAdmin):
    """Django Admin for UserPermission model"""

    pass
