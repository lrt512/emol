import uuid
from datetime import datetime

from django.db import models
from django.forms import ValidationError


class PrivacyPolicy(models.Model):
    class Meta:
        verbose_name_plural = "Privacy policies"
        constraints = [
            models.UniqueConstraint(fields=["version"], name="unique_version"),
        ]

    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    version = models.CharField(
        max_length=20, unique=True, editable=False, null=True, blank=True
    )
    changelog = models.TextField(
        help_text="Description of changes in this version", blank=True
    )
    approved = models.BooleanField(default=False)
    draft_uuid = models.UUIDField(unique=True, null=True, blank=True)

    def __str__(self):
        if self.version:
            return f"<Privacy policy version {self.version}>"
        return f"<Privacy policy version {self.created_at.strftime('%Y-%m-%d %H:%M')}>"

    @classmethod
    def latest_version(cls):
        """Get the latest approved policy version."""
        approved = cls.objects.filter(approved=True, version__isnull=False)
        if not approved.exists():
            return None

        def version_key(policy):
            """Extract version components for sorting."""
            try:
                year, minor = policy.version.split(".")
                return (int(year), int(minor))
            except (ValueError, AttributeError):
                return (0, 0)

        return max(approved, key=version_key)

    @classmethod
    def latest_text(cls):
        """Get the text of the latest approved policy."""
        latest = cls.latest_version()
        if latest is None:
            return ""
        return latest.text.replace("[DATE]", latest.created_at.strftime("%Y-%m-%d"))

    @classmethod
    def get_draft_by_uuid(cls, draft_uuid):
        """Get a draft policy by its UUID."""
        try:
            return cls.objects.get(draft_uuid=draft_uuid)
        except cls.DoesNotExist:
            return None

    def generate_version(self):
        """Generate a version number in YYYY.N format."""
        if self.approved and self.version:
            return self.version

        year = datetime.now().year
        existing_versions = PrivacyPolicy.objects.filter(
            approved=True, version__startswith=f"{year}."
        ).exclude(id=self.id if self.id else None)

        if existing_versions.exists():
            max_minor = 0
            for existing in existing_versions:
                try:
                    if existing.version:
                        minor = int(existing.version.split(".")[1])
                        max_minor = max(max_minor, minor)
                except (ValueError, IndexError):
                    pass
            return f"{year}.{max_minor + 1}"

        return f"{year}.1"

    def approve(self):
        """Approve this draft policy and generate a version number."""
        if self.approved:
            raise ValidationError("Policy is already approved.")

        self.version = self.generate_version()
        self.approved = True
        self.save()

    def save(self, *args, **kwargs):
        """Save the policy with draft editing support."""
        if self.pk is not None:
            existing = PrivacyPolicy.objects.get(pk=self.pk)
            if existing.approved:
                raise ValidationError(
                    "Cannot update an approved Privacy Policy. "
                    "Create a new draft instead."
                )

        if not self.approved and not self.draft_uuid:
            self.draft_uuid = uuid.uuid4()

        super().save(*args, **kwargs)
