"""Dependency Analysis Service for code knowledge graph.

This module implements dependency analysis features including:
- Circular dependency detection
- Import graph generation
- Change impact analysis

Feature: code-knowledge-graph-enhancement
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

from core.storage.sqlite import SQLiteStorage

logger = logging.getLogger(__name__)


class DependencyScope(str, Enum):
    """Scope for dependency analysis."""
    FILE = "file"
    MODULE = "module"  # Directory level
    PACKAGE = "package"  # Top-level package


class ImportScope(str, Enum):
    """Scope for import graph filtering."""
    INTERNAL = "internal"  # Only internal project files
    EXTERNAL = "external"  # Only external dependencies
    ALL = "all"  # Both internal and external


class GroupBy(str, Enum):
    """Grouping level for import graph."""
    FILE = "file"
    DIRECTORY = "directory"
    PACKAGE = "package"  # Top-level directory


@dataclass
class CircularDependencyResult:
    """Result of circular dependency detection."""
    project_path: str
    scope: str
    cycles: list[list[str]]  # Each cycle is a list of file/module paths
    count: int
    message: Optional[str] = None


@dataclass
class ImportGraphNode:
    """A node in the import graph."""
    id: str  # File path or module name
    node_type: str  # "python", "typescript", "go", etc.
    file_count: int = 1  # Number of files (for grouped nodes)


@dataclass
class ImportGraphEdge:
    """An edge in the import graph."""
    from_node: str
    to_node: str
    edge_type: str = "static"  # static, dynamic
    weight: int = 1  # Number of import statements


@dataclass
class ImportGraphResult:
    """Result of import graph generation."""
    project_path: str
    scope: str
    group_by: str
    nodes: list[ImportGraphNode]
    edges: list[ImportGraphEdge]
    external: list[str]  # List of external dependencies
    message: Optional[str] = None


@dataclass
class ChangeImpactResult:
    """Result of change impact analysis."""
    project_path: str
    modified_files: list[str]
    directly_affected: list[str]  # Files that directly import modified files
    indirectly_affected: list[str]  # Files affected through transitive imports
    affected_tests: list[str]  # Test files that may be affected
    total_files_at_risk: int
    message: Optional[str] = None


class DependencyAnalysisService:
    """Service for dependency analysis operations.

    Provides methods for:
    - Detecting circular dependencies at various scopes
    - Generating import graphs with filtering options
    - Analyzing change impact for modified files
    """

    def __init__(self, storage: SQLiteStorage):
        """Initialize dependency analysis service.

        Args:
            storage: SQLite storage backend instance
        """
        self.storage = storage

    def detect_circular_deps(
        self,
        project_path: str,
        scope: str = "file"
    ) -> CircularDependencyResult:
        """Detect circular dependencies in the project.

        Uses DFS with visited set to find all cycles in the import graph.

        Args:
            project_path: Path to the project
            scope: Detection scope - "file", "module", or "package"

        Returns:
            CircularDependencyResult containing all detected cycles
        """
        # Validate scope
        try:
            dep_scope = DependencyScope(scope)
        except ValueError:
            return CircularDependencyResult(
                project_path=project_path,
                scope=scope,
                cycles=[],
                count=0,
                message=f"Invalid scope: {scope}. Must be 'file', 'module', or 'package'"
            )

        # Get project
        project = self.storage.get_project(project_path)
        if not project:
            return CircularDependencyResult(
                project_path=project_path,
                scope=scope,
                cycles=[],
                count=0,
                message=f"Project not found: {project_path}"
            )

        # Build adjacency list for the import graph
        adj_list = self._build_import_adjacency_list(project.id, dep_scope)

        if not adj_list:
            return CircularDependencyResult(
                project_path=project_path,
                scope=scope,
                cycles=[],
                count=0,
                message="No imports found in the project"
            )

        # Find all cycles using DFS
        cycles = self._find_all_cycles(adj_list)

        return CircularDependencyResult(
            project_path=project_path,
            scope=scope,
            cycles=cycles,
            count=len(cycles),
            message=None
        )

    def _build_import_adjacency_list(
        self,
        project_id: int,
        scope: DependencyScope
    ) -> dict[str, set[str]]:
        """Build adjacency list for import relationships.

        Args:
            project_id: Project ID
            scope: Dependency scope for grouping

        Returns:
            Dictionary mapping source node to set of target nodes
        """
        cursor = self.storage._get_cursor()

        # Get all internal imports with resolved targets
        cursor.execute(
            """
            SELECT
                sf.relative_path as source_path,
                tf.relative_path as target_path
            FROM imports i
            JOIN files sf ON i.file_id = sf.id
            JOIN files tf ON i.resolved_file_id = tf.id
            WHERE sf.project_id = ?
              AND tf.project_id = ?
              AND i.resolved_file_id IS NOT NULL
            """,
            (project_id, project_id)
        )

        rows = cursor.fetchall()

        adj_list: dict[str, set[str]] = {}

        for row in rows:
            source = self._normalize_path_by_scope(row["source_path"], scope)
            target = self._normalize_path_by_scope(row["target_path"], scope)

            if source == target:
                continue  # Skip self-imports

            if source not in adj_list:
                adj_list[source] = set()
            adj_list[source].add(target)

        return adj_list

    def _normalize_path_by_scope(
        self,
        path: str,
        scope: DependencyScope
    ) -> str:
        """Normalize a file path based on the scope.

        Args:
            path: File relative path
            scope: Dependency scope

        Returns:
            Normalized path/identifier
        """
        if scope == DependencyScope.FILE:
            return path

        parts = Path(path).parts

        if scope == DependencyScope.MODULE:
            # Return directory path (parent of file)
            if len(parts) > 1:
                return str(Path(*parts[:-1]))
            return parts[0] if parts else path

        if scope == DependencyScope.PACKAGE:
            # Return top-level package (first directory)
            return parts[0] if parts else path

        return path

    def _find_all_cycles(
        self,
        adj_list: dict[str, set[str]]
    ) -> list[list[str]]:
        """Find all cycles in the graph using DFS.

        Uses Johnson's algorithm variant for finding all elementary cycles.

        Args:
            adj_list: Adjacency list representation of the graph

        Returns:
            List of cycles, each cycle is a list of nodes
        """
        cycles: list[list[str]] = []
        visited: set[str] = set()
        rec_stack: list[str] = []
        rec_set: set[str] = set()

        def dfs(node: str, start: str) -> None:
            """DFS to find cycles starting from 'start'."""
            visited.add(node)
            rec_stack.append(node)
            rec_set.add(node)

            for neighbor in adj_list.get(node, []):
                if neighbor == start and len(rec_stack) > 1:
                    # Found a cycle back to start
                    cycle = rec_stack.copy()
                    cycle.append(start)
                    # Normalize cycle to start from smallest element
                    min_idx = cycle.index(min(cycle[:-1]))
                    normalized = cycle[min_idx:-1] + cycle[:min_idx] + [cycle[min_idx]]
                    if normalized not in cycles:
                        cycles.append(normalized)
                elif neighbor not in rec_set and neighbor not in visited:
                    dfs(neighbor, start)

            rec_stack.pop()
            rec_set.remove(node)

        # Start DFS from each node
        all_nodes = set(adj_list.keys())
        for targets in adj_list.values():
            all_nodes.update(targets)

        for node in sorted(all_nodes):
            visited.clear()
            rec_stack.clear()
            rec_set.clear()
            dfs(node, node)

        # Remove duplicate cycles
        unique_cycles = []
        seen_cycles = set()
        for cycle in cycles:
            cycle_key = tuple(cycle)
            if cycle_key not in seen_cycles:
                seen_cycles.add(cycle_key)
                unique_cycles.append(cycle)

        return unique_cycles

    def get_import_graph(
        self,
        project_path: str,
        scope: str = "internal",
        group_by: str = "file",
        target_file: Optional[str] = None,
        direction: str = "both",
        depth: int = 2
    ) -> ImportGraphResult:
        """Generate import relationship graph.

        Args:
            project_path: Path to the project
            scope: Import scope - "internal", "external", or "all"
            group_by: Grouping level - "file", "directory", or "package"
            target_file: Optional file path to focus the graph on.
                         If provided, only shows files within 'depth' hops.
            direction: Direction for target_file traversal -
                       "imports" (what target imports),
                       "imported_by" (what imports target),
                       "both" (bidirectional)
            depth: Maximum hops from target_file (only used with target_file)

        Returns:
            ImportGraphResult containing nodes and edges
        """
        # Validate parameters
        try:
            import_scope = ImportScope(scope)
        except ValueError:
            return ImportGraphResult(
                project_path=project_path,
                scope=scope,
                group_by=group_by,
                nodes=[],
                edges=[],
                external=[],
                message=f"Invalid scope: {scope}. Must be 'internal', 'external', or 'all'"
            )

        try:
            group_level = GroupBy(group_by)
        except ValueError:
            return ImportGraphResult(
                project_path=project_path,
                scope=scope,
                group_by=group_by,
                nodes=[],
                edges=[],
                external=[],
                message=f"Invalid group_by: {group_by}. Must be 'file', 'directory', or 'package'"
            )

        if direction not in ("imports", "imported_by", "both"):
            return ImportGraphResult(
                project_path=project_path,
                scope=scope,
                group_by=group_by,
                nodes=[],
                edges=[],
                external=[],
                message=f"Invalid direction: {direction}. Must be 'imports', 'imported_by', or 'both'"
            )

        # Validate and clamp depth
        depth = max(1, min(10, depth))

        # Get project
        project = self.storage.get_project(project_path)
        if not project:
            return ImportGraphResult(
                project_path=project_path,
                scope=scope,
                group_by=group_by,
                nodes=[],
                edges=[],
                external=[],
                message=f"Project not found: {project_path}"
            )

        cursor = self.storage._get_cursor()

        # Get all files and their types
        cursor.execute(
            "SELECT relative_path, file_type FROM files WHERE project_id = ?",
            (project.id,)
        )
        file_info = {row["relative_path"]: row["file_type"] for row in cursor.fetchall()}

        # If target_file is specified, verify it exists
        if target_file and target_file not in file_info:
            return ImportGraphResult(
                project_path=project_path,
                scope=scope,
                group_by=group_by,
                nodes=[],
                edges=[],
                external=[],
                message=f"Target file not found: {target_file}"
            )

        # Get all imports
        cursor.execute(
            """
            SELECT
                sf.relative_path as source_path,
                sf.file_type as source_type,
                i.module as import_module,
                i.import_type,
                i.resolved_file_id,
                tf.relative_path as target_path,
                tf.file_type as target_type
            FROM imports i
            JOIN files sf ON i.file_id = sf.id
            LEFT JOIN files tf ON i.resolved_file_id = tf.id
            WHERE sf.project_id = ?
            """,
            (project.id,)
        )

        rows = cursor.fetchall()

        # Build adjacency lists for BFS (if target_file is specified)
        imports_adj: dict[str, set[str]] = {}  # file -> files it imports
        imported_by_adj: dict[str, set[str]] = {}  # file -> files that import it

        # Build nodes and edges
        nodes_dict: dict[str, ImportGraphNode] = {}
        edges_dict: dict[tuple[str, str], ImportGraphEdge] = {}
        external_deps: set[str] = set()

        for row in rows:
            source_path = row["source_path"]
            source_type = row["source_type"]
            target_path = row["target_path"]
            import_module = row["import_module"]

            # Determine if import is internal or external
            is_internal = target_path is not None

            # Build adjacency lists for internal imports
            if is_internal:
                # imports_adj: source imports target
                if source_path not in imports_adj:
                    imports_adj[source_path] = set()
                imports_adj[source_path].add(target_path)

                # imported_by_adj: target is imported by source
                if target_path not in imported_by_adj:
                    imported_by_adj[target_path] = set()
                imported_by_adj[target_path].add(source_path)

            # Apply scope filter
            if import_scope == ImportScope.INTERNAL and not is_internal:
                external_deps.add(import_module)
                continue
            elif import_scope == ImportScope.EXTERNAL and is_internal:
                continue

            # Normalize paths by grouping level
            source_key = self._normalize_path_by_group(source_path, group_level)

            if is_internal:
                target_key = self._normalize_path_by_group(target_path, group_level)
                target_type = row["target_type"]
            else:
                target_key = import_module
                target_type = "external"
                external_deps.add(import_module)

            if source_key == target_key:
                continue  # Skip self-references

            # Add source node
            if source_key not in nodes_dict:
                nodes_dict[source_key] = ImportGraphNode(
                    id=source_key,
                    node_type=source_type,
                    file_count=1 if group_level == GroupBy.FILE else 0
                )
            elif group_level != GroupBy.FILE:
                nodes_dict[source_key].file_count += 1

            # Add target node
            if target_key not in nodes_dict:
                nodes_dict[target_key] = ImportGraphNode(
                    id=target_key,
                    node_type=target_type if is_internal else "external",
                    file_count=1 if group_level == GroupBy.FILE else 0
                )
            elif group_level != GroupBy.FILE and is_internal:
                nodes_dict[target_key].file_count += 1

            # Add edge
            edge_key = (source_key, target_key)
            if edge_key not in edges_dict:
                edges_dict[edge_key] = ImportGraphEdge(
                    from_node=source_key,
                    to_node=target_key,
                    edge_type=row["import_type"] or "static",
                    weight=1
                )
            else:
                edges_dict[edge_key].weight += 1

        # Filter by target_file if specified
        if target_file:
            reachable_files = self._bfs_reachable_files(
                target_file,
                imports_adj,
                imported_by_adj,
                direction,
                depth
            )

            # Normalize reachable files to match grouping
            reachable_keys = {
                self._normalize_path_by_group(f, group_level)
                for f in reachable_files
            }

            # Filter nodes
            filtered_nodes = {
                k: v for k, v in nodes_dict.items()
                if k in reachable_keys
            }

            # Filter edges (both endpoints must be in reachable set)
            filtered_edges = {
                k: v for k, v in edges_dict.items()
                if k[0] in reachable_keys and k[1] in reachable_keys
            }

            nodes_dict = filtered_nodes
            edges_dict = filtered_edges

        return ImportGraphResult(
            project_path=project_path,
            scope=scope,
            group_by=group_by,
            nodes=list(nodes_dict.values()),
            edges=list(edges_dict.values()),
            external=sorted(external_deps),
            message=None
        )

    def _normalize_path_by_group(
        self,
        path: str,
        group_by: GroupBy
    ) -> str:
        """Normalize a file path based on grouping level.

        Args:
            path: File relative path
            group_by: Grouping level

        Returns:
            Normalized path/identifier
        """
        if group_by == GroupBy.FILE:
            return path

        parts = Path(path).parts

        if group_by == GroupBy.DIRECTORY:
            # Return directory path (parent of file)
            if len(parts) > 1:
                return str(Path(*parts[:-1]))
            return "."  # Root directory

        if group_by == GroupBy.PACKAGE:
            # Return top-level package (first directory)
            return parts[0] if parts else "."

        return path

    def _bfs_reachable_files(
        self,
        target_file: str,
        imports_adj: dict[str, set[str]],
        imported_by_adj: dict[str, set[str]],
        direction: str,
        depth: int
    ) -> set[str]:
        """Find all files reachable from target_file within depth hops.

        Uses BFS to traverse the import graph in the specified direction.

        Args:
            target_file: Starting file path
            imports_adj: Adjacency list for "imports" direction
            imported_by_adj: Adjacency list for "imported_by" direction
            direction: "imports", "imported_by", or "both"
            depth: Maximum number of hops

        Returns:
            Set of reachable file paths (including target_file)
        """
        from collections import deque

        reachable: set[str] = {target_file}
        queue: deque[tuple[str, int]] = deque([(target_file, 0)])

        while queue:
            current, current_depth = queue.popleft()

            if current_depth >= depth:
                continue

            neighbors: set[str] = set()

            # Collect neighbors based on direction
            if direction in ("imports", "both"):
                neighbors.update(imports_adj.get(current, set()))
            if direction in ("imported_by", "both"):
                neighbors.update(imported_by_adj.get(current, set()))

            for neighbor in neighbors:
                if neighbor not in reachable:
                    reachable.add(neighbor)
                    queue.append((neighbor, current_depth + 1))

        return reachable

    def analyze_change_impact(
        self,
        project_path: str,
        modified_files: list[str],
        depth: int = 3
    ) -> ChangeImpactResult:
        """Analyze the impact of file modifications.

        Traverses the reverse import graph to find all files that may be
        affected by changes to the specified files.

        Args:
            project_path: Path to the project
            modified_files: List of modified file paths (relative to project root)
            depth: Maximum depth of transitive impact analysis

        Returns:
            ChangeImpactResult containing affected files
        """
        # Validate depth
        depth = max(1, min(10, depth))

        # Get project
        project = self.storage.get_project(project_path)
        if not project:
            return ChangeImpactResult(
                project_path=project_path,
                modified_files=modified_files,
                directly_affected=[],
                indirectly_affected=[],
                affected_tests=[],
                total_files_at_risk=0,
                message=f"Project not found: {project_path}"
            )

        cursor = self.storage._get_cursor()

        # Build reverse import adjacency list (who imports this file)
        cursor.execute(
            """
            SELECT
                tf.relative_path as target_path,
                sf.relative_path as source_path
            FROM imports i
            JOIN files sf ON i.file_id = sf.id
            JOIN files tf ON i.resolved_file_id = tf.id
            WHERE sf.project_id = ?
              AND tf.project_id = ?
              AND i.resolved_file_id IS NOT NULL
            """,
            (project.id, project.id)
        )

        reverse_adj: dict[str, set[str]] = {}
        for row in cursor.fetchall():
            target = row["target_path"]
            source = row["source_path"]
            if target not in reverse_adj:
                reverse_adj[target] = set()
            reverse_adj[target].add(source)

        # Also build reverse adjacency by module name matching
        cursor.execute(
            """
            SELECT
                f.relative_path as file_path,
                i.module,
                sf.relative_path as source_path
            FROM imports i
            JOIN files sf ON i.file_id = sf.id
            JOIN files f ON f.project_id = sf.project_id
            WHERE sf.project_id = ?
              AND i.resolved_file_id IS NULL
              AND (
                  f.relative_path LIKE '%' || REPLACE(i.module, '.', '/') || '.py'
                  OR f.relative_path LIKE '%' || REPLACE(i.module, '.', '/') || '/__init__.py'
                  OR f.relative_path LIKE '%/' || i.module || '.py'
                  OR f.relative_path LIKE '%/' || i.module || '.ts'
                  OR f.relative_path LIKE '%/' || i.module || '.js'
                  OR f.relative_path LIKE '%/' || i.module || '.go'
              )
            """,
            (project.id,)
        )

        for row in cursor.fetchall():
            file_path = row["file_path"]
            source_path = row["source_path"]
            if file_path != source_path:
                if file_path not in reverse_adj:
                    reverse_adj[file_path] = set()
                reverse_adj[file_path].add(source_path)

        # Find affected files using BFS
        directly_affected: set[str] = set()
        indirectly_affected: set[str] = set()
        affected_tests: set[str] = set()

        modified_set = set(modified_files)
        visited: set[str] = set(modified_files)
        current_level = set(modified_files)

        for current_depth in range(depth):
            next_level: set[str] = set()

            for file_path in current_level:
                for importer in reverse_adj.get(file_path, []):
                    if importer not in visited:
                        visited.add(importer)
                        next_level.add(importer)

                        # Classify the affected file
                        if current_depth == 0:
                            directly_affected.add(importer)
                        else:
                            indirectly_affected.add(importer)

                        # Check if it's a test file
                        if self._is_test_file(importer):
                            affected_tests.add(importer)

            current_level = next_level
            if not current_level:
                break

        # Remove modified files from affected lists
        directly_affected -= modified_set
        indirectly_affected -= modified_set

        # Find affected tests using enhanced method
        all_affected = list(modified_set | directly_affected | indirectly_affected)
        affected_tests = self._find_affected_tests(
            project.id,
            all_affected,
            reverse_adj
        )

        total_at_risk = len(directly_affected) + len(indirectly_affected)

        return ChangeImpactResult(
            project_path=project_path,
            modified_files=modified_files,
            directly_affected=sorted(directly_affected),
            indirectly_affected=sorted(indirectly_affected),
            affected_tests=sorted(affected_tests),
            total_files_at_risk=total_at_risk,
            message=None
        )

    def _is_test_file(self, file_path: str) -> bool:
        """Check if a file is a test file.

        Args:
            file_path: File path to check

        Returns:
            True if the file is likely a test file
        """
        path_lower = file_path.lower()
        name = Path(file_path).name.lower()

        # Common test file patterns
        return (
            "test" in path_lower or
            name.startswith("test_") or
            name.endswith("_test.py") or
            name.endswith("_test.go") or
            name.endswith(".test.ts") or
            name.endswith(".test.js") or
            name.endswith(".spec.ts") or
            name.endswith(".spec.js") or
            "/tests/" in file_path or
            "\\tests\\" in file_path or
            "/test/" in file_path or
            "\\test\\" in file_path
        )

    def _find_affected_tests(
        self,
        project_id: int,
        affected_files: list[str],
        reverse_adj: dict[str, set[str]]
    ) -> set[str]:
        """Find test files affected by changes using multiple strategies.

        Uses three strategies:
        1. Naming convention: entity.go → entity_test.go
        2. Same directory test files
        3. Import relationship matching (tests that import affected packages)

        Args:
            project_id: Project ID
            affected_files: List of affected file paths
            reverse_adj: Reverse import adjacency list

        Returns:
            Set of affected test file paths
        """
        cursor = self.storage._get_cursor()
        affected_tests: set[str] = set()

        # Get all test files in the project
        cursor.execute(
            """
            SELECT relative_path FROM files
            WHERE project_id = ?
            """,
            (project_id,)
        )
        all_files = [row["relative_path"] for row in cursor.fetchall()]
        test_files = [f for f in all_files if self._is_test_file(f)]

        # Strategy 1: Naming convention matching
        # e.g., entity.go → entity_test.go, user_service.py → test_user_service.py
        for affected in affected_files:
            affected_path = Path(affected)
            affected_name = affected_path.stem  # filename without extension
            affected_dir = affected_path.parent
            affected_ext = affected_path.suffix

            # Go naming convention: entity.go → entity_test.go
            if affected_ext == ".go":
                test_name = f"{affected_name}_test.go"
                test_path = str(affected_dir / test_name)
                if test_path in test_files:
                    affected_tests.add(test_path)

            # Python naming convention: user_service.py → test_user_service.py
            elif affected_ext == ".py":
                test_name = f"test_{affected_name}.py"
                test_path = str(affected_dir / test_name)
                if test_path in test_files:
                    affected_tests.add(test_path)
                # Also check tests/ subdirectory
                tests_subdir = affected_dir / "tests" / test_name
                if str(tests_subdir) in test_files:
                    affected_tests.add(str(tests_subdir))

            # JS/TS naming convention: component.ts → component.test.ts or component.spec.ts
            elif affected_ext in (".ts", ".tsx", ".js", ".jsx"):
                for test_suffix in [".test", ".spec"]:
                    test_name = f"{affected_name}{test_suffix}{affected_ext}"
                    test_path = str(affected_dir / test_name)
                    if test_path in test_files:
                        affected_tests.add(test_path)
                # Check __tests__ directory
                tests_dir = affected_dir / "__tests__" / f"{affected_name}{test_suffix}{affected_ext}"
                for test_suffix in [".test", ".spec"]:
                    test_name = f"{affected_name}{test_suffix}{affected_ext}"
                    test_path = str(affected_dir / "__tests__" / test_name)
                    if test_path in test_files:
                        affected_tests.add(test_path)

        # Strategy 2: Same directory test files
        # Find test files in the same directory as affected files
        affected_dirs = {str(Path(f).parent) for f in affected_files}
        for test_file in test_files:
            test_dir = str(Path(test_file).parent)
            # Direct parent match
            if test_dir in affected_dirs:
                affected_tests.add(test_file)
            # Parent/tests directory match
            for affected_dir in affected_dirs:
                if test_dir == f"{affected_dir}/tests" or test_dir == f"{affected_dir}\\tests":
                    affected_tests.add(test_file)
                if test_dir == f"{affected_dir}/__tests__" or test_dir == f"{affected_dir}\\__tests__":
                    affected_tests.add(test_file)

        # Strategy 3: Import relationship matching
        # Find test files that import any of the affected files (via reverse_adj)
        for affected in affected_files:
            importers = reverse_adj.get(affected, set())
            for importer in importers:
                if self._is_test_file(importer):
                    affected_tests.add(importer)

        return affected_tests
