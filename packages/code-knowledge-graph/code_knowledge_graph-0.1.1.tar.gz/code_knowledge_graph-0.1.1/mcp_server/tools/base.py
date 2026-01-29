"""Base utilities for MCP tools.

Provides shared services and utilities for all MCP tools.
"""

from pathlib import Path
from typing import Optional

from core.storage import SQLiteStorage
from core.services import (
    StatsService,
    ProjectService,
    FunctionAnalysisService,
    RelatedContextService,
)

# Lazy-initialized services
_storage: Optional[SQLiteStorage] = None
_stats_service: Optional[StatsService] = None
_project_service: Optional[ProjectService] = None
_function_analysis: Optional[FunctionAnalysisService] = None


def get_storage() -> SQLiteStorage:
    """Get or create storage instance."""
    global _storage
    if _storage is None:
        db_path = Path(__file__).parent.parent.parent / "code_knowledge.db"
        _storage = SQLiteStorage(str(db_path))
    return _storage


def get_stats_service() -> StatsService:
    """Get or create stats service."""
    global _stats_service
    if _stats_service is None:
        _stats_service = StatsService(get_storage())
    return _stats_service


def get_project_service() -> ProjectService:
    """Get or create project service."""
    global _project_service
    if _project_service is None:
        _project_service = ProjectService(get_storage())
    return _project_service


def get_function_analysis() -> FunctionAnalysisService:
    """Get or create function analysis service."""
    global _function_analysis
    if _function_analysis is None:
        _function_analysis = FunctionAnalysisService()
    return _function_analysis


def filter_external_deps(data: dict, include_external: bool) -> dict:
    """Filter external dependencies from result data.
    
    Args:
        data: Result dictionary that may contain external dependencies
        include_external: If False, filter out external dependencies
        
    Returns:
        Filtered data dictionary
    """
    if include_external:
        return data
    
    # Filter relations if present
    if "relations" in data:
        data["relations"] = [
            r for r in data["relations"]
            if not r.get("is_external", False)
        ]
    
    # Filter external_calls if present
    if "external_calls" in data:
        data["external_calls"] = [] if not include_external else data["external_calls"]
    
    # Filter external_deps if present
    if "external_deps" in data and not include_external:
        data["external_deps"] = []
    
    return data
