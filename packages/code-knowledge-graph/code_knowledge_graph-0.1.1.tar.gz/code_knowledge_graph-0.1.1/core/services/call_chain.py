"""Call Chain Tracing Service for code knowledge graph.

This module implements call chain tracing using SQLite recursive CTE queries,
supporting upstream (who calls me) and downstream (who do I call) tracing
with depth limits, cycle detection, and standard library pruning.

Feature: code-knowledge-graph-enhancement
"""

import logging
from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING

from core.storage.sqlite import SQLiteStorage

if TYPE_CHECKING:
    from core.services.go_interface import GoInterfaceResolver

logger = logging.getLogger(__name__)


@dataclass
class CallChainNode:
    """A node in the call chain.
    
    Represents a single function/method in the call chain with its metadata.
    
    Attributes:
        function_name: Name of the function/method
        file_path: Relative path to the file containing the function
        line_number: Line number where the function is defined
        container_name: Name of the containing class/struct if applicable
        call_type: Type of call (direct, potential, deferred, async)
        is_cycle: Whether this node creates a cycle in the call chain
        depth: Distance from the starting node (0 = start node)
    """
    function_name: str
    file_path: str
    line_number: int
    container_name: Optional[str] = None
    call_type: str = "direct"  # direct, potential, deferred, async
    is_cycle: bool = False
    depth: int = 0


@dataclass
class CallChainResult:
    """Result of a call chain trace operation.
    
    Contains the traced call chain data and metadata about the trace.
    
    Attributes:
        start_symbol: The starting function name for the trace
        direction: Trace direction (upstream or downstream)
        depth: Maximum depth that was traced
        chains: List of call chain paths, each path is a list of nodes
        has_cycle: Whether any cycle was detected in the trace
        truncated: Whether results were truncated due to limits
        message: Optional message (e.g., error or info message)
    """
    start_symbol: str
    direction: str  # upstream, downstream
    depth: int
    chains: list[list[CallChainNode]] = field(default_factory=list)
    has_cycle: bool = False
    truncated: bool = False
    message: Optional[str] = None


