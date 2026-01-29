""" Apps file for core_semantic_search_app
"""

import sys

from django.apps import AppConfig
from django.db.models.signals import post_save, post_delete

from core_main_app.utils.databases.backend import uses_postgresql_backend
from core_semantic_search_app.commons.exceptions import SemanticSearchError


class SemanticSearchAppConfig(AppConfig):
    """Core application settings"""

    name = "core_semantic_search_app"

    def ready(self):
        """Run when the app is ready

        Returns:

        """
        if "migrate" in sys.argv:
            return

        _check_settings()
        _init_signals()


def _check_settings():
    """Check settings

    Returns:

    """
    if not uses_postgresql_backend():
        raise SemanticSearchError("PostgreSQL with Pgvector is required.")


def _init_signals():
    """Init Signals

    Returns:

    """
    from core_main_app.components.data.models import Data
    from core_semantic_search_app.components.data.watch import (
        post_save_data,
        post_delete_data,
    )

    post_save.connect(post_save_data, sender=Data)
    post_delete.connect(post_delete_data, sender=Data)
