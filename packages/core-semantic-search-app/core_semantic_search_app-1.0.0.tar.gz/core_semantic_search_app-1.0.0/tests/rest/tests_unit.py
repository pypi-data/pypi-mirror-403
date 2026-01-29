"""Unit tests for semantic search rest api
"""

from unittest.mock import patch, MagicMock

from django.test import SimpleTestCase
from rest_framework import status

from core_main_app.utils.tests_tools.MockUser import create_mock_user
from core_main_app.utils.tests_tools.RequestMock import (
    RequestMock,
)
from core_semantic_search_app.rest import views as rest_views


class TestSearchView(SimpleTestCase):
    """TestSearchView"""

    def test_post_without_model_settings_returns_http_500(self):
        """test_post_without_model_settings_returns_http_500

        Args:

        Returns:

        """
        # Arrange
        mock_user = create_mock_user("1")

        # Mock
        response = RequestMock.do_request_post(
            rest_views.SearchView.as_view(), mock_user, data={"query": "query"}
        )

        # Assert
        self.assertEqual(
            response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    @patch("core_semantic_search_app.rest.views.ModelSettings")
    def test_post_without_data_returns_http_500(self, mock_model_settings):
        """test_post_without_data_returns_http_500

        Args:

        Returns:

        """
        # Arrange
        mock_model_settings_obj = MagicMock()
        mock_model_settings_obj.embedding_models = {"model": {}}
        mock_model_settings.get.return_value = mock_model_settings_obj
        mock_user = create_mock_user("1")

        # Mock
        response = RequestMock.do_request_post(
            rest_views.SearchView.as_view(),
            mock_user,
        )

        # Assert
        self.assertEqual(
            response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    @patch("core_semantic_search_app.rest.views.ModelSettings")
    def test_post_without_query_returns_http_400(self, mock_model_settings):
        """test_post_without_query_returns_http_400

        Args:

        Returns:

        """
        # Arrange
        mock_model_settings_obj = MagicMock()
        mock_model_settings_obj.embedding_models = {"model": {}}
        mock_model_settings.get.return_value = mock_model_settings_obj
        mock_user = create_mock_user("1")

        # Mock
        response = RequestMock.do_request_post(
            rest_views.SearchView.as_view(), mock_user, data={}
        )

        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("core_semantic_search_app.rest.views.ModelSettings")
    @patch("core_semantic_search_app.rest.views.build_doc_list")
    @patch("core_semantic_search_app.rest.views.model_api")
    def test_post_snippet_only(
        self, mock_model_api, mock_build_doc_list, mock_model_settings
    ):
        """test_post_snippet_only

        Args:

        Returns:

        """
        # Arrange
        mock_model_settings_obj = MagicMock()
        mock_model_settings_obj.embedding_models = {"model": {}}
        mock_model_settings.get.return_value = mock_model_settings_obj
        mock_user = create_mock_user("1")

        # Mock
        response = RequestMock.do_request_post(
            rest_views.SearchView.as_view(),
            mock_user,
            data={"query": "query", "snippets_only": True},
        )

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(mock_build_doc_list.called)

    @patch("core_semantic_search_app.rest.views.ModelSettings")
    @patch("core_semantic_search_app.rest.views.build_doc_data_list")
    @patch("core_semantic_search_app.rest.views.model_api")
    def test_post_not_snippet_only(
        self, mock_model_api, build_doc_data_list, mock_model_settings
    ):
        """test_post_not_snippet_only

        Args:

        Returns:

        """
        # Arrange
        mock_model_settings_obj = MagicMock()
        mock_model_settings_obj.embedding_models = {"model": {}}
        mock_model_settings.get.return_value = mock_model_settings_obj
        mock_user = create_mock_user("1")

        # Mock
        response = RequestMock.do_request_post(
            rest_views.SearchView.as_view(),
            mock_user,
            data={"query": "query", "snippets_only": False},
        )

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(build_doc_data_list.called)

    @patch("core_semantic_search_app.rest.views.ModelSettings")
    @patch("core_semantic_search_app.rest.views.build_doc_list")
    @patch("core_semantic_search_app.rest.views.model_api")
    @patch("core_semantic_search_app.rest.views.data_api")
    def test_post_with_filters(
        self,
        mock_data_api,
        mock_model_api,
        build_doc_list,
        mock_model_settings,
    ):
        """test_post_with_filters

        Args:

        Returns:

        """
        # Arrange
        mock_model_settings_obj = MagicMock()
        mock_model_settings_obj.embedding_models = {"model": {}}
        mock_model_settings.get.return_value = mock_model_settings_obj
        mock_user = create_mock_user("1")

        # Mock
        response = RequestMock.do_request_post(
            rest_views.SearchView.as_view(),
            mock_user,
            data={"query": "query", "filters": {"field": "value"}},
        )

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(build_doc_list.called)
        self.assertTrue(mock_data_api.execute_json_query.called)

    @patch("core_semantic_search_app.rest.views.ModelSettings")
    @patch("core_semantic_search_app.rest.views.build_doc_data_list")
    @patch("core_semantic_search_app.rest.views.model_api")
    def test_post_no_model_settings(
        self, mock_model_api, build_doc_data_list, mock_model_settings
    ):
        """test_post_not_snippet_only

        Args:

        Returns:

        """
        # Arrange
        mock_model_settings_obj = MagicMock()
        mock_model_settings_obj.embedding_models = {}
        mock_model_settings.get.return_value = mock_model_settings_obj
        mock_user = create_mock_user("1")

        # Mock
        response = RequestMock.do_request_post(
            rest_views.SearchView.as_view(),
            mock_user,
            data={"query": "query"},
        )

        self.assertEqual(
            response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
        )
