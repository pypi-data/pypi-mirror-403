"""Authentication handling for Rail Engine SDK (retrieval package)."""

import os
from typing import Optional

# Default production API URL
DEFAULT_API_URL = "https://cndr.railtown.ai/api"


def get_pat(pat: Optional[str] = None) -> Optional[str]:
    """
    Get PAT token from parameter or environment variable.

    Args:
        pat: PAT token provided directly, or None to read from environment

    Returns:
        PAT token string or None if not found
    """
    return pat or os.getenv("ENGINE_PAT")


def get_engine_id(engine_id: Optional[str] = None) -> Optional[str]:
    """
    Get engine ID from parameter or environment variable.

    Args:
        engine_id: Engine ID provided directly, or None to read from environment

    Returns:
        Engine ID string or None if not found
    """
    return engine_id or os.getenv("ENGINE_ID")


def get_api_url(api_url: Optional[str] = None) -> str:
    """
    Get API URL from parameter or environment variable.

    Args:
        api_url: API URL provided directly, or None to read from environment

    Returns:
        API URL string (defaults to production if not provided)
    """
    if api_url:
        return api_url
    env_url = os.getenv("RAILTOWN_API_URL")
    return env_url if env_url else DEFAULT_API_URL


def normalize_base_url(url: str) -> str:
    """
    Normalize base URL by stripping /api suffix if present.

    Args:
        url: Base URL that may contain /api suffix

    Returns:
        Normalized URL without /api suffix
    """
    # Handle /api/ (with trailing slash)
    if url.endswith("/api/"):
        return url[:-5]
    # Handle /api (without trailing slash)
    if url.endswith("/api"):
        return url[:-4]
    return url
