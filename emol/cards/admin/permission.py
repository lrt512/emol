# -*- coding: utf-8 -*-
from cards.models.permission import Permission
from django.contrib import admin
from django.contrib.messages import ERROR, add_message
from django.http import HttpResponseRedirect
from django.urls import path


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    """Django Admin for Permission model"""

    change_list_template = "admin/role_changelist.html"

    list_display = ("name", "is_global", "is_default")

    def get_readonly_fields(self, request, obj=None):
        """
        Rules for viewing and creating Roles
        - User added roles can't be default
        - When editing, default and global flags can't be changed
        """
        if obj:
            return ["is_global", "is_default"]

        return ["is_default"]

    def has_delete_permission(self, request, obj=None):
        """
        Don't allow deletion of default roles
        """
        if obj is None or not obj.is_default:
            return True

        add_message(request, ERROR, "May not delete default roles")
        return False

    def get_urls(self):
        """
        Add the path for populating default roles
        """
        urls = super().get_urls()
        my_urls = [
            path("default_permissions/", self.default_permissions),
        ]
        return my_urls + urls

    def default_permissions(self, request):
        """
        Add any of the default roles that are missing
        """
        for permission in Permission.DEFAULT_PERMISSIONS:
            if not Permission.objects.filter(slug=permission.get("slug")).exists():
                new_p = Permission(is_default=True, **permission)
                new_p.save()

        self.message_user(request, "Added default permissions")
        return HttpResponseRedirect("../")
