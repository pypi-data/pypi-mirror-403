""" Authentication tests for Semantic Search REST API
"""

from unittest.mock import patch, MagicMock

from django.test import SimpleTestCase
from rest_framework import status

from core_main_app.utils.tests_tools.MockUser import create_mock_user
from core_main_app.utils.tests_tools.RequestMock import RequestMock
from core_semantic_search_app.rest import views as rest_views


class TestSearchPostPermissions(SimpleTestCase):
    """TestSearchViewPermissions"""

    def test_anonymous_returns_http_403(self):
        """test_anonymous_returns_http_403

        Returns:

        """
        response = RequestMock.do_request_post(
            rest_views.SearchView.as_view(), user=None, data={"query": "query"}
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch("core_semantic_search_app.rest.views.ModelSettings")
    @patch("core_semantic_search_app.rest.views.model_api")
    def test_authenticated_returns_http_200(
        self, mock_model_api, mock_model_settings
    ):
        """test_authenticated_returns_http_200

        Args:
            mock_model_api:

        Returns:

        """
        mock_model_settings_obj = MagicMock()
        mock_model_settings_obj.embedding_models = {"model": {}}
        mock_model_settings.get.return_value = mock_model_settings_obj
        mock_user = create_mock_user(1)

        response = RequestMock.do_request_post(
            rest_views.SearchView.as_view(),
            user=mock_user,
            data={"query": "query"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch("core_semantic_search_app.rest.views.ModelSettings")
    @patch("core_semantic_search_app.rest.views.model_api")
    def test_staff_returns_http_200(self, mock_model_api, mock_model_settings):
        """test_staff_returns_http_200

        Args:
            mock_model_api:

        Returns:

        """
        mock_model_settings_obj = MagicMock()
        mock_model_settings_obj.embedding_models = {"model": {}}
        mock_model_settings.get.return_value = mock_model_settings_obj
        mock_user = create_mock_user(1, is_staff=True)

        response = RequestMock.do_request_post(
            rest_views.SearchView.as_view(),
            user=mock_user,
            data={"query": "query"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
