"""Symbol Search Service for code knowledge graph.

This module implements high-performance symbol search using FTS5 full-text search
with BM25 scoring, supporting exact match, prefix match, and fuzzy search.

Feature: code-knowledge-graph-enhancement
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from core.storage.sqlite import SQLiteStorage

logger = logging.getLogger(__name__)


class SymbolType(Enum):
    """Symbol type enumeration.
    
    Represents different types of code symbols that can be searched.
    """
    FUNCTION = "function"
    CLASS = "class"
    METHOD = "method"
    VARIABLE = "variable"
    STRUCT = "struct"
    INTERFACE = "interface"


@dataclass
class SymbolSearchResult:
    """Symbol search result.
    
    Represents a single symbol found during search, including its metadata
    and match score for ranking.
    
    Attributes:
        name: Symbol name
        symbol_type: Type of the symbol (function, class, method, etc.)
        file_path: Relative path to the file containing the symbol
        line_number: Line number where the symbol is defined
        signature: Full signature of the symbol
        docstring: Documentation string if available
        container_name: Name of the containing class/struct if applicable
        is_exported: Whether the symbol is exported (for Go symbols)
        match_score: Score used for ranking results
    """
    name: str
    symbol_type: SymbolType
    file_path: str
    line_number: int
    signature: str
    docstring: Optional[str] = None
    container_name: Optional[str] = None
    is_exported: Optional[bool] = None
    match_score: float = 1.0


@dataclass
class SymbolSearchResponse:
    """Symbol search response.
    
    Contains the search results and metadata about the search operation.
    
    Attributes:
        query: The original search query
        results: List of matching symbols
        total_count: Total number of matches found
        truncated: Whether results were truncated due to limit
    """
    query: str
    results: list[SymbolSearchResult] = field(default_factory=list)
    total_count: int = 0
    truncated: bool = False


class SymbolSearchService:
    """Symbol search service using FTS5 full-text search.
    
    Provides high-performance symbol search with:
    - Exact match search
    - Prefix match search using FTS5
    - BM25 relevance scoring
    - Weighted result sorting
    
    Search priority:
    1. Exact match > Prefix match > Contains match
    2. Class/Struct/Interface > Function > Method > Variable
    3. Exported symbols > Private symbols
    """
    
    # FTS5 search query with BM25 scoring
    # Weights: name=10.0, signature=5.0, docstring=1.0
    FTS5_SEARCH_QUERY = """
    SELECT 
        s.id,
        s.name,
        s.symbol_type,
        s.signature,
        s.docstring,
        s.container_name,
        s.start_line,
        s.is_exported,
        f.relative_path as file_path,
        bm25(symbols_fts, 10.0, 5.0, 1.0) as relevance_score
    FROM symbols_fts
    JOIN symbols s ON symbols_fts.rowid = s.id
    JOIN files f ON s.file_id = f.id
    WHERE f.project_id = :project_id
      AND symbols_fts MATCH :query
      {type_filter}
    ORDER BY relevance_score
    LIMIT :limit;
    """
    
    # Exact match query for case-sensitive/insensitive search
    EXACT_MATCH_QUERY = """
    SELECT 
        s.id,
        s.name,
        s.symbol_type,
        s.signature,
        s.docstring,
        s.container_name,
        s.start_line,
        s.is_exported,
        f.relative_path as file_path,
        1.0 as relevance_score
    FROM symbols s
    JOIN files f ON s.file_id = f.id
    WHERE f.project_id = :project_id
      AND (
          (:case_sensitive = 1 AND s.name = :query)
          OR (:case_sensitive = 0 AND LOWER(s.name) = LOWER(:query))
      )
      {type_filter}
    LIMIT :limit;
    """
    
    def __init__(self, storage: SQLiteStorage):
        """Initialize symbol search service.
        
        Args:
            storage: SQLite storage backend instance
        """
        self.storage = storage
    
    def search(
        self,
        project_path: str,
        query: str,
        symbol_types: Optional[list[SymbolType]] = None,
        case_sensitive: bool = False,
        prefix_match: bool = True,
        limit: int = 50
    ) -> SymbolSearchResponse:
        """Search for symbols in a project.
        
        Search strategy:
        1. First perform exact match query
        2. Then use FTS5 for prefix/fuzzy matching
        3. Merge results with exact matches first
        4. Apply weighted sorting
        
        Args:
            project_path: Path to the project
            query: Search query string
            symbol_types: Optional list of symbol types to filter
            case_sensitive: Whether to perform case-sensitive search
            prefix_match: Whether to enable prefix matching
            limit: Maximum number of results to return
            
        Returns:
            SymbolSearchResponse containing matching symbols
        """
        if not query or not query.strip():
            return SymbolSearchResponse(
                query=query,
                results=[],
                total_count=0
            )
        
        query = query.strip()
        
        project = self.storage.get_project(project_path)
        if not project:
            logger.warning(f"Project not found: {project_path}")
            return SymbolSearchResponse(
                query=query,
                results=[],
                total_count=0
            )
        
        results: list[SymbolSearchResult] = []
        seen_keys: set[str] = set()
        
        # 1. Exact match search
        exact_results = self._search_exact(
            project.id, query, symbol_types, case_sensitive, limit
        )
        for result in exact_results:
            key = f"{result.name}:{result.file_path}:{result.line_number}"
            if key not in seen_keys:
                results.append(result)
                seen_keys.add(key)
        
        # 2. FTS5 prefix match (if enabled and need more results)
        if prefix_match and len(results) < limit:
            # FTS5 prefix syntax: query*
            fts_query = f"{query}*"
            fts_results = self._search_fts5(
                project.id, fts_query, symbol_types, limit - len(results)
            )
            for result in fts_results:
                key = f"{result.name}:{result.file_path}:{result.line_number}"
                if key not in seen_keys:
                    results.append(result)
                    seen_keys.add(key)
        
        # 3. Apply weighted sorting
        results = self._sort_results(results, query)
        
        # 4. Truncate if needed
        total_count = len(results)
        truncated = total_count > limit
        results = results[:limit]
        
        return SymbolSearchResponse(
            query=query,
            results=results,
            total_count=total_count,
            truncated=truncated
        )
    
    def _search_exact(
        self,
        project_id: int,
        query: str,
        symbol_types: Optional[list[SymbolType]],
        case_sensitive: bool,
        limit: int
    ) -> list[SymbolSearchResult]:
        """Perform exact match search.
        
        Args:
            project_id: Project ID
            query: Search query
            symbol_types: Optional symbol type filter
            case_sensitive: Whether to match case
            limit: Maximum results
            
        Returns:
            List of matching SymbolSearchResult objects
        """
        cursor = self.storage._get_cursor()
        
        # Build type filter clause
        type_filter = ""
        params: dict = {
            "project_id": project_id,
            "query": query,
            "case_sensitive": 1 if case_sensitive else 0,
            "limit": limit
        }
        
        if symbol_types:
            type_values = [t.value for t in symbol_types]
            placeholders = ", ".join(f":type_{i}" for i in range(len(type_values)))
            type_filter = f"AND s.symbol_type IN ({placeholders})"
            for i, t in enumerate(type_values):
                params[f"type_{i}"] = t
        
        sql = self.EXACT_MATCH_QUERY.format(type_filter=type_filter)
        
        try:
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                try:
                    symbol_type = SymbolType(row["symbol_type"])
                except ValueError:
                    # Unknown symbol type, skip
                    continue
                
                # Determine export status for Go symbols
                is_exported = self._determine_export_status(
                    row["name"],
                    row["file_path"],
                    row["is_exported"]
                )
                
                results.append(SymbolSearchResult(
                    name=row["name"],
                    symbol_type=symbol_type,
                    file_path=row["file_path"],
                    line_number=row["start_line"] or 0,
                    signature=row["signature"] or "",
                    docstring=row["docstring"],
                    container_name=row["container_name"],
                    is_exported=is_exported,
                    match_score=row["relevance_score"]
                ))
            
            return results
            
        except Exception as e:
            logger.error(f"Exact match search failed: {e}")
            return []
    
    def _search_fts5(
        self,
        project_id: int,
        fts_query: str,
        symbol_types: Optional[list[SymbolType]],
        limit: int
    ) -> list[SymbolSearchResult]:
        """Perform FTS5 full-text search with BM25 scoring.
        
        Args:
            project_id: Project ID
            fts_query: FTS5 query string (supports prefix with *)
            symbol_types: Optional symbol type filter
            limit: Maximum results
            
        Returns:
            List of matching SymbolSearchResult objects
        """
        cursor = self.storage._get_cursor()
        
        # Build type filter clause
        type_filter = ""
        params: dict = {
            "project_id": project_id,
            "query": fts_query,
            "limit": limit
        }
        
        if symbol_types:
            type_values = [t.value for t in symbol_types]
            placeholders = ", ".join(f":type_{i}" for i in range(len(type_values)))
            type_filter = f"AND s.symbol_type IN ({placeholders})"
            for i, t in enumerate(type_values):
                params[f"type_{i}"] = t
        
        sql = self.FTS5_SEARCH_QUERY.format(type_filter=type_filter)
        
        try:
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                try:
                    symbol_type = SymbolType(row["symbol_type"])
                except ValueError:
                    # Unknown symbol type, skip
                    continue
                
                # Determine export status for Go symbols
                is_exported = self._determine_export_status(
                    row["name"],
                    row["file_path"],
                    row["is_exported"]
                )
                
                results.append(SymbolSearchResult(
                    name=row["name"],
                    symbol_type=symbol_type,
                    file_path=row["file_path"],
                    line_number=row["start_line"] or 0,
                    signature=row["signature"] or "",
                    docstring=row["docstring"],
                    container_name=row["container_name"],
                    is_exported=is_exported,
                    match_score=abs(row["relevance_score"])  # BM25 returns negative scores
                ))
            
            return results
            
        except Exception as e:
            logger.error(f"FTS5 search failed: {e}")
            return []
    
    def _sort_results(
        self,
        results: list[SymbolSearchResult],
        query: str
    ) -> list[SymbolSearchResult]:
        """Apply weighted sorting to search results.
        
        Sorting rules:
        1. Match type: Exact match > Prefix match > Contains match
        2. Symbol type: Class/Struct/Interface > Function > Method > Variable
        3. Export status: Exported > Private
        
        Args:
            results: List of search results to sort
            query: Original search query for match comparison
            
        Returns:
            Sorted list of results
        """
        def sort_key(r: SymbolSearchResult) -> tuple:
            # 1. Match type score (lower is better)
            name_lower = r.name.lower()
            query_lower = query.lower()
            
            if name_lower == query_lower:
                match_score = 0  # Exact match
            elif name_lower.startswith(query_lower):
                match_score = 1  # Prefix match
            elif query_lower in name_lower:
                match_score = 2  # Contains match
            else:
                match_score = 3  # Other (signature/docstring match)
            
            # 2. Symbol type priority (lower is better)
            type_priority = {
                SymbolType.CLASS: 0,
                SymbolType.STRUCT: 0,
                SymbolType.INTERFACE: 0,
                SymbolType.FUNCTION: 1,
                SymbolType.METHOD: 2,
                SymbolType.VARIABLE: 3,
            }
            type_score = type_priority.get(r.symbol_type, 4)
            
            # 3. Export status (exported first, lower is better)
            export_score = 0 if r.is_exported else 1
            
            # 4. Alphabetical by name as tiebreaker
            return (match_score, type_score, export_score, r.name.lower())
        
        return sorted(results, key=sort_key)
    
    def _is_go_exported(self, symbol_name: str) -> bool:
        """Check if a Go symbol is exported (public).
        
        In Go, exported symbols start with an uppercase letter.
        
        Args:
            symbol_name: Name of the symbol
            
        Returns:
            True if the symbol is exported, False otherwise
        """
        if not symbol_name:
            return False
        return symbol_name[0].isupper()
    
    def _determine_export_status(
        self,
        name: str,
        file_path: str,
        stored_is_exported: Optional[bool]
    ) -> Optional[bool]:
        """Determine the export status of a symbol.
        
        For Go files, uses the naming convention (uppercase = exported).
        For other languages, uses the stored value or None.
        
        Args:
            name: Symbol name
            file_path: File path to determine language
            stored_is_exported: Stored export status from database
            
        Returns:
            Export status or None if not applicable
        """
        # Check if it's a Go file
        if file_path.endswith(".go"):
            return self._is_go_exported(name)
        
        # For other languages, return stored value
        return stored_is_exported
