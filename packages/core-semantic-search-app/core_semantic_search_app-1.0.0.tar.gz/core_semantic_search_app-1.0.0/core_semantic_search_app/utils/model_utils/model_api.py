""" Model api utils
"""

import logging

from core_semantic_search_app.commons.exceptions import SemanticSearchError
from core_semantic_search_app.components.document import api as document_api
from core_semantic_search_app.components.model_settings.api import get_api_key
from core_semantic_search_app.components.model_settings.models import (
    ModelSettings,
)
from core_semantic_search_app.utils.model_utils import model_client

logger = logging.getLogger(__name__)


def semantic_search(query=None, **kwargs):
    """Semantic search

    Args:
        query:
        **kwargs:

    Returns:

    """
    top_k = kwargs.get("top_k", 10)
    threshold = kwargs.get("threshold", 0.8)
    filters = kwargs.get("filters", None)

    model_settings = ModelSettings.get()

    query_embedding = get_embedding(query)

    documents = document_api.query(
        query_embedding=query_embedding,
        top_k=top_k,
        threshold=threshold,
        vector_function=model_settings.document_retrieval_vector_function,
        data_filters_qs=filters,
    )

    return list(documents)


def get_embedding(content):
    """Compute embedding

    Args:
        content:

    Returns:

    """
    model_settings = ModelSettings.get()
    embedding_model = list(model_settings.embedding_models.keys())[0]
    if model_settings.embedding_models[embedding_model].get("base_url"):
        return model_client.get_embedding(
            base_url=model_settings.embedding_models[embedding_model][
                "base_url"
            ],
            api_key=get_api_key(
                model_settings.embedding_models[embedding_model]
            ),
            model=model_settings.embedding_models[embedding_model]["model"],
            proxies=model_settings.embedding_models[embedding_model].get(
                "proxies", {}
            ),
            ssl_verify=model_settings.embedding_models[embedding_model].get(
                "ssl_verify", True
            ),
            api_content_key=model_settings.embedding_models[
                embedding_model
            ].get("content_key"),
            content=content,
        )
    else:
        try:
            from sentence_transformers import SentenceTransformer

            model = SentenceTransformer(
                model_settings.embedding_models[embedding_model]["model"],
                device=model_settings.embedding_models[embedding_model].get(
                    "device", "cpu"
                ),
            )
            return model.encode([content])[0].tolist()
        except ImportError:
            raise SemanticSearchError(
                "SentenceTransformer is not installed. "
                "Install with core-semantic-search-app[sentence_transformers]."
            )


def write_documents(data):
    """Write documents to database

    Args:

    Returns:

    """
    try:
        documents = document_api.generate_documents_from_data(data)
        for document in documents:
            document.embedding = get_embedding(document.content)
            document.save()
    except Exception as exception:
        logger.error(
            "ERROR: An error occurred while writing documents to database: %s",
            str(exception),
        )
