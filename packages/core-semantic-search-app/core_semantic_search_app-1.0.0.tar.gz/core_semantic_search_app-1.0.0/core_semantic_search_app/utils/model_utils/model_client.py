""" Model client
"""

import json
import logging

import requests

from core_semantic_search_app.commons.exceptions import SemanticSearchError


logger = logging.getLogger(__name__)


def get_embedding(base_url, content, **kwargs):
    """Get embedding

    Args:
        base_url:
        content:
        **kwargs:

    Returns:

    """
    api_key = kwargs.get("api_key", "no-key")
    model = kwargs.get("model", None)
    proxies = kwargs.get("proxies", {})
    ssl_verify = kwargs.get("ssl_verify", True)
    content_key = kwargs.get("content_key") or "input"

    data = dict()
    data["model"] = model
    data[content_key] = content

    url = f"{base_url}/embeddings"
    r = requests.post(
        proxies=proxies,
        url=url,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        data=json.dumps(data),
        verify=ssl_verify,
    )
    if r.status_code == 200:
        json_response = json.loads(r.text)
        try:
            if "embedding" in json_response:
                return json_response["embedding"]
            return json_response["data"][0]["embedding"]
        except Exception:
            raise SemanticSearchError(
                "An error occurred while retrieving embedding."
            )
    else:
        raise SemanticSearchError(
            f"Error (status code: {r.status_code}, error: {r.text})"
        )
