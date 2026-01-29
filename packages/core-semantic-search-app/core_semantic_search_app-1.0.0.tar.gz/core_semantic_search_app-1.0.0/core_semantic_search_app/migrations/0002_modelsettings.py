""" Migrations
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core_semantic_search_app", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ModelSettings",
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
                (
                    "embedding_models",
                    models.JSONField(blank=True, default=dict),
                ),
                (
                    "document_index_strategy",
                    models.CharField(
                        choices=[
                            ("DOCUMENT", "Full Document"),
                            ("VALUES", "Selected Values"),
                        ],
                        default="DOCUMENT",
                        max_length=8,
                    ),
                ),
                (
                    "document_index_fields",
                    models.JSONField(blank=True, default=list),
                ),
                (
                    "document_retrieval_vector_function",
                    models.CharField(
                        choices=[
                            ("cosine_similarity", "Cosine Similarity"),
                            ("max_inner_product", "Max Inner Product"),
                            ("l2_distance", "L2 Distance"),
                        ],
                        default="cosine_similarity",
                        max_length=50,
                    ),
                ),
                (
                    "document_index_template_name_filter",
                    models.CharField(default=".*", max_length=50),
                ),
                (
                    "sliding_window_chunk_length",
                    models.PositiveIntegerField(default=1000),
                ),
                (
                    "sliding_window_chunk_overlap",
                    models.PositiveIntegerField(default=200),
                ),
            ],
            options={
                "verbose_name": "Models Settings",
                "verbose_name_plural": "Models Settings",
            },
        ),
    ]
