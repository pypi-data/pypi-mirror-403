""" Settings for core_semantic_search_app.

Settings with the following syntax can be overwritten at the project level:
SETTING_NAME = getattr(settings, "SETTING_NAME", "Default Value")
"""

from django.conf import settings

if not settings.configured:
    settings.configure()

INSTALLED_APPS = getattr(settings, "INSTALLED_APPS", [])
""" :py:class:`list`: List of apps installed.
"""


SEMANTIC_SEARCH_MENU_NAME = getattr(
    settings,
    "SEMANTIC_SEARCH_MENU_NAME",
    "Semantic Search",
)
""" :py:class:`str`: Semantic Search app menu label.
"""
