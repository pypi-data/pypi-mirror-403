""" Unit Test Data
"""

from unittest.case import TestCase
from unittest.mock import patch, MagicMock

from core_semantic_search_app.components.data.watch import (
    post_save_data,
    post_delete_data,
)


class TestDataWatch(TestCase):
    """TestDataWatch"""

    @patch(
        "core_semantic_search_app.components.data.watch.index_documents_from_data"
    )
    def test_watch_post_save_data(self, mock_index_documents_from_data):
        """test_watch_post_save_data

        Args:
            mock_index_documents_from_data

        Returns:

        """
        post_save_data(sender=MagicMock(), instance=MagicMock())
        self.assertTrue(mock_index_documents_from_data.called)

    @patch(
        "core_semantic_search_app.components.data.watch.delete_documents_with_data_id"
    )
    def test_watch_post_delete_data(self, mock_delete_documents_with_data_id):
        """test_watch_post_save_data

        Args:
            mock_delete_documents_with_data_id

        Returns:

        """
        post_delete_data(sender=MagicMock(), instance=MagicMock())
        self.assertTrue(mock_delete_documents_with_data_id.called)
