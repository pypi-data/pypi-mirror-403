"""Authentication helpers for the Guidelinely API.

The main API endpoints (metadata) do not require authentication.
Calculation endpoints optionally accept an API key.
"""

import os
from typing import Optional

from dotenv import load_dotenv

from guidelinely.exceptions import GuidelinelyConfigError

# Load environment variables from .env file if present
load_dotenv()

__all__ = ["get_api_key", "get_api_base"]


def get_api_key(api_key: Optional[str] = None) -> Optional[str]:
    """Get API key from argument or GUIDELINELY_API_KEY environment variable.

    Args:
        api_key: Optional API key string. If not provided, will check environment.

    Returns:
        API key string or None if not available.
    """
    if api_key is not None:
        return api_key

    env_key = os.getenv("GUIDELINELY_API_KEY")
    if env_key:
        return env_key

    return None


def get_api_base(api_base: Optional[str] = None, use_fallback: bool = True) -> str:
    """Get API base URL from argument or GUIDELINELY_API_BASE environment variable.

    Args:
        api_base: Optional API base URL string. If not provided, will check environment.
        use_fallback: Whether to use a default API base if none is provided.
    Returns:
        API base URL string.

    Raises:
        GuidelinelyConfigError: If no API base URL is provided and GUIDELINELY_API_BASE is not set.
    """
    if api_base is not None:
        return api_base

    env_base = os.getenv("GUIDELINELY_API_BASE")
    if env_base:
        return env_base

    if use_fallback:
        return "https://guidelinely.1681248.com/api/v1"

    raise GuidelinelyConfigError("GUIDELINELY_API_BASE environment variable not set")
