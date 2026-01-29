"""MCP Tools package.

This package organizes MCP tools by functionality:
- project: Project scanning and management
- stats: Statistics and analysis
- context: Related code context (Repo Map)
- enhanced: New enhanced tools (call chain, entry points, symbol search)
- guide: Tool documentation and usage guide (lazy-loading)
"""

from .project import register_project_tools
from .stats import register_stats_tools
from .context import register_context_tools
from .enhanced import register_enhanced_tools
from .guide import register_guide_tools

__all__ = [
    "register_project_tools",
    "register_stats_tools",
    "register_context_tools",
    "register_enhanced_tools",
    "register_guide_tools",
]
