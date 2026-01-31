"""SDK tools helper module for ToothFairyAI MCP server.

This module provides utilities for using the ToothFairyAI SDK
in MCP tool implementations.
"""

from dataclasses import asdict, is_dataclass
from typing import Any, Dict, List, Optional, Union

from toothfairyai import ToothFairyClient, ListResponse


# Regional API URLs
REGIONAL_URLS = {
    "au": "https://api.toothfairyai.com",
    "eu": "https://api.eu.toothfairyai.com",
    "us": "https://api.us.toothfairyai.com",
    "dev": "https://api.toothfairylab.link",
}

# Regional AI URLs (for streaming/chat)
REGIONAL_AI_URLS = {
    "au": "https://ai.toothfairyai.com",
    "eu": "https://ai.eu.toothfairyai.com",
    "us": "https://ai.us.toothfairyai.com",
    "dev": "https://ai.toothfairylab.link",
}


def get_client(
    api_key: str,
    workspace_id: str,
    region: str = "au",
) -> ToothFairyClient:
    """Get a ToothFairyClient configured for the specified region.

    Args:
        api_key: ToothFairyAI API key
        workspace_id: Workspace UUID
        region: API region ("au", "eu", "us")

    Returns:
        Configured ToothFairyClient instance
    """
    base_url = REGIONAL_URLS.get(region, REGIONAL_URLS["au"])
    return ToothFairyClient(
        api_key=api_key,
        workspace_id=workspace_id,
        base_url=base_url,
    )


def to_dict(obj: Any) -> Any:
    """Convert SDK objects to JSON-serializable dicts.

    Handles dataclasses, ListResponse, lists, and nested objects.

    Args:
        obj: Object to convert

    Returns:
        JSON-serializable representation
    """
    if obj is None:
        return None

    if isinstance(obj, ListResponse):
        return {
            "items": [to_dict(item) for item in obj.items],
            "count": len(obj.items),
        }

    if is_dataclass(obj) and not isinstance(obj, type):
        return {k: to_dict(v) for k, v in asdict(obj).items()}

    if isinstance(obj, list):
        return [to_dict(item) for item in obj]

    if isinstance(obj, dict):
        return {k: to_dict(v) for k, v in obj.items()}

    return obj


def success_response(
    message: str,
    data: Any = None,
) -> Dict[str, Any]:
    """Create a successful response dict.

    Args:
        message: Success message
        data: Response data (will be converted to dict)

    Returns:
        Standardized success response
    """
    return {
        "success": True,
        "message": message,
        "error": None,
        "data": to_dict(data),
    }


def error_response(
    message: str,
    error: Optional[str] = None,
) -> Dict[str, Any]:
    """Create an error response dict.

    Args:
        message: Error message
        error: Error code or details

    Returns:
        Standardized error response
    """
    return {
        "success": False,
        "message": message,
        "error": error or message,
        "data": None,
    }


def safe_execute(func):
    """Decorator to safely execute SDK operations with error handling.

    Catches exceptions and returns standardized error responses.
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            return error_response(
                message=f"Operation failed: {str(e)}",
                error=str(e),
            )
    return wrapper
