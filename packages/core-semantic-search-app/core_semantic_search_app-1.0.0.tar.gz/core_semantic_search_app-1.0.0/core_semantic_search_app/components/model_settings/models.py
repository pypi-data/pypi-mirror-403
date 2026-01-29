""" Model Settings model
"""

from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import ValidationError
from django.db import models as db_models

from core_main_app.commons import exceptions


class ModelSettings(db_models.Model):
    """ModelSettings"""

    class Meta:
        verbose_name = "Models Settings"
        verbose_name_plural = "Models Settings"

    embedding_models = db_models.JSONField(default=dict, blank=True)

    INDEX_STRATEGIES = [
        ("DOCUMENT", "Full Document"),
        ("VALUES", "Selected Values"),
    ]
    document_index_strategy = db_models.CharField(
        max_length=8,
        choices=INDEX_STRATEGIES,
        default="DOCUMENT",
    )
    document_index_fields = db_models.JSONField(default=list, blank=True)

    VECTOR_FUNCTIONS = [
        ("cosine_similarity", "Cosine Similarity"),
        ("max_inner_product", "Inner Product"),
        ("l2_distance", "Euclidean Distance"),
    ]
    document_retrieval_vector_function = db_models.CharField(
        max_length=50, choices=VECTOR_FUNCTIONS, default="cosine_similarity"
    )
    document_index_template_name_filter = db_models.CharField(
        max_length=50, default=".*"
    )
    sliding_window_chunk_length = db_models.PositiveIntegerField(default=1000)
    sliding_window_chunk_overlap = db_models.PositiveIntegerField(default=200)

    @staticmethod
    def get():
        """Retrieve the Retrieve ModelSettings.

        Returns:
             ModelSettings - first ModelSettings object
        """
        try:
            return ModelSettings.objects.first()  # pylint: disable=no-member
        except ObjectDoesNotExist:
            return None
        except Exception as exc:
            raise exceptions.ModelError(str(exc))

    def __str__(self):
        """ModelSettings object as string.

        Returns:
            str - String representation of ModelSettings object.
        """
        return "Models Settings"

    def clean(self):
        """Clean model fields

        Returns:

        """
        super().clean()

        if (
            isinstance(self.embedding_models, dict)
            and len(self.embedding_models.keys()) > 1
        ):
            raise ValidationError(
                "Embedding models dictionary can only contain one embedding."
            )

    def save(self, *args, **kwargs):
        """Custom save

        Args:
            *args:
            **kwargs:

        Returns:

        """
        self.full_clean()

        super().save(*args, **kwargs)
