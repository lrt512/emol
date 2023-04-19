# Generated by Django 4.1.7 on 2023-04-16 17:37

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        ("cards", "0003_alter_authorization_slug_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="Reminder",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("object_id", models.PositiveIntegerField()),
                ("days_to_expiry", models.PositiveIntegerField()),
                ("due_date", models.DateField()),
            ],
        ),
        migrations.RemoveField(
            model_name="reminderemail",
            name="card",
        ),
        migrations.RemoveField(
            model_name="reminderemail",
            name="waiver",
        ),
        migrations.RenameField(
            model_name="card",
            old_name="card_issued",
            new_name="date_issued",
        ),
        migrations.AddConstraint(
            model_name="combatantauthorization",
            constraint=models.UniqueConstraint(
                fields=("card", "authorization"), name="combatant_authorization"
            ),
        ),
        migrations.AddConstraint(
            model_name="combatantwarrant",
            constraint=models.UniqueConstraint(
                fields=("card", "marshal"), name="combatant_warrant"
            ),
        ),
        migrations.DeleteModel(
            name="ReminderEmail",
        ),
        migrations.AddField(
            model_name="reminder",
            name="content_type",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="contenttypes.contenttype",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="reminder",
            unique_together={("content_type", "object_id", "days_to_expiry")},
        ),
    ]