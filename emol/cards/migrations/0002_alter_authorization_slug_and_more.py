# Generated by Django 4.1.7 on 2023-03-22 02:45

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("cards", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="authorization",
            name="slug",
            field=models.SlugField(editable=False, max_length=255, unique=True),
        ),
        migrations.AlterField(
            model_name="combatant",
            name="privacy_acceptance_code",
            field=models.CharField(max_length=32, null=True, unique=True),
        ),
    ]