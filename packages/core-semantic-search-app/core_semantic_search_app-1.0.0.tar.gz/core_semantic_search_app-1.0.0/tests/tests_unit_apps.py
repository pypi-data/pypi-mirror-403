""" Apps test class
"""

from unittest import TestCase
from unittest.mock import patch

from core_semantic_search_app.apps import _check_settings, _init_signals
from core_semantic_search_app.commons.exceptions import SemanticSearchError


class TestCheckSettings(TestCase):
    """TestCheckSettings"""

    @patch("core_semantic_search_app.apps.uses_postgresql_backend")
    def test_check_settings_without_psql_raises_error(self, mock_psql_backend):
        """test_check_settings_without_psql_raises_error

        Returns:

        """
        mock_psql_backend.return_value = False
        with self.assertRaises(SemanticSearchError):
            _check_settings()


class TestInitSignals(TestCase):
    """TestInitSignals"""

    @patch("core_semantic_search_app.apps.post_delete")
    @patch("core_semantic_search_app.apps.post_save")
    def test_signals_post_signals_called(
        self, mock_post_save, mock_post_delete
    ):
        """test_signals_post_signals_called

        Returns:

        """
        _init_signals()

        self.assertTrue(mock_post_save.connect.called)
        self.assertTrue(mock_post_delete.connect.called)
