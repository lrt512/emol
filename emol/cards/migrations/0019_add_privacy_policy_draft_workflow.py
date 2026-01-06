# Generated migration for privacy policy draft workflow

import uuid

from django.db import migrations, models


def set_existing_policy_versions(apps, schema_editor):
    """Set version numbers for existing policies based on creation year."""
    PrivacyPolicy = apps.get_model("cards", "PrivacyPolicy")
    for policy in PrivacyPolicy.objects.all():
        year = policy.created_at.year
        existing_versions = PrivacyPolicy.objects.filter(
            version__startswith=f"{year}."
        ).exclude(id=policy.id)
        if existing_versions.exists():
            max_minor = 0
            for existing in existing_versions:
                try:
                    if existing.version:
                        minor = int(existing.version.split(".")[1])
                        max_minor = max(max_minor, minor)
                except (ValueError, IndexError, AttributeError):
                    pass
            policy.version = f"{year}.{max_minor + 1}"
        else:
            policy.version = f"{year}.1"
        policy.approved = True
        if not policy.changelog:
            policy.changelog = "Initial policy version (migrated)"
        policy.save()


def reverse_set_existing_policy_versions(apps, schema_editor):
    """Reverse migration - no action needed."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("cards", "0018_delete_update_code_model"),
    ]

    operations = [
        migrations.AddField(
            model_name="privacypolicy",
            name="version",
            field=models.CharField(
                editable=False, max_length=20, null=True, blank=True
            ),
        ),
        migrations.AddField(
            model_name="privacypolicy",
            name="changelog",
            field=models.TextField(
                blank=True, help_text="Description of changes in this version"
            ),
        ),
        migrations.AddField(
            model_name="privacypolicy",
            name="approved",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="privacypolicy",
            name="draft_uuid",
            field=models.UUIDField(blank=True, null=True, unique=True),
        ),
        migrations.RunPython(
            set_existing_policy_versions, reverse_set_existing_policy_versions
        ),
        migrations.AlterField(
            model_name="privacypolicy",
            name="version",
            field=models.CharField(
                editable=False, max_length=20, unique=True, null=True, blank=True
            ),
        ),
        migrations.AddConstraint(
            model_name="privacypolicy",
            constraint=models.UniqueConstraint(
                fields=["version"], name="unique_version"
            ),
        ),
    ]

