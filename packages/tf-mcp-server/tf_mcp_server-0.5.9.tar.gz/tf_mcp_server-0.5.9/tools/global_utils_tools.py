"""Global utility tools for ToothFairyAI MCP server.

This module contains tools that interact with global utility endpoints
that are not workspace-specific, such as announcements, hireable agents,
and AI models. These endpoints do NOT require authentication.
"""

import os
from typing import Any, Dict, List, Optional
import requests


def _get_base_url() -> str:
    """Get the appropriate base URL based on environment."""
    # Check for explicit environment setting
    env = os.environ.get("TF_ENV", "dev").lower()
    
    # Production environments use toothfairyai.com
    if env in ("prod", "prodeu", "produs", "production"):
        return "https://api.toothfairyai.com"
    
    # Default to dev environment
    return "https://api.toothfairylab.link"


def _get_ai_base_url() -> str:
    """Get the appropriate AI services base URL based on environment."""
    # Check for explicit environment setting
    env = os.environ.get("TF_ENV", "dev").lower()
    
    # Production environments with regional variations
    if env == "prodeu":
        return "https://ai.eu.toothfairyai.com"
    elif env == "produs":
        return "https://ai.us.toothfairyai.com"
    elif env in ("prod", "production"):
        return "https://ai.toothfairyai.com"
    
    # Default to dev environment
    return "https://ai.toothfairylab.link"


def _make_request(endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
    """Make a request to the global utils API."""
    base_url = _get_base_url()
    url = f"{base_url}/global_utils/{endpoint}"
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"Request failed: {str(e)}",
            "endpoint": endpoint,
        }


def fetch_announcement() -> Dict[str, Any]:
    """Fetch the latest ToothFairyAI announcement (Public endpoint - no auth required).
    
    Returns the latest announcement message and announcement ID,
    typically used for release notes and important updates.
    
    This is a PUBLIC endpoint that does not require API key or workspace ID.
    
    Returns:
        Dict containing announcement data with fields:
        - lastAnnouncementInt: Integer identifier for the announcement
        - announcement: The announcement message text
    """
    result = _make_request("fetch_announcement")
    
    if "error" in result and not result.get("success", True):
        return result
    
    return {
        "success": True,
        "last_announcement_int": result.get("lastAnnouncementInt"),
        "announcement": result.get("announcement"),
        "raw_response": result,
    }


def fetch_hireable_agents(
    label: Optional[str] = None,
    description: Optional[str] = None,
    mode: Optional[str] = None,
    department: Optional[str] = None,
) -> Dict[str, Any]:
    """Fetch available hireable agents with optional filtering (Public endpoint - no auth required).
    
    This tool retrieves the list of pre-configured agents that can be used
    as inspiration or templates when creating new agents. These agents are
    available in the ToothFairyAI marketplace/workspace.
    
    This is a PUBLIC endpoint that does not require API key or workspace ID.
    
    Args:
        label: Filter by agent name (case-insensitive substring match)
        description: Filter by agent description (case-insensitive substring match)
        mode: Filter by agent mode - exact match (e.g., "coder", "retriever", 
              "chatter", "planner", "voice", "speed", "accuracy", "mathematician")
        department: Filter by department - exact match (e.g., "LEGAL_AND_COMPLIANCE",
                   "OPERATIONS", "INFORMATION_TECHNOLOGY", "SALES", "MARKETING",
                   "CUSTOMER_SUPPORT", "FINANCE", "HUMAN_RESOURCES", "PRODUCT",
                   "ENGINEERING", "RESEARCH_AND_DEVELOPMENT", "ADMINISTRATION",
                   "BUSINESS_DEVELOPMENT", "STRATEGY", "DATA_SCIENCE")
    
    Returns:
        Dict containing:
        - success: Boolean indicating if the request succeeded
        - count: Number of agents returned
        - agents: List of agent objects with their configuration details
        - error: Error message if the request failed
    """
    # Build query parameters
    params = {}
    if label:
        params["label"] = label
    if description:
        params["description"] = description
    if mode:
        params["mode"] = mode
    if department:
        params["department"] = department
    
    result = _make_request("fetch_hireable_agents", params=params if params else None)
    
    if "error" in result and not result.get("success", True):
        return result
    
    agents = result.get("items", [])
    count = result.get("count", len(agents))
    
    # Extract key information for each agent to make it more readable
    simplified_agents = []
    for agent in agents:
        simplified_agents.append({
            "id": agent.get("id"),
            "label": agent.get("label"),
            "description": agent.get("description"),
            "mode": agent.get("mode"),
            "department": agent.get("department"),
            "goals": agent.get("goals"),
            "interpolation_string": agent.get("interpolationString"),
            "has_code": agent.get("hasCode"),
            "charting": agent.get("charting"),
            "allow_internet_search": agent.get("allowInternetSearch"),
            "allow_docs_upload": agent.get("allowDocsUpload"),
            "allow_images_upload": agent.get("allowImagesUpload"),
            "temperature": agent.get("temperature"),
            "max_tokens": agent.get("maxTokens"),
            "minimum_subscription_type": agent.get("minimumSubscriptionType"),
        })
    
    return {
        "success": True,
        "count": count,
        "agents": simplified_agents,
        "raw_response": result,
    }


def fetch_models_list() -> Dict[str, Any]:
    """Fetch the list of supported AI models (Public endpoint - no auth required).
    
    This tool retrieves the complete list of AI models supported by ToothFairyAI,
    including pricing information and model characteristics. This is a PUBLIC endpoint
    that does not require API key or workspace ID.
    
    Returns:
        Dict containing:
        - success: Boolean indicating if the request succeeded
        - models: List of AI models with their details and pricing
        - error: Error message if the request failed
    """
    base_url = _get_ai_base_url()
    url = f"{base_url}/models_list"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        return {
            "success": True,
            "models": result,
            "count": len(result) if isinstance(result, list) else 0,
        }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"Request failed: {str(e)}",
            "endpoint": "models_list",
        }
