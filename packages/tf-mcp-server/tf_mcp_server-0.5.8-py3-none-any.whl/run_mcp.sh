#!/bin/bash
# Wrapper script to run the MCP server with correct Python path
cd "$(dirname "$0")/.."
exec ./tf_mcp_server/venv/bin/python -m tf_mcp_server.server "$@"
