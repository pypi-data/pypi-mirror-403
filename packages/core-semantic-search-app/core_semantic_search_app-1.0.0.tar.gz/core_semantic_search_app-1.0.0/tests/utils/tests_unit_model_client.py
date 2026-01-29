"""Model Client Utils unit testing
"""

import json
from unittest.case import TestCase
from unittest.mock import patch, MagicMock

from core_semantic_search_app.commons.exceptions import SemanticSearchError
from core_semantic_search_app.utils.model_utils.model_client import (
    get_embedding,
)


class TestGetEmbedding(TestCase):
    """TestGetEmbedding"""

    @patch("core_semantic_search_app.utils.model_utils.model_client.requests")
    def test_get_embedding(self, mock_requests):
        """test_get_embedding

        Returns:

        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = json.dumps(
            {
                "data": [
                    {
                        "embedding": [1, 2, 3],
                    }
                ]
            }
        )
        mock_requests.post.return_value = mock_response
        result = get_embedding(base_url="url", content="content")
        self.assertEqual(result, [1, 2, 3])

    @patch("core_semantic_search_app.utils.model_utils.model_client.requests")
    def test_get_embedding_http_error(self, mock_requests):
        """test_get_embedding_http_error

        Returns:

        """
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_requests.post.return_value = mock_response
        with self.assertRaises(SemanticSearchError):
            get_embedding(base_url="url", content="content")

    @patch("core_semantic_search_app.utils.model_utils.model_client.requests")
    def test_get_embedding_response(self, mock_requests):
        """test_get_embedding_response

        Returns:

        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"embedding": "value"}'
        mock_requests.post.return_value = mock_response
        result = get_embedding(base_url="url", content="content")
        self.assertEqual(result, "value")

    @patch("core_semantic_search_app.utils.model_utils.model_client.requests")
    def test_get_embedding_response_data(self, mock_requests):
        """test_get_embedding_response_data

        Returns:

        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"data": [{"embedding": "value"}]}'
        mock_requests.post.return_value = mock_response
        result = get_embedding(base_url="url", content="content")
        self.assertEqual(result, "value")

    @patch("core_semantic_search_app.utils.model_utils.model_client.requests")
    def test_get_embedding_unknown_response(self, mock_requests):
        """test_get_embedding_unknown_response

        Returns:

        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"unknown_key": "value"}'
        mock_requests.post.return_value = mock_response
        with self.assertRaises(SemanticSearchError):
            get_embedding(base_url="url", content="content")
