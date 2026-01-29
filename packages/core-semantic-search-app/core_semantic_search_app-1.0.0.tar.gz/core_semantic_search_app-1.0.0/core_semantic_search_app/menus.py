""" Add Semantic Search to main menu
"""

from django.urls import reverse
from menu import Menu, MenuItem

from core_semantic_search_app.settings import SEMANTIC_SEARCH_MENU_NAME

Menu.add_item(
    "main",
    MenuItem(
        SEMANTIC_SEARCH_MENU_NAME, reverse("core_semantic_search_app_index")
    ),
)
