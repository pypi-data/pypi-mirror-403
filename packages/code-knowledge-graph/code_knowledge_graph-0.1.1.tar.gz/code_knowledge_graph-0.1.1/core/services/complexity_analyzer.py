"""Code Complexity Analysis Service.

This module implements code complexity metrics calculation:
- Cyclomatic complexity (decision points)
- Cognitive complexity (mental effort)
- Lines of code (LOC)
- Parameter count
- Nesting depth

Feature: code-knowledge-graph-enhancement
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from core.storage.sqlite import SQLiteStorage

logger = logging.getLogger(__name__)


@dataclass
class FunctionMetrics:
    """Complexity metrics for a single function."""
    function_name: str
    file_path: str
    start_line: int
    end_line: int
    cyclomatic: int  # Cyclomatic complexity
    cognitive: int  # Cognitive complexity
    loc: int  # Lines of code
    parameter_count: int  # Number of parameters
    max_nesting_depth: int  # Maximum nesting level
    container_name: Optional[str] = None  # Parent class/struct


@dataclass
class HotspotInfo:
    """Information about a complexity hotspot."""
    function: str
    file: str
    line: int
    metrics: dict[str, int]
    severity: str  # "low", "medium", "high", "critical"
    suggestion: str


@dataclass
class DirectoryMetrics:
    """Aggregated metrics for a directory."""
    directory: str
    total_functions: int
    avg_cyclomatic: float
    avg_cognitive: float
    max_cyclomatic: int
    max_cognitive: int
    total_loc: int
    hotspot_count: int


@dataclass
class ComplexityResult:
    """Result of complexity analysis."""
    project_path: str
    hotspots: list[HotspotInfo]
    by_directory: dict[str, DirectoryMetrics]
    total_functions_analyzed: int
    high_complexity_count: int
    message: Optional[str] = None


class ComplexityAnalyzer:
    """Service for analyzing code complexity.

    Provides complexity metrics calculation and hotspot identification.
    """

    # Complexity thresholds
    CYCLOMATIC_THRESHOLDS = {
        "low": 5,
        "medium": 10,
        "high": 20,
        "critical": 50
    }

    COGNITIVE_THRESHOLDS = {
        "low": 8,
        "medium": 15,
        "high": 30,
        "critical": 60
    }

    def __init__(self, storage: SQLiteStorage):
        """Initialize complexity analyzer.

        Args:
            storage: SQLite storage backend instance
        """
        self.storage = storage

    def get_complexity_metrics(
        self,
        project_path: str,
        min_complexity: int = 10,
        limit: int = 50,
        directory: Optional[str] = None
    ) -> ComplexityResult:
        """Analyze complexity metrics for a project.

        Args:
            project_path: Path to the project
            min_complexity: Minimum cyclomatic complexity to report as hotspot
            limit: Maximum number of hotspots to return
            directory: Optional directory to filter by

        Returns:
            ComplexityResult with hotspots and directory metrics
        """
        # Validate parameters
        min_complexity = max(1, min(100, min_complexity))
        limit = max(1, min(500, limit))

        # Get project
        project = self.storage.get_project(project_path)
        if not project:
            return ComplexityResult(
                project_path=project_path,
                hotspots=[],
                by_directory={},
                total_functions_analyzed=0,
                high_complexity_count=0,
                message=f"Project not found: {project_path}"
            )

        cursor = self.storage._get_cursor()

        # Get all functions with their signatures for analysis
        if directory:
            cursor.execute(
                """
                SELECT
                    s.id,
                    s.name,
                    s.symbol_type,
                    s.container_name,
                    s.signature,
                    s.start_line,
                    s.end_line,
                    f.relative_path,
                    f.file_type
                FROM symbols s
                JOIN files f ON s.file_id = f.id
                WHERE f.project_id = ?
                  AND s.symbol_type IN ('function', 'method')
                  AND f.relative_path LIKE ?
                ORDER BY f.relative_path, s.start_line
                """,
                (project.id, f"{directory}%")
            )
        else:
            cursor.execute(
                """
                SELECT
                    s.id,
                    s.name,
                    s.symbol_type,
                    s.container_name,
                    s.signature,
                    s.start_line,
                    s.end_line,
                    f.relative_path,
                    f.file_type
                FROM symbols s
                JOIN files f ON s.file_id = f.id
                WHERE f.project_id = ?
                  AND s.symbol_type IN ('function', 'method')
                ORDER BY f.relative_path, s.start_line
                """,
                (project.id,)
            )

        rows = cursor.fetchall()

        if not rows:
            return ComplexityResult(
                project_path=project_path,
                hotspots=[],
                by_directory={},
                total_functions_analyzed=0,
                high_complexity_count=0,
                message="No functions found in the project"
            )

        # Analyze each function
        all_metrics: list[FunctionMetrics] = []
        for row in rows:
            metrics = self._analyze_function(row)
            if metrics:
                all_metrics.append(metrics)

        # Identify hotspots
        hotspots: list[HotspotInfo] = []
        for metrics in all_metrics:
            if metrics.cyclomatic >= min_complexity:
                severity = self._get_severity(metrics.cyclomatic, metrics.cognitive)
                suggestion = self._generate_suggestion(metrics)

                hotspots.append(HotspotInfo(
                    function=metrics.function_name,
                    file=metrics.file_path,
                    line=metrics.start_line,
                    metrics={
                        "cyclomatic": metrics.cyclomatic,
                        "cognitive": metrics.cognitive,
                        "loc": metrics.loc,
                        "parameter_count": metrics.parameter_count,
                        "max_nesting_depth": metrics.max_nesting_depth
                    },
                    severity=severity,
                    suggestion=suggestion
                ))

        # Sort by cyclomatic complexity descending
        hotspots.sort(key=lambda h: h.metrics["cyclomatic"], reverse=True)
        hotspots = hotspots[:limit]

        # Calculate directory metrics
        by_directory = self._calculate_directory_metrics(all_metrics, min_complexity)

        # Count high complexity functions
        high_complexity_count = sum(
            1 for m in all_metrics
            if m.cyclomatic >= self.CYCLOMATIC_THRESHOLDS["high"]
        )

        return ComplexityResult(
            project_path=project_path,
            hotspots=hotspots,
            by_directory=by_directory,
            total_functions_analyzed=len(all_metrics),
            high_complexity_count=high_complexity_count,
            message=None
        )

    def _analyze_function(self, row) -> Optional[FunctionMetrics]:
        """Analyze complexity metrics for a function.

        Args:
            row: Database row with function info

        Returns:
            FunctionMetrics if analysis succeeds
        """
        try:
            name = row["name"]
            file_path = row["relative_path"]
            start_line = row["start_line"] or 0
            end_line = row["end_line"] or 0
            signature = row["signature"] or ""
            container_name = row["container_name"]

            # Calculate LOC
            loc = max(1, end_line - start_line + 1)

            # Estimate cyclomatic complexity from signature
            # (simplified: count decision keywords in signature)
            cyclomatic = self._estimate_cyclomatic(signature, loc)

            # Estimate cognitive complexity
            cognitive = self._estimate_cognitive(signature, loc)

            # Count parameters
            parameter_count = self._count_parameters(signature)

            # Estimate max nesting depth
            max_nesting_depth = self._estimate_nesting(signature, loc)

            # Use fully qualified name for methods
            func_name = name
            if container_name:
                func_name = f"{container_name}.{name}"

            return FunctionMetrics(
                function_name=func_name,
                file_path=file_path,
                start_line=start_line,
                end_line=end_line,
                cyclomatic=cyclomatic,
                cognitive=cognitive,
                loc=loc,
                parameter_count=parameter_count,
                max_nesting_depth=max_nesting_depth,
                container_name=container_name
            )
        except Exception as e:
            logger.warning(f"Failed to analyze function: {e}")
            return None

    def _estimate_cyclomatic(self, signature: str, loc: int) -> int:
        """Estimate cyclomatic complexity.

        Cyclomatic complexity = E - N + 2P
        where E = edges, N = nodes, P = connected components

        Simplified: 1 + number of decision points

        Args:
            signature: Function signature
            loc: Lines of code

        Returns:
            Estimated cyclomatic complexity
        """
        # Base complexity
        complexity = 1

        # Estimate based on LOC (roughly 1 decision point per 10-15 lines)
        complexity += loc // 12

        # Check signature for complexity indicators
        sig_lower = signature.lower()

        # Count apparent decision keywords in signature comments/docs
        keywords = ["if", "else", "switch", "case", "for", "while", "catch", "&&", "||"]
        for kw in keywords:
            if kw in sig_lower:
                complexity += 1

        return max(1, complexity)

    def _estimate_cognitive(self, signature: str, loc: int) -> int:
        """Estimate cognitive complexity.

        Cognitive complexity measures mental effort, penalizing:
        - Nesting
        - Breaks in linear flow
        - Complex conditions

        Args:
            signature: Function signature
            loc: Lines of code

        Returns:
            Estimated cognitive complexity
        """
        # Base cognitive score
        cognitive = 0

        # Estimate based on LOC (cognitive load increases with size)
        cognitive += loc // 10

        # Add for estimated nesting (cognitive penalty is higher for nesting)
        estimated_nesting = min(5, loc // 20)
        cognitive += estimated_nesting * 2

        # Complexity indicators
        sig_lower = signature.lower()
        cognitive_keywords = ["if", "else", "switch", "for", "while", "try", "catch", "&&", "||"]
        for kw in cognitive_keywords:
            if kw in sig_lower:
                cognitive += 2

        return max(1, cognitive)

    def _count_parameters(self, signature: str) -> int:
        """Count parameters in a function signature.

        Args:
            signature: Function signature

        Returns:
            Estimated parameter count
        """
        # Find parameter list between parentheses
        start = signature.find("(")
        end = signature.find(")")

        if start == -1 or end == -1 or end <= start + 1:
            return 0

        params_str = signature[start + 1:end]
        if not params_str.strip():
            return 0

        # Count commas + 1 (simple estimation)
        return params_str.count(",") + 1

    def _estimate_nesting(self, signature: str, loc: int) -> int:
        """Estimate maximum nesting depth.

        Args:
            signature: Function signature
            loc: Lines of code

        Returns:
            Estimated max nesting depth
        """
        # Estimate based on function size
        if loc < 10:
            return 1
        elif loc < 30:
            return 2
        elif loc < 60:
            return 3
        elif loc < 100:
            return 4
        else:
            return 5

    def _get_severity(self, cyclomatic: int, cognitive: int) -> str:
        """Determine severity level based on complexity metrics.

        Args:
            cyclomatic: Cyclomatic complexity
            cognitive: Cognitive complexity

        Returns:
            Severity level string
        """
        if cyclomatic >= self.CYCLOMATIC_THRESHOLDS["critical"] or \
           cognitive >= self.COGNITIVE_THRESHOLDS["critical"]:
            return "critical"
        elif cyclomatic >= self.CYCLOMATIC_THRESHOLDS["high"] or \
             cognitive >= self.COGNITIVE_THRESHOLDS["high"]:
            return "high"
        elif cyclomatic >= self.CYCLOMATIC_THRESHOLDS["medium"] or \
             cognitive >= self.COGNITIVE_THRESHOLDS["medium"]:
            return "medium"
        else:
            return "low"

    def _generate_suggestion(self, metrics: FunctionMetrics) -> str:
        """Generate improvement suggestion based on metrics.

        Args:
            metrics: Function metrics

        Returns:
            Suggestion string
        """
        suggestions = []

        if metrics.cyclomatic >= self.CYCLOMATIC_THRESHOLDS["high"]:
            suggestions.append("Consider splitting into smaller functions")

        if metrics.loc > 100:
            suggestions.append("Function is too long, extract helper methods")

        if metrics.parameter_count > 5:
            suggestions.append("Too many parameters, consider using a config object")

        if metrics.max_nesting_depth > 3:
            suggestions.append("Reduce nesting with early returns or guard clauses")

        if metrics.cognitive >= self.COGNITIVE_THRESHOLDS["high"]:
            suggestions.append("High cognitive load, simplify logic flow")

        return "; ".join(suggestions) if suggestions else "Review for potential refactoring"

    def _calculate_directory_metrics(
        self,
        all_metrics: list[FunctionMetrics],
        min_complexity: int
    ) -> dict[str, DirectoryMetrics]:
        """Calculate aggregated metrics per directory.

        Args:
            all_metrics: List of all function metrics
            min_complexity: Minimum complexity for hotspot counting

        Returns:
            Dictionary of directory path to DirectoryMetrics
        """
        # Group by directory
        by_dir: dict[str, list[FunctionMetrics]] = {}
        for metrics in all_metrics:
            dir_path = str(Path(metrics.file_path).parent)
            if dir_path not in by_dir:
                by_dir[dir_path] = []
            by_dir[dir_path].append(metrics)

        # Calculate aggregates
        result: dict[str, DirectoryMetrics] = {}
        for dir_path, dir_metrics in by_dir.items():
            if not dir_metrics:
                continue

            total_functions = len(dir_metrics)
            avg_cyclomatic = sum(m.cyclomatic for m in dir_metrics) / total_functions
            avg_cognitive = sum(m.cognitive for m in dir_metrics) / total_functions
            max_cyclomatic = max(m.cyclomatic for m in dir_metrics)
            max_cognitive = max(m.cognitive for m in dir_metrics)
            total_loc = sum(m.loc for m in dir_metrics)
            hotspot_count = sum(1 for m in dir_metrics if m.cyclomatic >= min_complexity)

            result[dir_path] = DirectoryMetrics(
                directory=dir_path,
                total_functions=total_functions,
                avg_cyclomatic=round(avg_cyclomatic, 2),
                avg_cognitive=round(avg_cognitive, 2),
                max_cyclomatic=max_cyclomatic,
                max_cognitive=max_cognitive,
                total_loc=total_loc,
                hotspot_count=hotspot_count
            )

        return result

    def to_dict(self, result: ComplexityResult) -> dict:
        """Convert result to dictionary for JSON serialization.

        Args:
            result: ComplexityResult

        Returns:
            Dictionary representation
        """
        return {
            "project_path": result.project_path,
            "hotspots": [
                {
                    "function": h.function,
                    "file": h.file,
                    "line": h.line,
                    "metrics": h.metrics,
                    "severity": h.severity,
                    "suggestion": h.suggestion
                }
                for h in result.hotspots
            ],
            "by_directory": {
                dir_path: {
                    "total_functions": dm.total_functions,
                    "avg_cyclomatic": dm.avg_cyclomatic,
                    "avg_cognitive": dm.avg_cognitive,
                    "max_cyclomatic": dm.max_cyclomatic,
                    "max_cognitive": dm.max_cognitive,
                    "total_loc": dm.total_loc,
                    "hotspot_count": dm.hotspot_count
                }
                for dir_path, dm in result.by_directory.items()
            },
            "total_functions_analyzed": result.total_functions_analyzed,
            "high_complexity_count": result.high_complexity_count,
            "message": result.message
        }
