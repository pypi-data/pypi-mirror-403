""" Unit Test Document
"""

from unittest.case import TestCase
from unittest.mock import patch, MagicMock

from django.contrib.auth.models import User

from core_main_app.commons.exceptions import ApiError
from core_semantic_search_app.components.document.api import (
    delete_documents_with_data_id,
    _get_documents_by_data_id,
    _check_template_name,
    query,
    reindex,
    index_documents_from_data,
    generate_documents_from_data,
)
from core_semantic_search_app.components.document.models import Document
from core_semantic_search_app.components.model_settings.models import (
    ModelSettings,
)


class TestGenerateDocumentsFromData(TestCase):
    """TestGenerateDocumentsFromData"""

    @patch.object(ModelSettings, "get")
    @patch("core_semantic_search_app.components.document.api.logger")
    @patch(
        "core_semantic_search_app.components.document.api.system_pid_path_api"
    )
    @patch("core_semantic_search_app.components.document.api.chunk_json_dict")
    def test_generate_documents_from_data_pid_error(
        self,
        mock_chunk_json_dict,
        mock_system_pid_path_api,
        mock_logger,
        mock_model_settings_get,
    ):
        """test_generate_documents_from_data_pid_error

        Args:
            mock_chunk_json_dict:
            mock_system_pid_path_api:
            mock_logger:
            mock_model_settings_get:

        Returns:

        """
        mock_model_settings = MagicMock()
        mock_model_settings.sliding_window_split_length = 200
        mock_model_settings.sliding_window_split_overlap = 20
        mock_model_settings_get.return_value = mock_model_settings
        mock_system_pid_path_api.get_pid_path_by_template.side_effect = (
            Exception()
        )
        generate_documents_from_data(MagicMock())
        self.assertTrue(mock_logger.error.called)

    @patch.object(ModelSettings, "get")
    @patch(
        "core_semantic_search_app.components.document.api.is_dot_notation_in_dictionary"
    )
    @patch(
        "core_semantic_search_app.components.document.api.get_value_from_dot_notation"
    )
    @patch(
        "core_semantic_search_app.components.document.api.system_pid_path_api"
    )
    @patch("core_semantic_search_app.components.document.api.chunk_json_dict")
    def test_generate_documents_from_data_pid_calls_get_value_from_dot_notation(
        self,
        mock_chunk_json_dict,
        mock_system_pid_path_api,
        mock_get_value_from_dot_notation,
        mock_is_dot_notation_in_dictionary,
        mock_model_settings_get,
    ):
        """test_generate_documents_from_data_pid_calls_get_value_from_dot_notation

        Args:
            mock_chunk_json_dict:
            mock_system_pid_path_api:
            mock_is_dot_notation_in_dictionary:
            mock_model_settings_get:

        Returns:

        """
        mock_model_settings = MagicMock()
        mock_model_settings.sliding_window_split_length = 200
        mock_model_settings.sliding_window_split_overlap = 20
        mock_model_settings_get.return_value = mock_model_settings
        mock_is_dot_notation_in_dictionary.return_value = True
        generate_documents_from_data(MagicMock())
        self.assertTrue(mock_get_value_from_dot_notation.called)

    @patch.object(ModelSettings, "get")
    @patch(
        "core_semantic_search_app.components.document.api.is_dot_notation_in_dictionary"
    )
    @patch(
        "core_semantic_search_app.components.document.api.get_value_from_dot_notation"
    )
    @patch(
        "core_semantic_search_app.components.document.api.system_pid_path_api"
    )
    @patch("core_semantic_search_app.components.document.api.chunk_json_dict")
    def test_generate_documents_from_data_values(
        self,
        mock_chunk_json_dict,
        mock_system_pid_path_api,
        mock_get_value_from_dot_notation,
        mock_is_dot_notation_in_dictionary,
        mock_model_settings_get,
    ):
        """

        Args:
            mock_chunk_json_dict:
            mock_system_pid_path_api:
            mock_get_value_from_dot_notation:
            mock_is_dot_notation_in_dictionary:
            mock_model_settings_get:

        Returns:

        """
        mock_model_settings = MagicMock()
        mock_model_settings_get.return_value = mock_model_settings
        mock_model_settings.document_index_strategy = "VALUES"
        generate_documents_from_data(MagicMock())
        self.assertTrue(mock_chunk_json_dict.called)

    @patch.object(ModelSettings, "get")
    @patch(
        "core_semantic_search_app.components.document.api.is_dot_notation_in_dictionary"
    )
    @patch(
        "core_semantic_search_app.components.document.api.get_value_from_dot_notation"
    )
    @patch(
        "core_semantic_search_app.components.document.api.system_pid_path_api"
    )
    @patch("core_semantic_search_app.components.document.api.chunk_json_dict")
    def test_generate_documents_from_data_text(
        self,
        mock_chunk_json_dict,
        mock_system_pid_path_api,
        mock_get_value_from_dot_notation,
        mock_is_dot_notation_in_dictionary,
        mock_model_settings_get,
    ):
        """

        Args:
            mock_system_pid_path_api:
            mock_get_value_from_dot_notation:
            mock_is_dot_notation_in_dictionary:
            mock_model_settings_get:

        Returns:

        """
        mock_model_settings = MagicMock()
        mock_model_settings_get.return_value = mock_model_settings
        mock_model_settings.document_index_strategy = "DOCUMENT"
        mock_model_settings.sliding_window_split_length = 200
        mock_model_settings.sliding_window_split_overlap = 20
        mock_chunk_json_dict.return_value = " ".join(
            [str(i) for i in range(100)]
        )
        generate_documents_from_data(MagicMock())
        self.assertTrue(mock_chunk_json_dict.called)


