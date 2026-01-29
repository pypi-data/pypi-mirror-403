""" Document API
"""

import logging
import re

from django.db.models import OuterRef, Exists, IntegerField
from django.db.models.fields.json import KeyTextTransform
from django.db.models.functions import Cast
from pgvector.django import CosineDistance, L2Distance, MaxInnerProduct

from core_main_app.access_control.api import has_perm_administration
from core_main_app.access_control.decorators import access_control
from core_main_app.commons.exceptions import ApiError
from core_main_app.components.data import api as data_api
from core_main_app.components.workspace import api as workspace_api
from core_semantic_search_app import tasks as semantic_search_tasks
from core_semantic_search_app.components.document.models import Document
from core_semantic_search_app.components.model_settings.models import (
    ModelSettings,
)
from core_semantic_search_app.settings import (
    INSTALLED_APPS,
)
from core_semantic_search_app.utils.chunking_utils import chunk_json_dict

if "core_linked_records_app" in INSTALLED_APPS:
    from core_linked_records_app.system.pid_path import (
        api as system_pid_path_api,
    )
    from core_linked_records_app.utils.dict import (
        is_dot_notation_in_dictionary,
        get_value_from_dot_notation,
    )
logger = logging.getLogger(__name__)

VECTOR_FUNCTIONS = {
    "cosine_similarity": CosineDistance,
    "l2_distance": L2Distance,
    "max_inner_product": MaxInnerProduct,
}


# NOTE: called from task
def generate_documents_from_data(data):
    """Convert data to documents

    Args:
        data:

    Returns:

    """
    data_pid = None
    if "core_linked_records_app" in INSTALLED_APPS:
        try:
            pid_path = system_pid_path_api.get_pid_path_by_template(
                data.template,
            ).path

            # If the pid_path does not exist in the document, exit early and return None
            data_dict = data.get_dict_content()
            if is_dot_notation_in_dictionary(data_dict, pid_path):
                data_pid = get_value_from_dot_notation(data_dict, pid_path)
        except Exception as e:
            logger.error(
                f"Unable to get data PID during data to document conversion: {str(e)}"
            )
    model_settings = ModelSettings.get()

    target_keys = (
        model_settings.document_index_fields
        if model_settings.document_index_strategy == "VALUES"
        else None
    )

    text_chunks = chunk_json_dict(
        json_dict=data.get_dict_content(),
        chunk_size=model_settings.sliding_window_chunk_length,
        chunk_overlap=model_settings.sliding_window_chunk_overlap,
        target_keys=target_keys,
    )

    documents = list()
    for text_chunk in text_chunks:
        document = Document(
            content=text_chunk,
            meta={
                "title": data.title,
                "data_id": data.id,
                "data_pid": data_pid,
            },
        )
        documents.append(document)
    return documents


# NOTE: called from data watch
def delete_documents_with_data_id(data_id):
    """Delete documents with given data id

    Args:
        data_id:

    Returns:

    """
    # Get any existing documents for this data
    documents = _get_documents_by_data_id(data_id=data_id)
    # Delete documents
    documents.delete()


# NOTE: called from data watch
def index_documents_from_data(data):
    """Index documents extracted from a data

    Args:
        data:

    Returns:

    """
    model_settings = ModelSettings.get()

    if not model_settings or not model_settings.embedding_models.keys():
        return

    # Delete previous documents
    delete_documents_with_data_id(data.id)

    if not _check_template_name(
        data, model_settings.document_index_template_name_filter
    ):
        return

    # only deal with data in a workspace
    if not data.workspace:
        return

    # only deal with public data
    public_workspaces = workspace_api.get_all_public_workspaces().values_list(
        "id", flat=True
    )
    if data.workspace.id not in public_workspaces:
        return

    # Start indexing of documents
    semantic_search_tasks.write_documents.apply_async((data.id,))


@access_control(has_perm_administration)
def reindex(user):
    """Reindex the full knowledge base

    Returns:

    """
    # Get all currently indexed documents
    all_docs = Document.objects.all()
    # Delete them
    all_docs.delete()

    # Find all public workspaces
    public_workspaces = workspace_api.get_all_public_workspaces().values_list(
        "id", flat=True
    )
    # Get all public data
    all_data = data_api.get_all(user).filter(workspace__in=public_workspaces)

    # Get model settings from database
    model_settings = ModelSettings.get()
    # Go through all records
    for data in all_data:
        # Check if template name matches pattern
        if not _check_template_name(
            data, model_settings.document_index_template_name_filter
        ):
            continue
        # Index documents in tasks
        semantic_search_tasks.write_documents.apply_async((data.id,))


def query(
    query_embedding=None,
    top_k=10,
    threshold=0.8,
    vector_function="cosine_similarity",
    data_filters_qs=None,
):
    """Query the embedding

    Args:
        query_embedding:
        top_k:
        threshold:
        data_filters_qs:
        vector_function:

    Returns:

    """
    if vector_function not in list(VECTOR_FUNCTIONS.keys()):
        raise ApiError(
            f"Vector function should be in: {list(VECTOR_FUNCTIONS.keys())}."
        )
    # Get all documents
    queryset = Document.objects.all()

    if data_filters_qs is not None:
        # Pull data_id from meta field
        data_id_expr = Cast(
            KeyTextTransform("data_id", "meta"),
            output_field=IntegerField(),
        )
        # Filter on extracted data_id
        queryset = queryset.annotate(_data_id=data_id_expr).filter(
            Exists(data_filters_qs.filter(id=OuterRef("_data_id")))
        )

    if query_embedding:
        # Order documents by distance to query
        # https://github.com/pgvector/pgvector-python?tab=readme-ov-file#django
        queryset = queryset.order_by(
            VECTOR_FUNCTIONS[vector_function]("embedding", query_embedding)
        )

        # Compute the score between query and documents
        # https://github.com/pgvector/pgvector?tab=readme-ov-file#distances
        if vector_function == "cosine_similarity":
            queryset = queryset.annotate(
                score=1 - CosineDistance("embedding", query_embedding)
            )
        elif vector_function == "max_inner_product":
            queryset = queryset.annotate(
                score=-1 * MaxInnerProduct("embedding", query_embedding)
            )
        elif vector_function == "l2_distance":
            queryset = queryset.annotate(
                score=L2Distance("embedding", query_embedding)
            )

        # filter score with provided threshold
        if threshold:
            if vector_function == "l2_distance":
                queryset = queryset.filter(score__lt=threshold)
            else:
                queryset = queryset.filter(score__gt=threshold)

    # Keep the top k results
    if top_k:
        queryset = queryset.all()[:top_k]

    return queryset


def _check_template_name(data, pattern):
    """Check template name matches the pattern

    Args:
        data:
        pattern:

    Returns:

    """
    return re.search(pattern, data.template.version_manager.title)


def _get_documents_by_data_id(data_id):
    """Get documents with data id

    Args:
        data_id:

    Returns:

    """
    return Document.objects.filter(meta__data_id=int(data_id))
