========================
Core Semantic Search App
========================

Semantic search for the curator core project.

Quick start
===========

1. Add "core_semantic_search_app" to your INSTALLED_APPS setting
----------------------------------------------------------------

.. code:: python

    INSTALLED_APPS = [
      ...
      'core_semantic_search_app',
    ]


2. Include the core_semantic_search_app URLconf in your project urls.py
-----------------------------------------------------------------------

.. code:: python

    re_path(r'^semantic-search/', include('core_semantic_search_app.urls')),