class TestDeleteDocumentsWithDataId(TestCase):
    """TestDeleteDocumentsWithDataId"""

    @patch(
        "core_semantic_search_app.components.document.api._get_documents_by_data_id"
    )
    def test_documents_delete_called(self, mock_get_documents_by_data_id):
        """test_documents_delete_called

        Args:
            mock_get_documents_by_data_id:

        Returns:

        """
        # Arrange
        mock_documents = MagicMock()
        mock_get_documents_by_data_id.return_value = mock_documents
        # Act
        delete_documents_with_data_id("1")
        # Assert
        self.assertTrue(mock_documents.delete.called)


class TestIndexDocumentsFromData(TestCase):
    """TestIndexDocumentsFromData"""

    @patch.object(ModelSettings, "get")
    @patch.object(Document, "objects")
    @patch("core_semantic_search_app.components.document.api.workspace_api")
    @patch("core_semantic_search_app.components.document.api.data_api")
    @patch(
        "core_semantic_search_app.components.document.api.semantic_search_tasks"
    )
    @patch(
        "core_semantic_search_app.components.document.api._check_template_name"
    )
    def test_index_documents_from_data_no_model_settings(
        self,
        mock_check_template_name,
        mock_tasks,
        mock_data_api,
        mock_workspace_api,
        mock_document_objects,
        mock_model_settings_get,
    ):
        mock_model_settings_get.return_value = None
        mock_data = MagicMock()
        mock_data.workspace.id = 1
        mock_workspace_api.get_all_public_workspaces.return_value.values_list.return_value = [
            1
        ]
        index_documents_from_data(mock_data)
        self.assertFalse(mock_tasks.write_documents.apply_async.called)

    @patch.object(ModelSettings, "get")
    @patch.object(Document, "objects")
    @patch("core_semantic_search_app.components.document.api.workspace_api")
    @patch("core_semantic_search_app.components.document.api.data_api")
    @patch(
        "core_semantic_search_app.components.document.api.semantic_search_tasks"
    )
    @patch(
        "core_semantic_search_app.components.document.api._check_template_name"
    )
    def test_index_documents_from_data(
        self,
        mock_check_template_name,
        mock_tasks,
        mock_data_api,
        mock_workspace_api,
        mock_document_objects,
        mock_model_settings_get,
    ):
        mock_data = MagicMock()
        mock_data.workspace.id = 1
        mock_workspace_api.get_all_public_workspaces.return_value.values_list.return_value = [
            1
        ]
        index_documents_from_data(mock_data)
        self.assertTrue(mock_tasks.write_documents.apply_async.called)

    @patch.object(ModelSettings, "get")
    @patch.object(Document, "objects")
    @patch("core_semantic_search_app.components.document.api.workspace_api")
    @patch("core_semantic_search_app.components.document.api.data_api")
    @patch(
        "core_semantic_search_app.components.document.api.semantic_search_tasks"
    )
    @patch(
        "core_semantic_search_app.components.document.api._check_template_name"
    )
    def test_index_documents_from_data_with_bad_template_name(
        self,
        mock_check_template_name,
        mock_tasks,
        mock_data_api,
        mock_workspace_api,
        mock_document_objects,
        mock_model_settings_get,
    ):
        mock_data = MagicMock()
        mock_check_template_name.return_value = False
        mock_data.workspace.id = 1
        mock_workspace_api.get_all_public_workspaces.return_value.values_list.return_value = [
            1
        ]
        index_documents_from_data(mock_data)
        self.assertFalse(mock_tasks.write_documents.apply_async.called)

    @patch.object(ModelSettings, "get")
    @patch.object(Document, "objects")
    @patch("core_semantic_search_app.components.document.api.workspace_api")
    @patch("core_semantic_search_app.components.document.api.data_api")
    @patch(
        "core_semantic_search_app.components.document.api.semantic_search_tasks"
    )
    @patch(
        "core_semantic_search_app.components.document.api._check_template_name"
    )
    def test_index_documents_from_data_without_workspace(
        self,
        mock_check_template_name,
        mock_tasks,
        mock_data_api,
        mock_workspace_api,
        mock_document_objects,
        mock_model_settings_get,
    ):
        mock_data = MagicMock()
        mock_data.workspace = None
        mock_workspace_api.get_all_public_workspaces.return_value.values_list.return_value = [
            1
        ]
        index_documents_from_data(mock_data)
        self.assertFalse(mock_tasks.write_documents.apply_async.called)

    @patch.object(ModelSettings, "get")
    @patch.object(Document, "objects")
    @patch("core_semantic_search_app.components.document.api.workspace_api")
    @patch("core_semantic_search_app.components.document.api.data_api")
    @patch(
        "core_semantic_search_app.components.document.api.semantic_search_tasks"
    )
    @patch(
        "core_semantic_search_app.components.document.api._check_template_name"
    )
    def test_index_documents_from_data_workspace_not_public(
        self,
        mock_check_template_name,
        mock_tasks,
        mock_data_api,
        mock_workspace_api,
        mock_document_objects,
        mock_model_settings_get,
    ):
        mock_data = MagicMock()
        mock_data.workspace.id = 1
        mock_workspace_api.get_all_public_workspaces.return_value.values_list.return_value = (
            []
        )
        index_documents_from_data(mock_data)
        self.assertFalse(mock_tasks.write_documents.apply_async.called)


