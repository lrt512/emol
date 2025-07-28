# -*- coding: utf-8 -*-
from cards.models.user_permission import UserPermission
from cards.models.permission import Permission
from django.contrib import admin
from django.forms import ModelForm
from django.core.exceptions import ValidationError
import json


class UserPermissionForm(ModelForm):
    """Custom form for UserPermission with validation"""
    
    class Meta:
        model = UserPermission
        fields = ['user', 'permission', 'discipline']
    
    def clean(self):
        """Validate that global permissions don't have disciplines assigned"""
        cleaned_data = super().clean()
        permission = cleaned_data.get('permission')
        discipline = cleaned_data.get('discipline')
        
        if permission and permission.is_global and discipline is not None:
            raise ValidationError(
                f"Global permission '{permission.name}' cannot be assigned to a specific discipline. "
                f"Global permissions must be discipline-independent."
            )
        
        if permission and not permission.is_global and discipline is None:
            raise ValidationError(
                f"Non-global permission '{permission.name}' requires a discipline to be specified."
            )
        
        return cleaned_data


@admin.register(UserPermission)
class UserPermissionAdmin(admin.ModelAdmin):
    """Django Admin for UserPermission model"""

    form = UserPermissionForm
    list_display = ('user', 'permission', 'discipline', 'is_global_permission')
    list_filter = ('permission__is_global', 'discipline')
    search_fields = ('user__email', 'permission__name', 'discipline__name')
    
    def is_global_permission(self, obj):
        """Display whether the permission is global in the list view"""
        return obj.permission.is_global
    is_global_permission.boolean = True
    is_global_permission.short_description = 'Global Permission'
    
    def add_view(self, request, form_url='', extra_context=None):
        """Add permission data to the context for JavaScript"""
        extra_context = extra_context or {}
        
        # Get all permissions and their global status
        permissions_data = {}
        for perm in Permission.objects.all():
            permissions_data[str(perm.id)] = {
                'name': perm.name,
                'is_global': perm.is_global
            }
        
        extra_context['permissions_data'] = json.dumps(permissions_data)
        return super().add_view(request, form_url, extra_context)
    
    def change_view(self, request, object_id, form_url='', extra_context=None):
        """Add permission data to the context for JavaScript"""
        extra_context = extra_context or {}
        
        # Get all permissions and their global status
        permissions_data = {}
        for perm in Permission.objects.all():
            permissions_data[str(perm.id)] = {
                'name': perm.name,
                'is_global': perm.is_global
            }
        
        extra_context['permissions_data'] = json.dumps(permissions_data)
        return super().change_view(request, object_id, form_url, extra_context)
    
    class Media:
        js = ('admin/js/user_permission_admin.js',)
