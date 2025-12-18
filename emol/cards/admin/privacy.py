# -*- coding: utf-8 -*-
from cards.models import PrivacyAcceptance, PrivacyPolicy
from django import forms
from django.contrib import admin, messages
from django.forms import ValidationError

__all__ = ["PrivacyAcceptanceAdmin"]


@admin.register(PrivacyAcceptance)
class PrivacyAcceptanceAdmin(admin.ModelAdmin):
    """Django Admin for PrivacyAcceptance model"""


class PrivacyPolicyForm(forms.ModelForm):
    class Meta:
        model = PrivacyPolicy
        fields = ("text",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk is not None:
            self.fields["text"].widget.attrs["readonly"] = True

        self.fields["text"].widget.attrs.update({"rows": "32", "cols": "80"})

    def clean(self):
        cleaned_data = super().clean()
        if self.instance.pk is not None:
            raise ValidationError(
                "Cannot update an existing Privacy Policy. Create a new one instead."
            )

        return cleaned_data


@admin.register(PrivacyPolicy)
class PrivacyPolicyAdmin(admin.ModelAdmin):
    form = PrivacyPolicyForm

    def has_delete_permission(self, request, obj=None):
        return False

    def delete_model(self, request, obj):
        pass

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        policy = PrivacyPolicy.objects.get(pk=object_id)

        if policy.pk is not None:
            extra_context["readonly_fields"] = ("text",)
            extra_context["save_as"] = False
            extra_context["show_save"] = False
            extra_context["show_save_and_add_another"] = False
            extra_context["show_save_and_continue"] = False
            self.message_user(
                request,
                "Note: the text field is read-only for existing policies.",
                level=messages.INFO,
            )

        return super().change_view(
            request, object_id, form_url=form_url, extra_context=extra_context
        )