class TestReindex(TestCase):
    """TestReindex"""

    @patch.object(ModelSettings, "get")
    @patch.object(Document, "objects")
    @patch("core_semantic_search_app.components.document.api.workspace_api")
    @patch("core_semantic_search_app.components.document.api.data_api")
    @patch(
        "core_semantic_search_app.components.document.api.semantic_search_tasks"
    )
    @patch(
        "core_semantic_search_app.components.document.api._check_template_name"
    )
    def test_reindex(
        self,
        mock_check_template_name,
        mock_tasks,
        mock_data_api,
        mock_workspace_api,
        mock_document_objects,
        mock_model_settings_get,
    ):
        """test_reindex

        Args:
            mock_check_template_name:
            mock_tasks:
            mock_data_api:
            mock_workspace_api:
            mock_document_objects:
            mock_model_settings_get:

        Returns:

        """
        mock_data_api.get_all.return_value.filter.return_value = [MagicMock()]
        mock_user = User()
        mock_user.is_superuser = True
        reindex(mock_user)
        self.assertTrue(mock_document_objects.all.return_value.delete.called)
        self.assertTrue(mock_tasks.write_documents.apply_async.called)

    @patch.object(ModelSettings, "get")
    @patch.object(Document, "objects")
    @patch("core_semantic_search_app.components.document.api.workspace_api")
    @patch("core_semantic_search_app.components.document.api.data_api")
    @patch(
        "core_semantic_search_app.components.document.api.semantic_search_tasks"
    )
    @patch(
        "core_semantic_search_app.components.document.api._check_template_name"
    )
    def test_reindex_only_if_template_name_matches(
        self,
        mock_check_template_name,
        mock_tasks,
        mock_data_api,
        mock_workspace_api,
        mock_document_objects,
        mock_model_settings_get,
    ):
        """test_reindex_only_if_template_name_matches

        Args:
            mock_check_template_name:
            mock_tasks:
            mock_data_api:
            mock_workspace_api:
            mock_document_objects:
            mock_model_settings_get:

        Returns:

        """
        mock_data_no_match = MagicMock()
        mock_data_no_match.id = 1
        mock_data_api.get_all.return_value.filter.return_value = [
            mock_data_no_match
        ]
        mock_user = User()
        mock_user.is_superuser = True
        mock_check_template_name.return_value = False
        reindex(mock_user)
        self.assertTrue(mock_document_objects.all.return_value.delete.called)
        self.assertFalse(mock_tasks.write_documents.apply_async.called)


