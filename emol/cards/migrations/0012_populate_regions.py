# Generated manually for data migration
from django.db import migrations


def populate_regions(apps, schema_editor):
    """Populate the Region table with expected regions."""
    Region = apps.get_model("cards", "Region")

    # Define the regions for SCA Ealdormere (Ontario and Michigan only)
    regions = [
        {
            "code": "ON",
            "name": "Ontario",
            "country": "Canada",
            "postal_format": "A1A 1A1",
            "active": True,
        },
        {
            "code": "MI",
            "name": "Michigan",
            "country": "United States",
            "postal_format": "12345",
            "active": True,
        },
    ]

    # Create region records
    for region_data in regions:
        Region.objects.get_or_create(code=region_data["code"], defaults=region_data)


def migrate_combatant_provinces(apps, schema_editor):
    """No data migration needed - province field structure unchanged."""
    # The province field is still just a CharField, not a foreign key
    # Admin interface provides dropdown, so no data conversion needed
    pass


def reverse_populate_regions(apps, schema_editor):
    """Remove all Region records."""
    Region = apps.get_model("cards", "Region")
    Region.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("cards", "0011_fix_global_permissions"),
    ]

    operations = [
        migrations.RunPython(
            populate_regions,
            reverse_populate_regions,
        ),
        migrations.RunPython(
            migrate_combatant_provinces,
            migrations.RunPython.noop,
        ),
    ]
