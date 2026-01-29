""" Custom admin site for the Model Settings model
"""

from django.contrib import admin
from django.contrib import messages

from core_semantic_search_app.components.document.api import reindex
from core_semantic_search_app.components.model_settings.forms import (
    ModelSettingsAdminForm,
)


@admin.action(description="Reindex the knowledge base")
def reindex_action(model_admin, request, queryset):
    """

    Args:
        model_admin:
        request:
        queryset:

    Returns:

    """
    if not request.user.is_superuser:
        model_admin.message_user(request, "Permission denied.", messages.ERROR)
        return

    reindex(request.user)


class CustomModelSettingsAdmin(admin.ModelAdmin):
    """CustomModelSettingsAdmin"""

    form = ModelSettingsAdminForm
    actions = [reindex_action]

    def has_add_permission(self, request):
        """Has add permission - only if doesn't exist

        Args:
            request:

        Returns:

        """
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)