class TestQuery(TestCase):
    """TestQuery"""

    @patch.object(Document, "objects")
    def test_query(self, mock_document_objects):
        """test_query

        Returns:

        """
        query([1, 2, 3])
        self.assertTrue(mock_document_objects.all.called)
        self.assertTrue(mock_document_objects.all.return_value.order_by.called)
        self.assertTrue(
            mock_document_objects.all.return_value.order_by.return_value.annotate.called
        )

    @patch.object(Document, "objects")
    def test_query_filters(self, mock_document_objects):
        """test_query_filters

        Returns:

        """
        filters_qs = MagicMock()
        result = query([1, 2, 3], data_filters_qs=filters_qs, top_k=1)
        self.assertTrue(type(result), list)

    @patch.object(Document, "objects")
    def test_query_no_filters(self, mock_document_objects):
        """test_query_no_filters

        Returns:

        """
        query()
        self.assertTrue(mock_document_objects.all.called)
        self.assertFalse(
            mock_document_objects.all.return_value.order_by.called
        )

    def test_query_with_invalid_vector_function(self):
        """test_query_with_invalid_vector_function

        Returns:

        """
        with self.assertRaises(ApiError):
            query(vector_function="invalid")

    @patch.object(Document, "objects")
    def test_query_vector_function_max_inner_product(
        self, mock_document_objects
    ):
        """test_query_vector_function_max_inner_product

        Returns:

        """
        query([1, 2, 3], vector_function="max_inner_product")
        self.assertTrue(mock_document_objects.all.called)
        self.assertTrue(mock_document_objects.all.return_value.order_by.called)
        self.assertTrue(
            mock_document_objects.all.return_value.order_by.return_value.annotate.called
        )

    @patch.object(Document, "objects")
    def test_query_vector_function_l2_distance(self, mock_document_objects):
        """test_query_vector_function_l2_distance

        Returns:

        """
        query([1, 2, 3], vector_function="l2_distance")
        self.assertTrue(mock_document_objects.all.called)
        self.assertTrue(mock_document_objects.all.return_value.order_by.called)
        self.assertTrue(
            mock_document_objects.all.return_value.order_by.return_value.annotate.called
        )


class TestCheckTemplateName(TestCase):
    """TestCheckTemplateName"""

    def test_check_template_name_with_valid_pattern(self):
        """test_check_template_name_with_valid_pattern

        Returns:

        """
        mock_data = MagicMock()
        mock_data.template.version_manager.title = "template.json"
        self.assertIsNotNone(_check_template_name(mock_data, ".json"))

    def test_check_template_name_with_invalid_pattern(self):
        """test_check_template_name_with_valid_pattern

        Returns:

        """
        mock_data = MagicMock()
        mock_data.template.version_manager.title = "template.xml"
        self.assertIsNone(_check_template_name(mock_data, ".json"))


class TestGetDocumentsByDataId(TestCase):
    """TestGetDocumentsByDataId"""

    @patch.object(Document, "objects")
    def test_get_documents_by_data_id(self, mock_documents_objects):
        """test_get_documents_by_data_id

        Returns:

        """
        mock_documents = MagicMock()
        mock_documents_objects.filter.return_value = mock_documents
        documents = _get_documents_by_data_id(data_id=1)
        self.assertEqual(documents, mock_documents)


class TestDocumentStr(TestCase):
    """TestDocumentStr"""

    def test_document_str(self):
        """test_document_str

        Returns:

        """
        document = Document(
            embedding=[1, 2, 3], content="content", meta={"title": "title"}
        )
        self.assertEqual(str(document), "title")
