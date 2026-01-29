""" Model Settings forms
"""

import json

from django import forms

from core_semantic_search_app.components.model_settings.models import (
    ModelSettings,
)


class PrettyJSONEncoder(json.JSONEncoder):
    def __init__(self, *args, indent, sort_keys, **kwargs):
        super().__init__(*args, indent=4, sort_keys=False, **kwargs)


class ModelSettingsAdminForm(forms.ModelForm):

    class Meta:
        model = ModelSettings
        fields = "__all__"
        labels = {
            "sliding_window_chunk_length": "Chunk size (characters)",
            "sliding_window_chunk_overlap": "Chunk overlap (characters)",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["embedding_models"].encoder = PrettyJSONEncoder
        self.fields["embedding_models"].widget.attrs.update(
            {
                "placeholder": """{"modelName":{
        "model": "modelName:version",
        "base_url": "http://localhost:8080/v1",
        "api_key": "",
        "api_key_env": "",
        "ssl_verify": true,
        "proxies": {}
    }
}
            """
            }
        )
