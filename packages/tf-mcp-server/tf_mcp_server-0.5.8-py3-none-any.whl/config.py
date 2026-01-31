"""Configuration management for the MCP server."""

import os
from pathlib import Path
from typing import Literal, Optional

from pydantic import BaseModel, Field


#
class ServerConfig(BaseModel):
    """Configuration for the MCP server."""

    host: str = Field(default="0.0.0.0", description="Host to bind the server")
    port: int = Field(default=8000, description="Port to bind the server")
    transport: Literal["stdio", "http"] = Field(
        default="http",
        description="Transport type: 'stdio' for local use, 'http' for remote access",
    )

    # Documentation paths (relative to repo root)
    docs_path: Path = Field(
        default=Path("docs/tf_docs/docs"), description="Path to markdown documentation"
    )
    api_docs_path: Path = Field(
        default=Path("docs/api_docs/public"),
        description="Path to API documentation (OpenAPI specs)",
    )

    # Base path for the repository
    base_path: Optional[Path] = Field(
        default=None, description="Base path to the repository root"
    )

    def __init__(self, **data):
        super().__init__(**data)
        # Resolve base path if not provided
        if self.base_path is None:
            # Default to parent of tf_mcp_server directory
            self.base_path = Path(__file__).parent.parent

        # Make docs paths absolute
        if not self.docs_path.is_absolute():
            self.docs_path = self.base_path / self.docs_path
        if not self.api_docs_path.is_absolute():
            self.api_docs_path = self.base_path / self.api_docs_path

    @classmethod
    def from_env(cls) -> "ServerConfig":
        """Create configuration from environment variables."""
        transport = os.environ.get("MCP_TRANSPORT", "http")
        if transport not in ("stdio", "http"):
            transport = "http"
        return cls(
            host=os.environ.get("MCP_HOST", "0.0.0.0"),
            port=int(os.environ.get("MCP_PORT", "8000")),
            transport=transport,
            docs_path=Path(os.environ.get("DOCS_PATH", "docs/tf_docs/docs")),
            api_docs_path=Path(os.environ.get("API_DOCS_PATH", "docs/api_docs/public")),
            base_path=(
                Path(os.environ.get("BASE_PATH"))
                if os.environ.get("BASE_PATH")
                else None
            ),
        )


# Global configuration instance
config = ServerConfig.from_env()
