""" Unit Test Document Tasks
"""

from unittest.case import TestCase
from unittest.mock import patch

from core_semantic_search_app.tasks import write_documents


class TestWriteDocuments(TestCase):
    """TestWriteDocuments"""

    @patch("core_semantic_search_app.tasks.model_api")
    @patch("core_semantic_search_app.tasks.system_api")
    def test_write_documents(
        self,
        mock_system_api,
        mock_model_api,
    ):
        """test_write_documents

        Args:
            mock_system_api:
            mock_model_api:

        Returns:

        """
        write_documents(1)
        self.assertTrue(mock_model_api.write_documents.called)
