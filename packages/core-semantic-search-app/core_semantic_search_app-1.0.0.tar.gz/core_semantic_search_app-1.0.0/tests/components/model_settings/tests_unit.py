""" Unit Test Model Settings
"""

from unittest.case import TestCase
from unittest.mock import patch, MagicMock

from django.contrib import admin
from django.core.exceptions import ObjectDoesNotExist, ValidationError

from core_main_app.commons.exceptions import ModelError
from core_semantic_search_app.components.document.models import Document
from core_semantic_search_app.components.model_settings.admin_site import (
    CustomModelSettingsAdmin,
    reindex_action,
)
from core_semantic_search_app.components.model_settings.api import get_api_key
from core_semantic_search_app.components.model_settings.forms import (
    ModelSettingsAdminForm,
    PrettyJSONEncoder,
)
from core_semantic_search_app.components.model_settings.models import (
    ModelSettings,
)


class TestModelSettingsAdminForm(TestCase):
    """TestModelSettingsAdminForm"""

    def test_init(self):
        """test_init

        Returns:

        """
        form = ModelSettingsAdminForm()
        self.assertIsNotNone(
            form.fields["embedding_models"].widget.attrs["placeholder"]
        )

    @patch("builtins.super")
    def test_json_encoder(self, mock_super):
        """test_json_encoder

        Returns:

        """
        PrettyJSONEncoder(indent=0, sort_keys=True)
        self.assertTrue(mock_super.return_value.indent == 4)
        self.assertFalse(mock_super.return_value.sort_keys)


class TestCustomModelSettingsAdmin(TestCase):
    """TestCustomModelSettingsAdmin"""

    def test_has_add_permission_true_if_doesnt_exist(self):
        """test_has_add_permission_true_if_doesnt_exist

        Returns:

        """
        custom_admin_settings = CustomModelSettingsAdmin(
            Document, admin.AdminSite()
        )
        custom_admin_settings.model = MagicMock()
        custom_admin_settings.model.objects.exists.return_value = True
        has_perm = custom_admin_settings.has_add_permission(
            request=MagicMock()
        )
        self.assertFalse(has_perm)

    def test_has_add_permission_false_if_exists(self):
        """test_has_add_permission_false_if_exists

        Returns:

        """
        custom_admin_settings = CustomModelSettingsAdmin(
            Document, admin.AdminSite()
        )
        custom_admin_settings.model = MagicMock()
        custom_admin_settings.model.objects.exists.return_value = False
        has_perm = custom_admin_settings.has_add_permission(
            request=MagicMock()
        )
        self.assertTrue(has_perm)

    @patch(
        "core_semantic_search_app.components.model_settings.admin_site.reindex"
    )
    def test_reindex_action_calls_reindex(self, mock_reindex):
        """test_reindex_action_calls_reindex

        Returns:

        """
        mock_request = MagicMock()
        mock_model_admin = MagicMock()
        mock_queryset = MagicMock()
        mock_request.user.is_superuser = True
        reindex_action(mock_model_admin, mock_request, mock_queryset)
        self.assertTrue(mock_reindex.called)

    @patch(
        "core_semantic_search_app.components.model_settings.admin_site.reindex"
    )
    def test_reindex_action_forbidden_if_not_superuser(self, mock_reindex):
        """test_reindex_action_forbidden_if_not_superuser

        Returns:

        """
        mock_request = MagicMock()
        mock_model_admin = MagicMock()
        mock_queryset = MagicMock()
        mock_request.user.is_superuser = False
        reindex_action(mock_model_admin, mock_request, mock_queryset)
        self.assertFalse(mock_reindex.called)


class TestGetAPIKey(TestCase):
    """TestGetAPIKey"""

    def test_get_api_key_from_dict(self):
        """

        Returns:

        """
        model_dict = {"api_key": "test_key"}
        result = get_api_key(model_dict)
        self.assertEqual(result, "test_key")

    @patch("core_semantic_search_app.components.model_settings.api.os")
    def test_get_api_key_from_env(self, mock_os):
        """test_get_api_key_from_env

        Returns:

        """
        mock_os.getenv.return_value = "test_env_key"
        model_dict = {"api_key_env": "test_env_name"}

        result = get_api_key(model_dict)
        self.assertEqual(result, "test_env_key")
        mock_os.getenv.assert_called_with("test_env_name")


class TestModelSettings(TestCase):
    """TestModelSettings"""

    @patch.object(ModelSettings, "objects")
    def test_get(self, mock_model_settings_object):
        """test_get

        Returns:

        """
        model_settings = ModelSettings()
        mock_object = MagicMock()
        mock_model_settings_object.first.return_value = mock_object
        result = model_settings.get()
        self.assertEqual(result, mock_object)

    @patch.object(ModelSettings, "objects")
    def test_get_does_not_exist(self, mock_model_settings_object):
        """test_get_does_not_exist

        Returns:

        """
        model_settings = ModelSettings()
        mock_model_settings_object.first.side_effect = ObjectDoesNotExist()
        result = model_settings.get()
        self.assertIsNone(result)

    @patch.object(ModelSettings, "objects")
    def test_get_model_error(self, mock_model_settings_object):
        """test_get_model_error

        Returns:

        """
        model_settings = ModelSettings()
        mock_model_settings_object.first.side_effect = Exception()
        with self.assertRaises(ModelError):
            model_settings.get()

    def test_str(self):
        """test_str

        Returns:

        """
        model_settings = ModelSettings()
        self.assertEqual(str(model_settings), "Models Settings")

    @patch("builtins.super")
    def test_clean(self, mock_super):
        """test_clean

        Returns:

        """
        mock_super.clean.return_value = None
        model_settings = ModelSettings()
        model_settings.models = {}
        model_settings.embedding_models = {}
        model_settings.clean()

    @patch("builtins.super")
    def test_clean_invalid_embedding_models(self, mock_super):
        """test_clean_invalid_embedding_models

        Returns:

        """
        mock_super.clean.return_value = None
        model_settings = ModelSettings()
        model_settings.embedding_models = {"a": 1, "b": 2}
        with self.assertRaises(ValidationError):
            model_settings.clean()

    @patch.object(ModelSettings, "full_clean")
    @patch("builtins.super")
    def test_save(self, mock_super, mock_full_clean):
        """test_save

        Returns:

        """
        mock_super.save.return_value = None
        model_settings = ModelSettings()
        model_settings.save()
        self.assertTrue(mock_full_clean.called)
