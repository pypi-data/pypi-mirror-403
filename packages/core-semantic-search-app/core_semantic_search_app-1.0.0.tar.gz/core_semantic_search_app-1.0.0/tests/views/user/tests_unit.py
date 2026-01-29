""" Unit test for `views.user.views` package.
"""

from unittest.mock import patch, MagicMock

from django.test import RequestFactory, SimpleTestCase

from core_main_app.utils.tests_tools.MockUser import create_mock_user
from core_semantic_search_app.views.user import views as user_views


class TestIndex(SimpleTestCase):
    """TestIndex"""

    def setUp(self):
        """setUp

        Returns:

        """
        self.factory = RequestFactory()
        self.user1 = create_mock_user(user_id="1")

    @patch("core_semantic_search_app.views.user.views.ModelSettings")
    @patch("core_semantic_search_app.views.user.views.render")
    def test_index(self, mock_render, mock_model_settings):
        """test_index

        Returns:

        """
        # Arrange
        mock_model_settings_obj = MagicMock()
        mock_model_settings_obj.embedding_models = {"model": {}}
        mock_model_settings.get.return_value = mock_model_settings_obj
        request = self.factory.get("core_semantic_search_app_index")
        request.user = self.user1

        # Act
        user_views.index(request)

        # Assert
        self.assertTrue(mock_render.called)

    @patch("core_semantic_search_app.views.user.views.ModelSettings")
    @patch("core_semantic_search_app.views.user.views.render")
    def test_index_no_model_settings(self, mock_render, mock_model_settings):
        """test_index

        Returns:

        """
        # Arrange
        mock_model_settings_obj = MagicMock()
        mock_model_settings_obj.embedding_models = {}
        mock_model_settings.get.return_value = mock_model_settings_obj
        request = self.factory.get("core_semantic_search_app_index")
        request.user = self.user1

        # Act
        user_views.index(request)

        # Assert
        self.assertTrue(mock_render.called)
