"""
ISA MCP Package - MCP Client for service-to-service communication

Usage:
    from isa_mcp import MCPClient, AsyncMCPClient

    # Or
    from isa_mcp.mcp_client import MCPClient, AsyncMCPClient

Install:
    pip install -e /path/to/isA_MCP
"""

from .mcp_client import (
    MCPClient,
    AsyncMCPClient,
    MCPClientError,
    MCPConnectionError,
    MCPToolError,
    SearchResult,
    ToolMatch,
)

__all__ = [
    "MCPClient",
    "AsyncMCPClient",
    "MCPClientError",
    "MCPConnectionError",
    "MCPToolError",
    "SearchResult",
    "ToolMatch",
]

__version__ = "0.1.0"
