from django.db import models
from django.forms import ValidationError


class PrivacyPolicy(models.Model):
    class Meta:
        verbose_name_plural = "Privacy policies"

    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"<Privacy policy version {self.created_at.strftime('%Y-%m-%d %H:%M')}>"

    @classmethod
    def latest_version(cls):
        return cls.objects.latest("created_at")

    @classmethod
    def latest_text(cls):
        latest = cls.latest_version()
        return latest.text.replace("[DATE]", latest.created_at.strftime("%Y-%m-%d"))

    def save(self, *args, **kwargs):
        """Policies are write-once"""
        if self.pk is not None:
            raise ValidationError(
                "Cannot update an existing Privacy Policy. Create a new one instead."
            )
        super().save(*args, **kwargs)
