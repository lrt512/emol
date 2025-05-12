from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.forms import ModelChoiceField, ModelForm

from cards.models.card import Card
from cards.models.reminder import Reminder
from cards.models.waiver import Waiver


class ReminderForm(ModelForm):
    """Custom form for Reminder model"""

    content_type = ModelChoiceField(
        queryset=ContentType.objects.filter(model__in=("Card", "Waiver")).order_by(
            "model"
        ),
        empty_label="-- Select --",
        label="Reminder for",
    )
    object_id = ModelChoiceField(
        queryset=Card.objects.none(), empty_label="-- Select --", label="Object"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["content_type"].label_from_instance = self._get_label_from_instance

        if self.instance and self.instance.object_id is not None:
            self.fields["content_type"].disabled = True
            self.fields["object_id"].disabled = True
            self.fields["object_id"].queryset = self._get_object_instance_queryset(
                self.instance.content_type, self.instance.object_id
            )

    def _get_label_from_instance(self, obj):
        """Get display text for content_type choices"""
        return obj.name.capitalize()

    def _get_object_instance_queryset(self, content_type=None, object_id=None):
        """Get queryset for object_id field based on selected content_type"""
        if content_type and object_id:
            model_class = content_type.model_class()
            return model_class.objects.filter(id=object_id)

        return Card.objects.all()

    def clean(self):
        """Ensure that content_type and object_id are valid"""
        cleaned_data = super().clean()
        content_type = cleaned_data.get("content_type")
        object_id = cleaned_data.get("object_id")
        if content_type and object_id:
            model_class = content_type.model_class()
            try:
                model_class.objects.get(pk=object_id.pk)
            except model_class.DoesNotExist:
                self.add_error(
                    "object_id",
                    f"{model_class.__name__} with id {object_id.pk} does not exist",
                )
        return cleaned_data

    class Meta:
        model = Reminder
        fields = "__all__"


class ReminderAdmin(admin.ModelAdmin):
    """Django Admin for Reminder model"""


admin.site.register(Reminder, ReminderAdmin)
