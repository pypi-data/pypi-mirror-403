""" ModelSetting api
"""

import os


def get_api_key(model_dict):
    """Get API Key from dictionary

    Args:
        model_dict:

    Returns:

    """
    # Check if api_key_env is set
    api_key_env = model_dict.get("api_key_env")
    # Get value of API Key from env
    api_key = os.getenv(api_key_env) if api_key_env else None
    # Get value from dict otherwise
    api_key = model_dict.get("api_key", "no-key") if not api_key else api_key
    # Return API Key
    return api_key
