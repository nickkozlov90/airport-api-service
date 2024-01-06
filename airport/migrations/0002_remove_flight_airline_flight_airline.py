# Generated by Django 5.0 on 2024-01-01 17:23

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("airport", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="flight",
            name="airline",
        ),
        migrations.AddField(
            model_name="flight",
            name="airline",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="flights",
                to="airport.airline",
            ),
        ),
    ]