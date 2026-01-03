# Generated migration for granular feature switch control

from django.db import migrations, models


def migrate_enabled_to_access_mode(apps, schema_editor):
    """Migrate existing enabled field to access_mode."""
    FeatureSwitch = apps.get_model("feature_switches", "FeatureSwitch")
    for switch in FeatureSwitch.objects.all():
        if switch.enabled:
            switch.access_mode = "global"
        else:
            switch.access_mode = "disabled"
        switch.save()


def reverse_migrate_access_mode_to_enabled(apps, schema_editor):
    """Reverse migration: convert access_mode back to enabled."""
    FeatureSwitch = apps.get_model("feature_switches", "FeatureSwitch")
    for switch in FeatureSwitch.objects.all():
        switch.enabled = switch.access_mode == "global"
        switch.save()


class Migration(migrations.Migration):

    dependencies = [
        ("feature_switches", "0001_initial"),
        ("cards", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="featureswitch",
            name="access_mode",
            field=models.CharField(
                choices=[
                    ("disabled", "Disabled - Off for everyone"),
                    ("global", "Global - Enabled for everyone"),
                    ("list", "List - Enabled only for selected users"),
                ],
                default="disabled",
                help_text="Control who can access this feature",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="featureswitch",
            name="allowed_users",
            field=models.ManyToManyField(
                blank=True,
                help_text="Combatants who can access this feature when mode is 'List'",
                to="cards.combatant",
            ),
        ),
        migrations.RunPython(
            migrate_enabled_to_access_mode, reverse_migrate_access_mode_to_enabled
        ),
        migrations.RemoveField(
            model_name="featureswitch",
            name="enabled",
        ),
    ]
