"""Model API Utils unit testing
"""

from unittest.case import TestCase
from unittest.mock import patch, MagicMock

from core_semantic_search_app.commons.exceptions import SemanticSearchError
from core_semantic_search_app.components.model_settings.models import (
    ModelSettings,
)
from core_semantic_search_app.utils.model_utils.model_api import (
    semantic_search,
    get_embedding,
    write_documents,
)


class TestSemanticSearch(TestCase):
    """TestSemanticSearch"""

    @patch(
        "core_semantic_search_app.utils.model_utils.model_api.get_embedding"
    )
    @patch("core_semantic_search_app.utils.model_utils.model_api.document_api")
    @patch.object(ModelSettings, "get")
    def test_semantic_search(
        self, mock_model_settings_get, mock_document_api, mock_get_embedding
    ):
        """test_semantic_search

        Returns:

        """
        result = semantic_search(query="query")
        self.assertTrue(mock_document_api.query.called)
        mock_get_embedding.assert_called_with("query")
        self.assertTrue(isinstance(result, list))


class TestGetEmbedding(TestCase):
    """TestGetEmbedding"""

    @patch(
        "core_semantic_search_app.utils.model_utils.model_client.get_embedding"
    )
    @patch.object(ModelSettings, "get")
    def test_get_embedding(self, mock_model_settings_get, mock_get_embedding):
        """test_get_embedding

        Returns:

        """
        mock_model_settings_get.return_value.embedding_models = {
            "model1": {
                "base_url": "URL",
                "model": "model",
                "server": "server",
            }
        }
        get_embedding(content="content")
        self.assertTrue(mock_get_embedding.called)

    @patch("sentence_transformers.SentenceTransformer")
    @patch.object(ModelSettings, "get")
    def test_get_embedding_local(
        self, mock_model_settings_get, mock_sentence_transformer
    ):
        """test_get_embedding_local

        Returns:

        """
        mock_model_settings_get.return_value.embedding_models = {
            "model1": {
                "model": "model",
            }
        }
        get_embedding(content="content")
        self.assertTrue(mock_sentence_transformer.called)

    @patch("sentence_transformers.SentenceTransformer")
    @patch.object(ModelSettings, "get")
    def test_get_embedding_local_missing_package(
        self, mock_model_settings_get, mock_sentence_transformer
    ):
        """test_get_embedding_local_missing_package

        Returns:

        """
        mock_sentence_transformer.side_effect = ImportError()
        mock_model_settings_get.return_value.embedding_models = {
            "model1": {
                "model": "model",
            }
        }
        with self.assertRaises(SemanticSearchError):
            get_embedding(content="content")


class TestWriteDocuments(TestCase):
    """TestWriteDocuments"""

    @patch(
        "core_semantic_search_app.utils.model_utils.model_api.get_embedding"
    )
    @patch("core_semantic_search_app.utils.model_utils.model_api.document_api")
    def test_write_documents(self, mock_document_api, mock_get_embedding):
        """test_write_documents

        Returns:

        """
        mock_document = MagicMock()
        mock_document_api.generate_documents_from_data.return_value = [
            mock_document
        ]
        write_documents(MagicMock())
        mock_get_embedding.assert_called_with(mock_document.content)
        self.assertTrue(mock_document.save.called)

    @patch("core_semantic_search_app.utils.model_utils.model_api.logger")
    @patch("core_semantic_search_app.utils.model_utils.model_api.document_api")
    def test_write_documents_exception(self, mock_document_api, mock_logger):
        """test_write_documents_exception

        Returns:

        """
        mock_document_api.generate_documents_from_data.side_effect = (
            Exception()
        )
        write_documents(MagicMock())
        self.assertTrue(mock_logger.error.called)
