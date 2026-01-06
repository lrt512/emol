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
        fields = ("text", "changelog", "approved")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk is not None:
            if self.instance.approved:
                self.fields["text"].widget.attrs["readonly"] = True
                self.fields["changelog"].widget.attrs["readonly"] = True
                self.fields["approved"].widget.attrs["disabled"] = True

        self.fields["text"].widget.attrs.update({"rows": "32", "cols": "80"})

    def clean(self):
        cleaned_data = super().clean()
        if self.instance.pk is not None:
            existing = PrivacyPolicy.objects.get(pk=self.instance.pk)
            if existing.approved:
                raise ValidationError(
                    "Cannot update an approved Privacy Policy. "
                    "Create a new draft instead."
                )

        return cleaned_data


@admin.register(PrivacyPolicy)
class PrivacyPolicyAdmin(admin.ModelAdmin):
    form = PrivacyPolicyForm
    list_display = ("version", "approved", "created_at", "draft_uuid")
    list_filter = ("approved", "created_at")
    readonly_fields = ("version", "draft_uuid", "created_at")

    def has_delete_permission(self, request, obj=None):
        return False

    def delete_model(self, request, obj):
        pass

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        policy = PrivacyPolicy.objects.get(pk=object_id)

        if policy.approved:
            extra_context["readonly_fields"] = ("text", "changelog", "version")
            extra_context["save_as"] = False
            extra_context["show_save"] = False
            extra_context["show_save_and_add_another"] = False
            extra_context["show_save_and_continue"] = False
            self.message_user(
                request,
                "Note: approved policies cannot be edited. Create a new draft instead.",
                level=messages.INFO,
            )
        elif policy.pk is not None:
            self.message_user(
                request,
                "Note: This is a draft. You can edit it here or use the edit interface.",
                level=messages.INFO,
            )

        return super().change_view(
            request, object_id, form_url=form_url, extra_context=extra_context
        )
