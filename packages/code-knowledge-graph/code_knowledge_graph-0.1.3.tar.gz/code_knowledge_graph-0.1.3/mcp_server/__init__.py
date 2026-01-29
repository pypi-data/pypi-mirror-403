"""MCP Server for Code Knowledge Graph.

This module provides Model Context Protocol (MCP) server
for AI tool integration with code knowledge graph features.

Usage:
    python -m mcp_server.run
    
Or with FastMCP CLI:
    fastmcp run mcp_server/run.py
"""

from .tools import (
    register_project_tools,
    register_stats_tools,
    register_context_tools,
    register_enhanced_tools,
    register_guide_tools,
)

__all__ = [
    "register_project_tools",
    "register_stats_tools",
    "register_context_tools",
    "register_enhanced_tools",
    "register_guide_tools",
]
