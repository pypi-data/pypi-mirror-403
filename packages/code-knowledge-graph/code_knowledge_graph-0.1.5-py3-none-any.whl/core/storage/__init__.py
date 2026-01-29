"""Storage module for Code Knowledge Graph.

This module provides storage backends for persisting parsed project data.
"""

from .base import (
    StorageBackend,
    ProjectRecord,
    FileRecord,
    ImportRecord,
    FunctionRecord,
    FunctionCallRecord,
    CodeSummaryRecord,
    FileTypeStats,
    DepthStats,
    ReferenceRankingItem,
    SymbolRecord,
    EnhancedFunctionCallRecord,
    GoModuleRecord,
    ParseErrorRecord,
)
from .sqlite import SQLiteStorage

__all__ = [
    "StorageBackend",
    "SQLiteStorage",
    "ProjectRecord",
    "FileRecord",
    "ImportRecord",
    "FunctionRecord",
    "FunctionCallRecord",
    "CodeSummaryRecord",
    "FileTypeStats",
    "DepthStats",
    "ReferenceRankingItem",
    "SymbolRecord",
    "EnhancedFunctionCallRecord",
    "GoModuleRecord",
    "ParseErrorRecord",
]
