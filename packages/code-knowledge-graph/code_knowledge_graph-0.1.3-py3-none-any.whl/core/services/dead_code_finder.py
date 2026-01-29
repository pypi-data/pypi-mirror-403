"""Dead Code Finder Service.

This module implements dead code detection by analyzing reachability
from entry points through the call graph.

Detection types:
- unused_functions: Functions/methods never called
- unused_types: Types/classes never instantiated or referenced
- unused_constants: Constants never used
- unreferenced_files: Files with no incoming imports

Feature: code-knowledge-graph-enhancement
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Set

from core.storage.sqlite import SQLiteStorage

logger = logging.getLogger(__name__)


@dataclass
class DeadCodeItem:
    """A single dead code item."""
    name: str
    file_path: str
    line_number: int
    item_type: str  # function, method, class, struct, constant, file
    reason: str  # Why it's considered dead
    confidence: str  # high, medium, low


@dataclass
class DeadCodeStats:
    """Statistics for dead code detection."""
    total_symbols: int
    reachable_symbols: int
    unreachable_symbols: int
    unreferenced_files: int
    entry_points_found: int


@dataclass
class DeadCodeResult:
    """Result of dead code detection."""
    project_path: str
    dead_code: list[DeadCodeItem]
    stats: DeadCodeStats
    by_type: dict[str, list[DeadCodeItem]]
    entry_points: list[str]  # Entry points used for reachability
    message: Optional[str] = None


class DeadCodeFinder:
    """Service for finding dead (unreachable) code.

    Uses call graph traversal from entry points to find unreachable code:
    1. Identify entry points (main functions, HTTP handlers, CLI commands)
    2. Traverse call graph to mark reachable symbols
    3. Report unreachable symbols as dead code
    """

    # Entry point patterns
    ENTRY_POINT_PATTERNS = {
        # Go entry points
        "main": ["main"],
        "init": ["init"],
        "http_handler": ["Handler", "ServeHTTP", "HandleFunc"],
        "test": ["Test", "Benchmark"],

        # Python entry points
        "python_main": ["main", "__main__"],
        "django_view": ["View", "APIView", "ViewSet"],
        "flask_route": ["route"],

        # Generic patterns
        "exported": [],  # Exported symbols (is_exported=True) are considered entry points
    }

    def __init__(self, storage: SQLiteStorage):
        """Initialize dead code finder.

        Args:
            storage: SQLite storage backend instance
        """
        self.storage = storage

    def find_dead_code(
        self,
        project_path: str,
        include_exported: bool = False,
        include_tests: bool = False,
        confidence_threshold: str = "medium"
    ) -> DeadCodeResult:
        """Find dead (unreachable) code in the project.

        Args:
            project_path: Path to the project
            include_exported: Whether to include exported symbols as potential dead code
            include_tests: Whether to include test files in analysis
            confidence_threshold: Minimum confidence level to report ("low", "medium", "high")

        Returns:
            DeadCodeResult containing dead code items
        """
        # Get project
        project = self.storage.get_project(project_path)
        if not project:
            return DeadCodeResult(
                project_path=project_path,
                dead_code=[],
                stats=DeadCodeStats(0, 0, 0, 0, 0),
                by_type={},
                entry_points=[],
                message=f"Project not found: {project_path}"
            )

        cursor = self.storage._get_cursor()

        # Get all symbols in the project
        cursor.execute(
            """
            SELECT
                s.id,
                s.name,
                s.symbol_type,
                s.container_name,
                s.start_line,
                s.is_exported,
                f.relative_path
            FROM symbols s
            JOIN files f ON s.file_id = f.id
            WHERE f.project_id = ?
            """,
            (project.id,)
        )
        all_symbols = cursor.fetchall()

        # Filter out test files if requested
        if not include_tests:
            all_symbols = [
                s for s in all_symbols
                if not self._is_test_file(s["relative_path"])
            ]

        if not all_symbols:
            return DeadCodeResult(
                project_path=project_path,
                dead_code=[],
                stats=DeadCodeStats(0, 0, 0, 0, 0),
                by_type={},
                entry_points=[],
                message="No symbols found in the project"
            )

        # Build symbol lookup
        symbol_by_id = {s["id"]: s for s in all_symbols}
        symbol_by_name: dict[str, list] = {}
        for s in all_symbols:
            name = s["name"]
            if name not in symbol_by_name:
                symbol_by_name[name] = []
            symbol_by_name[name].append(s)

        # Find entry points
        entry_point_ids: Set[int] = set()
        entry_point_names: list[str] = []

        for symbol in all_symbols:
            if self._is_entry_point(symbol, include_exported):
                entry_point_ids.add(symbol["id"])
                entry_point_names.append(f"{symbol['relative_path']}:{symbol['name']}")

        # Build call graph (caller -> callee)
        cursor.execute(
            """
            SELECT
                source_symbol_id,
                target_symbol_id,
                target_symbol_name
            FROM enhanced_function_calls
            WHERE source_symbol_id IN (
                SELECT s.id FROM symbols s
                JOIN files f ON s.file_id = f.id
                WHERE f.project_id = ?
            )
            """,
            (project.id,)
        )
        call_edges = cursor.fetchall()

        # Build adjacency list
        call_graph: dict[int, Set[int]] = {}
        for edge in call_edges:
            source_id = edge["source_symbol_id"]
            target_id = edge["target_symbol_id"]
            target_name = edge["target_symbol_name"]

            if source_id not in call_graph:
                call_graph[source_id] = set()

            # Add resolved target
            if target_id:
                call_graph[source_id].add(target_id)
            else:
                # Try to resolve by name
                if target_name in symbol_by_name:
                    for target_symbol in symbol_by_name[target_name]:
                        call_graph[source_id].add(target_symbol["id"])

        # Traverse call graph from entry points (BFS)
        reachable: Set[int] = set(entry_point_ids)
        queue = list(entry_point_ids)

        while queue:
            current = queue.pop(0)
            for callee_id in call_graph.get(current, set()):
                if callee_id not in reachable:
                    reachable.add(callee_id)
                    queue.append(callee_id)

        # Find dead code (unreachable symbols)
        dead_code: list[DeadCodeItem] = []
        by_type: dict[str, list[DeadCodeItem]] = {
            "function": [],
            "method": [],
            "class": [],
            "struct": [],
            "interface": [],
            "constant": [],
            "variable": []
        }

        confidence_levels = {"low": 0, "medium": 1, "high": 2}
        min_confidence = confidence_levels.get(confidence_threshold, 1)

        for symbol in all_symbols:
            symbol_id = symbol["id"]
            if symbol_id in reachable:
                continue

            # Skip exported symbols if not included
            if symbol["is_exported"] and not include_exported:
                continue

            # Determine confidence level
            confidence = self._get_confidence(symbol, reachable, call_graph)
            if confidence_levels.get(confidence, 0) < min_confidence:
                continue

            item = DeadCodeItem(
                name=symbol["name"],
                file_path=symbol["relative_path"],
                line_number=symbol["start_line"] or 0,
                item_type=symbol["symbol_type"],
                reason=self._get_reason(symbol, entry_point_ids),
                confidence=confidence
            )

            dead_code.append(item)

            # Categorize by type
            symbol_type = symbol["symbol_type"]
            if symbol_type in by_type:
                by_type[symbol_type].append(item)
            else:
                by_type["function"].append(item)  # Default bucket

        # Find unreferenced files
        cursor.execute(
            """
            SELECT f.relative_path
            FROM files f
            WHERE f.project_id = ?
              AND f.id NOT IN (
                  SELECT DISTINCT resolved_file_id FROM imports
                  WHERE resolved_file_id IS NOT NULL
              )
            """,
            (project.id,)
        )
        unreferenced_files_count = len(cursor.fetchall())

        # Build stats
        stats = DeadCodeStats(
            total_symbols=len(all_symbols),
            reachable_symbols=len(reachable),
            unreachable_symbols=len(all_symbols) - len(reachable),
            unreferenced_files=unreferenced_files_count,
            entry_points_found=len(entry_point_ids)
        )

        # Sort by file path and line number
        dead_code.sort(key=lambda x: (x.file_path, x.line_number))

        return DeadCodeResult(
            project_path=project_path,
            dead_code=dead_code,
            stats=stats,
            by_type={k: v for k, v in by_type.items() if v},
            entry_points=entry_point_names[:20],  # Limit to first 20
            message=None
        )

    def _is_entry_point(self, symbol: dict, include_exported: bool) -> bool:
        """Check if a symbol is an entry point.

        Args:
            symbol: Symbol dictionary
            include_exported: Whether exported symbols are entry points

        Returns:
            True if symbol is an entry point
        """
        name = symbol["name"]
        symbol_type = symbol["symbol_type"]

        # Main function
        if name == "main" and symbol_type == "function":
            return True

        # Init function (Go)
        if name == "init" and symbol_type == "function":
            return True

        # Test functions
        if name.startswith("Test") or name.startswith("Benchmark"):
            return True

        # HTTP handlers (common patterns)
        http_patterns = ["Handler", "ServeHTTP", "handle", "Handle"]
        if any(pattern in name for pattern in http_patterns):
            return True

        # Django/Flask views
        if name.endswith("View") or name.endswith("APIView"):
            return True

        # Exported symbols (if requested)
        if include_exported and symbol["is_exported"]:
            return True

        # Interface implementations are reachable
        if symbol_type == "interface":
            return True

        return False

    def _is_test_file(self, file_path: str) -> bool:
        """Check if a file is a test file.

        Args:
            file_path: File path

        Returns:
            True if test file
        """
        path_lower = file_path.lower()
        name = Path(file_path).name.lower()

        return (
            "test" in path_lower or
            name.startswith("test_") or
            name.endswith("_test.py") or
            name.endswith("_test.go") or
            name.endswith(".test.ts") or
            name.endswith(".test.js") or
            name.endswith(".spec.ts") or
            name.endswith(".spec.js")
        )

    def _get_confidence(
        self,
        symbol: dict,
        reachable: Set[int],
        call_graph: dict[int, Set[int]]
    ) -> str:
        """Determine confidence level for dead code classification.

        Args:
            symbol: Symbol dictionary
            reachable: Set of reachable symbol IDs
            call_graph: Call graph

        Returns:
            Confidence level: "low", "medium", "high"
        """
        symbol_id = symbol["id"]
        name = symbol["name"]
        symbol_type = symbol["symbol_type"]

        # High confidence: Private/internal symbols with no calls
        if not symbol["is_exported"]:
            # Check if anything calls this symbol
            called_by_count = sum(
                1 for callees in call_graph.values()
                if symbol_id in callees
            )
            if called_by_count == 0:
                return "high"

        # Medium confidence: Has some suspicious patterns
        if name.startswith("_") or name.startswith("unused"):
            return "high"

        if symbol_type in ("function", "method"):
            return "medium"

        # Low confidence: Could be used dynamically
        return "low"

    def _get_reason(self, symbol: dict, entry_points: Set[int]) -> str:
        """Get reason why symbol is considered dead.

        Args:
            symbol: Symbol dictionary
            entry_points: Set of entry point IDs

        Returns:
            Reason string
        """
        symbol_type = symbol["symbol_type"]
        is_exported = symbol["is_exported"]

        if symbol_type in ("function", "method"):
            if is_exported:
                return "Exported but not called from any entry point"
            return "Private function with no callers"
        elif symbol_type in ("class", "struct"):
            return "Type never instantiated or referenced"
        elif symbol_type == "interface":
            return "Interface never implemented"
        elif symbol_type in ("constant", "variable"):
            return "Never referenced in code"

        return "Not reachable from any entry point"

    def to_dict(self, result: DeadCodeResult) -> dict:
        """Convert result to dictionary for JSON serialization.

        Args:
            result: DeadCodeResult

        Returns:
            Dictionary representation
        """
        return {
            "project_path": result.project_path,
            "dead_code": [
                {
                    "name": item.name,
                    "file_path": item.file_path,
                    "line_number": item.line_number,
                    "item_type": item.item_type,
                    "reason": item.reason,
                    "confidence": item.confidence
                }
                for item in result.dead_code
            ],
            "stats": {
                "total_symbols": result.stats.total_symbols,
                "reachable_symbols": result.stats.reachable_symbols,
                "unreachable_symbols": result.stats.unreachable_symbols,
                "unreferenced_files": result.stats.unreferenced_files,
                "entry_points_found": result.stats.entry_points_found
            },
            "by_type": {
                type_name: [
                    {
                        "name": item.name,
                        "file_path": item.file_path,
                        "line_number": item.line_number,
                        "confidence": item.confidence
                    }
                    for item in items
                ]
                for type_name, items in result.by_type.items()
            },
            "entry_points": result.entry_points,
            "message": result.message
        }
