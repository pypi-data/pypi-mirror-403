""" Semantic Search tasks
"""

import logging

from celery import shared_task

from core_main_app.system import api as system_api
from core_semantic_search_app.utils.model_utils import model_api

logger = logging.getLogger(__name__)


@shared_task
def write_documents(data_id):
    """Write documents to database"""
    data = system_api.get_data_by_id(data_id)
    model_api.write_documents(data)