class CallChainService:
    """Call chain tracing service using SQLite recursive CTE.
    
    Provides efficient call chain tracing using recursive Common Table Expressions
    (CTE) in SQLite, avoiding N+1 query problems. Supports:
    
    - Upstream tracing: Find all callers of a function
    - Downstream tracing: Find all functions called by a function
    - Depth limiting: Control maximum trace depth
    - Per-level limiting: Control maximum nodes per depth level
    - Cycle detection: Detect and mark circular call patterns
    - Standard library pruning: Filter out standard library calls
    
    The service uses the enhanced_function_calls table which references
    the symbols table for accurate call chain resolution.
    """
    
    DEFAULT_DEPTH = 5
    DEFAULT_LIMIT_PER_LEVEL = 20
    
    # Standard library path patterns for pruning
    STDLIB_PATTERNS = [
        "site-packages/",
        "site-packages\\",
        "lib/python",
        "lib\\python",
        "node_modules/",
        "node_modules\\",
        "vendor/",
        "vendor\\",
        ".venv/",
        ".venv\\",
        "venv/",
        "venv\\",
    ]
    
    # Recursive CTE query for downstream tracing (who do I call)
    # Uses path tracking for cycle detection
    DOWNSTREAM_CTE_QUERY = """
    WITH RECURSIVE call_graph(
        id, source_id, target_id, target_name, call_type, depth, path, is_cycle
    ) AS (
        -- Base case: direct calls from the starting symbol
        SELECT
            fc.id,
            fc.source_symbol_id,
            fc.target_symbol_id,
            fc.target_symbol_name,
            fc.call_type,
            1 as depth,
            CAST(fc.source_symbol_id AS TEXT) || ',' ||
                COALESCE(CAST(fc.target_symbol_id AS TEXT), fc.target_symbol_name) as path,
            0 as is_cycle
        FROM enhanced_function_calls fc
        JOIN symbols s ON fc.source_symbol_id = s.id
        WHERE s.name = :start_symbol
          AND s.file_id IN (SELECT id FROM files WHERE project_id = :project_id)
          AND s.symbol_type IN ('function', 'method')

        UNION ALL

        -- Recursive case: follow the call chain
        SELECT
            fc.id,
            fc.source_symbol_id,
            fc.target_symbol_id,
            fc.target_symbol_name,
            fc.call_type,
            cg.depth + 1,
            cg.path || ',' || COALESCE(CAST(fc.target_symbol_id AS TEXT), fc.target_symbol_name),
            -- Cycle detection: check if target already in path (exact match with comma delimiter)
            CASE
                WHEN (',' || cg.path || ',') LIKE ('%,' || COALESCE(CAST(fc.target_symbol_id AS TEXT), fc.target_symbol_name) || ',%')
                THEN 1
                ELSE 0
            END as is_cycle
        FROM enhanced_function_calls fc
        JOIN call_graph cg ON fc.source_symbol_id = cg.target_id
        WHERE cg.depth < :max_depth
          AND cg.is_cycle = 0  -- Stop recursion on cycles
          AND cg.target_id IS NOT NULL  -- Can only follow resolved targets
    )
    SELECT DISTINCT
        cg.id,
        cg.source_id,
        cg.target_id,
        cg.target_name,
        cg.call_type,
        cg.depth,
        cg.path,
        cg.is_cycle,
        s.name as symbol_name,
        s.signature,
        s.container_name,
        f.relative_path as file_path,
        s.start_line
    FROM call_graph cg
    LEFT JOIN symbols s ON cg.target_id = s.id
    LEFT JOIN files f ON s.file_id = f.id
    WHERE (
        :prune_stdlib = 0
        OR f.relative_path IS NULL
        OR (
            f.relative_path NOT LIKE '%site-packages%'
            AND f.relative_path NOT LIKE '%node_modules%'
            AND f.relative_path NOT LIKE '%vendor%'
            AND f.relative_path NOT LIKE '%.venv%'
            AND f.relative_path NOT LIKE '%venv%'
        )
    )
    AND (s.symbol_type IS NULL OR s.symbol_type IN ('function', 'method'))
    ORDER BY cg.depth, cg.id
    LIMIT :limit;
    """
    
    # Recursive CTE query for upstream tracing (who calls me)
    UPSTREAM_CTE_QUERY = """
    WITH RECURSIVE call_graph(
        id, source_id, target_id, call_type, depth, path, is_cycle
    ) AS (
        -- Base case: direct callers of the starting symbol
        SELECT
            fc.id,
            fc.source_symbol_id,
            fc.target_symbol_id,
            fc.call_type,
            1 as depth,
            CAST(fc.target_symbol_id AS TEXT) || ',' || CAST(fc.source_symbol_id AS TEXT) as path,
            0 as is_cycle
        FROM enhanced_function_calls fc
        JOIN symbols s ON fc.target_symbol_id = s.id
        WHERE s.name = :start_symbol
          AND s.file_id IN (SELECT id FROM files WHERE project_id = :project_id)
          AND s.symbol_type IN ('function', 'method')

        UNION ALL

        -- Recursive case: follow callers up the chain
        SELECT
            fc.id,
            fc.source_symbol_id,
            fc.target_symbol_id,
            fc.call_type,
            cg.depth + 1,
            cg.path || ',' || CAST(fc.source_symbol_id AS TEXT),
            -- Cycle detection: check if source already in path (exact match with comma delimiter)
            CASE
                WHEN (',' || cg.path || ',') LIKE ('%,' || CAST(fc.source_symbol_id AS TEXT) || ',%')
                THEN 1
                ELSE 0
            END as is_cycle
        FROM enhanced_function_calls fc
        JOIN call_graph cg ON fc.target_symbol_id = cg.source_id
        WHERE cg.depth < :max_depth
          AND cg.is_cycle = 0  -- Stop recursion on cycles
    )
    SELECT DISTINCT
        cg.id,
        cg.source_id,
        cg.target_id,
        cg.call_type,
        cg.depth,
        cg.path,
        cg.is_cycle,
        s.name as symbol_name,
        s.signature,
        s.container_name,
        f.relative_path as file_path,
        s.start_line
    FROM call_graph cg
    JOIN symbols s ON cg.source_id = s.id
    JOIN files f ON s.file_id = f.id
    WHERE (
        :prune_stdlib = 0
        OR (
            f.relative_path NOT LIKE '%site-packages%'
            AND f.relative_path NOT LIKE '%node_modules%'
            AND f.relative_path NOT LIKE '%vendor%'
            AND f.relative_path NOT LIKE '%.venv%'
            AND f.relative_path NOT LIKE '%venv%'
        )
    )
    AND s.symbol_type IN ('function', 'method')
    ORDER BY cg.depth, cg.id
    LIMIT :limit;
    """
    
    def __init__(self, storage: SQLiteStorage):
        """Initialize call chain service.
        
        Args:
            storage: SQLite storage backend instance
        """
        self.storage = storage
        self._go_interface_resolver: Optional["GoInterfaceResolver"] = None
    
    @property
    def go_interface_resolver(self) -> "GoInterfaceResolver":
        """Lazy-load Go interface resolver.
        
        Returns:
            GoInterfaceResolver instance
        """
        if self._go_interface_resolver is None:
            from core.services.go_interface import GoInterfaceResolver
            self._go_interface_resolver = GoInterfaceResolver(self.storage)
        return self._go_interface_resolver
    
    def trace_call_chain(
        self,
        project_path: str,
        start_symbol: str,
        direction: str = "downstream",
        depth: int = DEFAULT_DEPTH,
        limit_per_level: int = DEFAULT_LIMIT_PER_LEVEL,
        prune_standard_libs: bool = True
    ) -> CallChainResult:
        """Trace function call chain.
        
        Uses recursive CTE to efficiently query the entire call tree in a single
        database operation, avoiding N+1 query problems.
        
        Args:
            project_path: Path to the project
            start_symbol: Name of the starting function/method
            direction: Trace direction - "upstream" (who calls me) or 
                      "downstream" (who do I call)
            depth: Maximum trace depth (default: 5)
            limit_per_level: Maximum nodes per depth level (default: 20)
            prune_standard_libs: Whether to filter out standard library calls
            
        Returns:
            CallChainResult containing the traced call chain data
        """
        # Validate direction
        if direction not in ("upstream", "downstream"):
            return CallChainResult(
                start_symbol=start_symbol,
                direction=direction,
                depth=depth,
                chains=[],
                message=f"Invalid direction: {direction}. Must be 'upstream' or 'downstream'"
            )
        
        # Get project
        project = self.storage.get_project(project_path)
        if not project:
            return CallChainResult(
                start_symbol=start_symbol,
                direction=direction,
                depth=depth,
                chains=[],
                message=f"Project not found: {project_path}"
            )
        
        # Select appropriate query
        query = self.DOWNSTREAM_CTE_QUERY if direction == "downstream" else self.UPSTREAM_CTE_QUERY
        
        # Execute query
        try:
            cursor = self.storage._get_cursor()
            cursor.execute(query, {
                "start_symbol": start_symbol,
                "project_id": project.id,
                "max_depth": depth,
                "limit": limit_per_level * depth,
                "prune_stdlib": 1 if prune_standard_libs else 0
            })
            
            rows = cursor.fetchall()
            
            # Build result
            return self._build_chain_result(
                rows, start_symbol, direction, depth, limit_per_level
            )
            
        except Exception as e:
            logger.error(f"Call chain trace failed: {e}")
            return CallChainResult(
                start_symbol=start_symbol,
                direction=direction,
                depth=depth,
                chains=[],
                message=f"Query failed: {str(e)}"
            )
    
    def _build_chain_result(
        self,
        rows: list,
        start_symbol: str,
        direction: str,
        depth: int,
        limit_per_level: int
    ) -> CallChainResult:
        """Build CallChainResult from SQL query results.

        Organizes results into chains by following the relationships.
        For downstream: start -> callees
        For upstream: callers -> start (reversed display)

        Args:
            rows: Raw SQL result rows
            start_symbol: Starting symbol name
            direction: Trace direction
            depth: Maximum depth
            limit_per_level: Limit per level

        Returns:
            Structured CallChainResult with complete call paths
        """
        if not rows:
            return CallChainResult(
                start_symbol=start_symbol,
                direction=direction,
                depth=depth,
                chains=[],
                message="No call chain found for the specified symbol"
            )

        has_cycle = False
        truncated = False

        # Count nodes per depth level for truncation detection
        depth_counts: dict[int, int] = {}

        # Store all node info by ID (for upstream, this is the source/caller)
        all_nodes: dict[str, dict] = {}

        # Build edges based on direction
        # For downstream: source_id -> [target_ids] (who do I call)
        # For upstream: target_id -> [source_ids] (who calls me)
        edges: dict[str, list[str]] = {}

        for row in rows:
            row_depth = row["depth"]

            # Track depth counts for truncation detection
            depth_counts[row_depth] = depth_counts.get(row_depth, 0) + 1
            if depth_counts[row_depth] > limit_per_level:
                truncated = True
                continue

            # Check for cycle
            is_cycle = bool(row["is_cycle"])
            if is_cycle:
                has_cycle = True

            source_id = str(row["source_id"]) if row["source_id"] else None
            target_id = str(row["target_id"]) if row["target_id"] else None

            if direction == "downstream":
                # For downstream, we track targets (callees)
                node_id = target_id or row["target_name"]
                # Only add if not seen, or update if this is an earlier depth
                if node_id not in all_nodes or row_depth < all_nodes[node_id]["depth"]:
                    all_nodes[node_id] = {
                        "function_name": row["symbol_name"] or row["target_name"],
                        "file_path": row["file_path"] or "",
                        "line_number": row["start_line"] or 0,
                        "container_name": row["container_name"],
                        "call_type": row["call_type"] or "direct",
                        "is_cycle": is_cycle,
                        "depth": row_depth
                    }
                # Build edge: source -> target
                if source_id and node_id:
                    if source_id not in edges:
                        edges[source_id] = []
                    if node_id not in edges[source_id]:
                        edges[source_id].append(node_id)
            else:
                # For upstream, we track sources (callers)
                node_id = source_id
                if node_id:
                    # Only add if not seen, or update if this is an earlier depth
                    if node_id not in all_nodes or row_depth < all_nodes[node_id]["depth"]:
                        all_nodes[node_id] = {
                            "function_name": row["symbol_name"],
                            "file_path": row["file_path"] or "",
                            "line_number": row["start_line"] or 0,
                            "container_name": row["container_name"],
                            "call_type": row["call_type"] or "direct",
                            "is_cycle": is_cycle,
                            "depth": row_depth
                        }
                    # Build edge: current caller -> callers of current caller
                    # For upstream depth=1: target_id is the start symbol, source_id is direct caller
                    # For upstream depth=2: source_id calls target_id (which was a caller at depth=1)
                    if target_id and node_id:
                        if target_id not in edges:
                            edges[target_id] = []
                        if node_id not in edges[target_id]:
                            edges[target_id].append(node_id)

        # Build chains using DFS
        chains: list[list[CallChainNode]] = []

        def build_chain_dfs(current_id: str, current_chain: list[CallChainNode], visited: set[str]):
            """Build chains using depth-first search."""
            if current_id in visited:
                return

            if current_id in all_nodes:
                info = all_nodes[current_id]
                node = CallChainNode(
                    function_name=info["function_name"],
                    file_path=info["file_path"],
                    line_number=info["line_number"],
                    container_name=info["container_name"],
                    call_type=info["call_type"],
                    is_cycle=info["is_cycle"],
                    depth=info["depth"]
                )
                current_chain.append(node)
                visited.add(current_id)

                # Follow edges to children
                if current_id in edges:
                    for child_id in edges[current_id]:
                        build_chain_dfs(child_id, current_chain, visited)
                else:
                    # Leaf node - save the chain
                    if current_chain:
                        chains.append(list(current_chain))

                current_chain.pop()
                visited.remove(current_id)

        # Start DFS from depth-1 nodes
        depth_1_nodes = [nid for nid, info in all_nodes.items() if info["depth"] == 1]

        for node_id in depth_1_nodes:
            build_chain_dfs(node_id, [], set())

        # Deduplicate chains (same sequence of function names)
        seen_chains: set[tuple] = set()
        unique_chains: list[list[CallChainNode]] = []
        for chain in chains:
            chain_key = tuple((n.function_name, n.depth) for n in chain)
            if chain_key not in seen_chains:
                seen_chains.add(chain_key)
                unique_chains.append(chain)

        # If DFS didn't produce chains, fall back to flat list by depth
        if not unique_chains and all_nodes:
            nodes_by_depth: dict[int, list[CallChainNode]] = {}
            for node_id, info in all_nodes.items():
                d = info["depth"]
                node = CallChainNode(
                    function_name=info["function_name"],
                    file_path=info["file_path"],
                    line_number=info["line_number"],
                    container_name=info["container_name"],
                    call_type=info["call_type"],
                    is_cycle=info["is_cycle"],
                    depth=d
                )
                if d not in nodes_by_depth:
                    nodes_by_depth[d] = []
                # Avoid duplicates
                if not any(n.function_name == node.function_name for n in nodes_by_depth[d]):
                    nodes_by_depth[d].append(node)

            # Create one chain with all nodes sorted by depth
            flat_chain = []
            for d in sorted(nodes_by_depth.keys()):
                flat_chain.extend(nodes_by_depth[d])
            if flat_chain:
                unique_chains.append(flat_chain)

        return CallChainResult(
            start_symbol=start_symbol,
            direction=direction,
            depth=depth,
            chains=unique_chains,
            has_cycle=has_cycle,
            truncated=truncated,
            message=None
        )
    
    def _is_standard_lib(self, file_path: str) -> bool:
        """Check if a file path belongs to standard library or third-party packages.
        
        Detects common patterns for:
        - Python: site-packages, lib/python, venv
        - Node.js: node_modules
        - Go: vendor
        
        Args:
            file_path: File path to check
            
        Returns:
            True if the path appears to be a standard library or third-party package
        """
        if not file_path:
            return False
        
        file_path_lower = file_path.lower()
        return any(pattern.lower() in file_path_lower for pattern in self.STDLIB_PATTERNS)
    
    def get_call_chain_flat(
        self,
        project_path: str,
        start_symbol: str,
        direction: str = "downstream",
        depth: int = DEFAULT_DEPTH,
        limit_per_level: int = DEFAULT_LIMIT_PER_LEVEL,
        prune_standard_libs: bool = True
    ) -> list[CallChainNode]:
        """Get call chain as a flat list of nodes.
        
        Convenience method that returns all nodes in a single flat list,
        useful for simple iteration over all traced functions.
        
        Args:
            project_path: Path to the project
            start_symbol: Name of the starting function/method
            direction: Trace direction
            depth: Maximum trace depth
            limit_per_level: Maximum nodes per depth level
            prune_standard_libs: Whether to filter out standard library calls
            
        Returns:
            Flat list of all CallChainNode objects
        """
        result = self.trace_call_chain(
            project_path=project_path,
            start_symbol=start_symbol,
            direction=direction,
            depth=depth,
            limit_per_level=limit_per_level,
            prune_standard_libs=prune_standard_libs
        )
        
        # Flatten chains
        flat_nodes: list[CallChainNode] = []
        for chain in result.chains:
            flat_nodes.extend(chain)
        
        return flat_nodes

    def trace_call_chain_with_interface_expansion(
        self,
        project_path: str,
        start_symbol: str,
        direction: str = "downstream",
        depth: int = DEFAULT_DEPTH,
        limit_per_level: int = DEFAULT_LIMIT_PER_LEVEL,
        prune_standard_libs: bool = True,
        expand_interfaces: bool = True
    ) -> CallChainResult:
        """Trace function call chain with Go interface expansion.
        
        Similar to trace_call_chain, but also expands interface method calls
        to include all potential implementations. When a call to an interface
        method is detected, all structs implementing that interface are added
        as potential call targets.
        
        Args:
            project_path: Path to the project
            start_symbol: Name of the starting function/method
            direction: Trace direction - "upstream" or "downstream"
            depth: Maximum trace depth (default: 5)
            limit_per_level: Maximum nodes per depth level (default: 20)
            prune_standard_libs: Whether to filter out standard library calls
            expand_interfaces: Whether to expand interface calls to implementations
            
        Returns:
            CallChainResult containing the traced call chain data with
            potential implementations marked as "potential" call type
        """
        # First, get the basic call chain
        result = self.trace_call_chain(
            project_path=project_path,
            start_symbol=start_symbol,
            direction=direction,
            depth=depth,
            limit_per_level=limit_per_level,
            prune_standard_libs=prune_standard_libs
        )
        
        if not expand_interfaces or not result.chains:
            return result
        
        # Get project for interface expansion
        project = self.storage.get_project(project_path)
        if not project:
            return result
        
        # Expand interface calls in downstream direction
        if direction == "downstream":
            result = self._expand_interface_calls(result, project.id)
        
        return result
    
    def _expand_interface_calls(
        self,
        result: CallChainResult,
        project_id: int
    ) -> CallChainResult:
        """Expand interface method calls to include all implementations.
        
        For each node in the call chain that represents an interface method call,
        find all structs that implement the interface and add them as potential
        call targets.
        
        Args:
            result: Original call chain result
            project_id: Project ID
            
        Returns:
            Updated CallChainResult with expanded interface calls
        """
        expanded_chains: list[list[CallChainNode]] = []
        
        for chain in result.chains:
            expanded_chain = list(chain)  # Copy the original chain
            
            for node in chain:
                # Check if this is an interface method call
                if node.container_name:
                    # Check if the container is an interface
                    if self._is_interface(project_id, node.container_name):
                        # Get all implementations
                        implementations = self.go_interface_resolver.get_potential_implementations_for_call(
                            project_id,
                            node.container_name,
                            node.function_name
                        )
                        
                        # Add implementation nodes
                        for impl in implementations:
                            impl_node = CallChainNode(
                                function_name=impl["method_name"],
                                file_path=impl["file_path"],
                                line_number=impl["line_number"],
                                container_name=impl["struct_name"],
                                call_type="potential",
                                is_cycle=False,
                                depth=node.depth
                            )
                            expanded_chain.append(impl_node)
            
            expanded_chains.append(expanded_chain)
        
        return CallChainResult(
            start_symbol=result.start_symbol,
            direction=result.direction,
            depth=result.depth,
            chains=expanded_chains,
            has_cycle=result.has_cycle,
            truncated=result.truncated,
            message=result.message
        )
    
    def _is_interface(self, project_id: int, name: str) -> bool:
        """Check if a symbol name is an interface.
        
        Args:
            project_id: Project ID
            name: Symbol name to check
            
        Returns:
            True if the symbol is an interface
        """
        cursor = self.storage._get_cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM symbols s
            JOIN files f ON s.file_id = f.id
            WHERE f.project_id = ?
              AND s.name = ?
              AND s.symbol_type = 'interface'
        """, (project_id, name))
        
        count = cursor.fetchone()[0]
        return count > 0
    
    def get_interface_implementations(
        self,
        project_path: str,
        interface_name: str
    ) -> list[dict]:
        """Get all implementations of a Go interface.
        
        Convenience method to find all structs that implement a given interface.
        
        Args:
            project_path: Path to the project
            interface_name: Name of the interface
            
        Returns:
            List of dicts with implementation info:
            - struct_name: Name of the implementing struct
            - struct_file: File path where struct is defined
            - confidence: Match confidence (0-1)
        """
        project = self.storage.get_project(project_path)
        if not project:
            return []
        
        implementations = self.go_interface_resolver.find_implementations(
            project.id, interface_name
        )
        
        return [
            {
                "struct_name": impl.struct_name,
                "struct_file": impl.struct_file,
                "confidence": impl.confidence
            }
            for impl in implementations
        ]
