"""Semantic Search app user views
"""

import logging

from core_main_app.utils.rendering import render
from core_semantic_search_app.components.model_settings.models import (
    ModelSettings,
)

logger = logging.getLogger(__name__)


def index(request):
    """Semantic Search landing page.

    Args:
        request:

    Returns:

    """
    assets = {
        "js": [
            {
                "path": "core_semantic_search_app/js/search_box.js",
                "is_raw": False,
            },
            {
                "path": "core_main_app/common/js/csrf.js",
                "is_raw": False,
            },
        ],
        "css": [
            "core_semantic_search_app/css/search_box.css",
        ],
    }

    modals = ["core_semantic_search_app/user/modals/settings.html"]

    context = dict()
    model_settings = ModelSettings.get()
    if not model_settings or not model_settings.embedding_models.keys():
        context["error"] = "An embedding model has not been set."
    else:
        context["vector_function"] = (
            model_settings.document_retrieval_vector_function
        )
        context["vector_function_display"] = (
            model_settings.get_document_retrieval_vector_function_display()
        )

    return render(
        request,
        "core_semantic_search_app/user/index.html",
        assets=assets,
        context=context,
        modals=modals,
    )
