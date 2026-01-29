""" Url router for the core semantic search app
"""

from django.urls import re_path

from core_semantic_search_app.rest import views as semantic_search_views

urlpatterns = [
    re_path(
        r"^search/$",
        semantic_search_views.SearchView.as_view(),
        name="core_semantic_search_app_rest_search",
    ),
]
