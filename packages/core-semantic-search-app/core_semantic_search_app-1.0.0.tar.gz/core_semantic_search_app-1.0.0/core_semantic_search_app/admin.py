""" Url router for the administration site
"""

from django.contrib import admin

from core_semantic_search_app.components.document.models import Document
from core_semantic_search_app.components.model_settings.admin_site import (
    CustomModelSettingsAdmin,
)
from core_semantic_search_app.components.model_settings.models import (
    ModelSettings,
)

admin.site.register(Document)
admin.site.register(ModelSettings, CustomModelSettingsAdmin)
