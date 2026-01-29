""" Document models
"""

from django.db import models
from django.db.models import JSONField
from pgvector.django import VectorField


class Document(models.Model):
    """Document Model"""

    embedding = VectorField()
    content = models.CharField(unique=False, max_length=4000)
    meta = JSONField(default=dict)

    def __str__(self):
        """

        Returns:

        """
        return self.meta.get("title", "Untitled")
