"""ToothFairyAI Documentation MCP Server.

A Model Context Protocol server that exposes ToothFairyAI documentation,
API specifications, and integration guides for AI assistants.
"""

from .server import mcp

__version__ = "0.1.0"
__all__ = ["mcp"]
