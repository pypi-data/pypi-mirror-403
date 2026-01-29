""" Url router for the core semantic search app
"""

from django.conf.urls import include
from django.contrib.auth.decorators import login_required
from django.urls import re_path

from core_semantic_search_app.views.user import views as user_views

urlpatterns = [
    re_path(
        r"^$",
        login_required(
            user_views.index,
        ),
        name="core_semantic_search_app_index",
    ),
    re_path(r"rest/", include("core_semantic_search_app.rest.urls")),
]
