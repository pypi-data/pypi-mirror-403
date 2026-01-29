""" Migrations
"""

from django.db import migrations, models
import pgvector.django
from pgvector.django import VectorExtension


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        VectorExtension(),
        migrations.CreateModel(
            name="Document",
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
                ("embedding", pgvector.django.VectorField()),
                ("content", models.CharField(max_length=4000, unique=False)),
                ("meta", models.JSONField(default=dict)),
            ],
        ),
    ]
