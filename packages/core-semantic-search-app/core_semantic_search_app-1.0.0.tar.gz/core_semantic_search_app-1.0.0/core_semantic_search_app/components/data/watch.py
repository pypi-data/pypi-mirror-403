""" Watchers for the data collection
"""

from core_semantic_search_app.components.document.api import (
    index_documents_from_data,
    delete_documents_with_data_id,
)


def post_save_data(sender, instance, **kwargs):
    """Method executed after saving a Data object.
    Args:
        sender: Class.
        instance: Data object.
        **kwargs: Args.

    """

    index_documents_from_data(data=instance)


def post_delete_data(sender, instance, **kwargs):
    """Method executed after deleting a Data object.
    Args:
        sender: Class.
        instance: Data object.
        **kwargs: Args.

    """
    delete_documents_with_data_id(instance.id)
