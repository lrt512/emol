from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.forms import ModelForm

from sso_user.models import SSOUser


class UserForm(ModelForm):
    class Meta:
        model = SSOUser
        exclude = (
            "username",
            "password",
            "date_joined",
            "first_name",
            "is_active",
            "last_name",
            "is_staff",
            "is_superuser",
        )
        fields = ("email",)


class UserAdmin(BaseUserAdmin):
    form = UserForm
    add_form = UserForm

    list_display = ("email", "is_superuser")
    list_filter = ("email",)

    fieldsets = ((None, {"fields": ("email",)}),)
    add_fieldsets = ((None, {"fields": ("email",)}),)
    exclude = (
        "username",
        "password",
        "date_joined",
        "first_name",
        "is_active",
        "last_name",
    )

    search_fields = ("email",)
    ordering = ("email",)
    filter_horizontal = ()


# admin.site.unregister(User)
admin.site.register(SSOUser, UserAdmin)
