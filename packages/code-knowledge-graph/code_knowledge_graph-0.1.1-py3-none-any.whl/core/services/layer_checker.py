"""Architecture Layer Checker Service.

This module implements architecture layer violation detection
based on Clean Architecture / Hexagonal Architecture patterns.

Default layer hierarchy (Clean Architecture):
- domain: Core business logic (no external dependencies)
- application: Use cases and orchestration (depends on domain)
- infrastructure: External integrations (depends on domain)
- interface: User interface layer (depends on domain, application)

Feature: code-knowledge-graph-enhancement
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from core.storage.sqlite import SQLiteStorage

logger = logging.getLogger(__name__)


@dataclass
class LayerViolation:
    """A single layer violation."""
    from_layer: str
    to_layer: str
    from_file: str
    to_file: str
    from_line: Optional[int]
    import_module: str
    suggestion: str


@dataclass
class LayerStats:
    """Statistics for a layer."""
    name: str
    file_count: int
    import_count: int
    violation_count: int


@dataclass
class LayerCheckResult:
    """Result of layer violation check."""
    project_path: str
    violations: list[LayerViolation]
    violation_count: int
    layers_detected: list[str]
    layer_stats: dict[str, LayerStats]
    rules_applied: dict[str, list[str]]
    message: Optional[str] = None


class LayerChecker:
    """Service for checking architecture layer violations.

    Detects violations of Clean Architecture / Hexagonal Architecture
    layer dependency rules.
    """

    # Default Clean Architecture rules
    DEFAULT_RULES = {
        "domain": [],  # Domain doesn't depend on anything
        "application": ["domain"],  # Application can only depend on domain
        "infrastructure": ["domain"],  # Infrastructure can only depend on domain
        "interface": ["domain", "application"],  # Interface can depend on domain and application
    }

    # Common layer directory patterns
    LAYER_PATTERNS = {
        "domain": [
            "domain", "entities", "entity", "models", "model",
            "core/domain", "internal/domain", "pkg/domain"
        ],
        "application": [
            "application", "usecases", "usecase", "use_cases", "services",
            "core/application", "internal/application", "pkg/application"
        ],
        "infrastructure": [
            "infrastructure", "infra", "adapters", "adapter",
            "repository", "repositories", "persistence", "database",
            "external", "clients", "client", "pkg/infrastructure"
        ],
        "interface": [
            "interface", "interfaces", "api", "handlers", "handler",
            "controllers", "controller", "presentation", "ui",
            "web", "http", "grpc", "rest", "graphql"
        ]
    }

    def __init__(self, storage: SQLiteStorage):
        """Initialize layer checker.

        Args:
            storage: SQLite storage backend instance
        """
        self.storage = storage

    def check_layer_violations(
        self,
        project_path: str,
        rules: Optional[dict[str, list[str]]] = None,
        custom_patterns: Optional[dict[str, list[str]]] = None
    ) -> LayerCheckResult:
        """Check for layer dependency violations.

        Args:
            project_path: Path to the project
            rules: Optional custom dependency rules. If not provided, uses default
                   Clean Architecture rules. Format: {layer: [allowed_dependencies]}
            custom_patterns: Optional custom layer directory patterns.
                            Format: {layer: [directory_patterns]}

        Returns:
            LayerCheckResult containing violations and statistics
        """
        # Use default or custom rules
        effective_rules = rules or self.DEFAULT_RULES
        effective_patterns = custom_patterns or self.LAYER_PATTERNS

        # Get project
        project = self.storage.get_project(project_path)
        if not project:
            return LayerCheckResult(
                project_path=project_path,
                violations=[],
                violation_count=0,
                layers_detected=[],
                layer_stats={},
                rules_applied=effective_rules,
                message=f"Project not found: {project_path}"
            )

        cursor = self.storage._get_cursor()

        # Build layer mapping for all files
        cursor.execute(
            "SELECT relative_path FROM files WHERE project_id = ?",
            (project.id,)
        )
        all_files = [row["relative_path"] for row in cursor.fetchall()]

        file_to_layer = self._map_files_to_layers(all_files, effective_patterns)

        # Detect which layers are present
        layers_detected = list(set(file_to_layer.values()))
        layers_detected.sort()

        if not layers_detected:
            return LayerCheckResult(
                project_path=project_path,
                violations=[],
                violation_count=0,
                layers_detected=[],
                layer_stats={},
                rules_applied=effective_rules,
                message="No recognizable architecture layers found"
            )

        # Get all imports with source and target files
        cursor.execute(
            """
            SELECT
                sf.relative_path as source_path,
                tf.relative_path as target_path,
                i.module,
                i.line
            FROM imports i
            JOIN files sf ON i.file_id = sf.id
            LEFT JOIN files tf ON i.resolved_file_id = tf.id
            WHERE sf.project_id = ?
            """,
            (project.id,)
        )

        imports = cursor.fetchall()

        # Check for violations
        violations: list[LayerViolation] = []
        layer_import_counts: dict[str, int] = {layer: 0 for layer in effective_rules}
        layer_file_counts: dict[str, int] = {layer: 0 for layer in effective_rules}

        # Count files per layer
        for file_path, layer in file_to_layer.items():
            if layer in layer_file_counts:
                layer_file_counts[layer] += 1

        for row in imports:
            source_path = row["source_path"]
            target_path = row["target_path"]
            module = row["module"]
            line = row["line"]

            source_layer = file_to_layer.get(source_path)
            if not source_layer:
                continue

            # Count import
            if source_layer in layer_import_counts:
                layer_import_counts[source_layer] += 1

            # Determine target layer
            target_layer = None
            if target_path:
                target_layer = file_to_layer.get(target_path)
            else:
                # Try to infer layer from module name
                target_layer = self._infer_layer_from_module(module, effective_patterns)

            if not target_layer:
                continue

            # Check if this dependency is allowed
            if source_layer in effective_rules:
                allowed = effective_rules[source_layer]
                # A layer can always depend on itself
                if target_layer != source_layer and target_layer not in allowed:
                    violation = LayerViolation(
                        from_layer=source_layer,
                        to_layer=target_layer,
                        from_file=source_path,
                        to_file=target_path or module,
                        from_line=line,
                        import_module=module,
                        suggestion=self._generate_suggestion(source_layer, target_layer)
                    )
                    violations.append(violation)

        # Calculate layer statistics
        layer_stats: dict[str, LayerStats] = {}
        violation_counts = {}
        for v in violations:
            violation_counts[v.from_layer] = violation_counts.get(v.from_layer, 0) + 1

        for layer in effective_rules:
            layer_stats[layer] = LayerStats(
                name=layer,
                file_count=layer_file_counts.get(layer, 0),
                import_count=layer_import_counts.get(layer, 0),
                violation_count=violation_counts.get(layer, 0)
            )

        return LayerCheckResult(
            project_path=project_path,
            violations=violations,
            violation_count=len(violations),
            layers_detected=layers_detected,
            layer_stats=layer_stats,
            rules_applied=effective_rules,
            message=None
        )

    def _map_files_to_layers(
        self,
        files: list[str],
        patterns: dict[str, list[str]]
    ) -> dict[str, str]:
        """Map files to their architecture layers.

        Args:
            files: List of file paths
            patterns: Layer directory patterns

        Returns:
            Dictionary mapping file path to layer name
        """
        file_to_layer: dict[str, str] = {}

        for file_path in files:
            path_lower = file_path.lower()
            path_parts = Path(file_path).parts

            for layer, layer_patterns in patterns.items():
                for pattern in layer_patterns:
                    pattern_lower = pattern.lower()
                    # Check if pattern matches any part of the path
                    if "/" in pattern_lower:
                        # Multi-part pattern
                        if pattern_lower in path_lower:
                            file_to_layer[file_path] = layer
                            break
                    else:
                        # Single directory pattern
                        if any(part.lower() == pattern_lower for part in path_parts):
                            file_to_layer[file_path] = layer
                            break
                if file_path in file_to_layer:
                    break

        return file_to_layer

    def _infer_layer_from_module(
        self,
        module: str,
        patterns: dict[str, list[str]]
    ) -> Optional[str]:
        """Infer layer from import module name.

        Args:
            module: Import module name
            patterns: Layer patterns

        Returns:
            Layer name if inferred, None otherwise
        """
        module_lower = module.lower()

        for layer, layer_patterns in patterns.items():
            for pattern in layer_patterns:
                if pattern.lower() in module_lower:
                    return layer

        return None

    def _generate_suggestion(self, from_layer: str, to_layer: str) -> str:
        """Generate suggestion for fixing a violation.

        Args:
            from_layer: Source layer
            to_layer: Target layer

        Returns:
            Suggestion string
        """
        suggestions = {
            ("domain", "application"): "Domain layer should not depend on application. Move business logic to domain.",
            ("domain", "infrastructure"): "Domain layer should not depend on infrastructure. Use dependency injection.",
            ("domain", "interface"): "Domain layer should not depend on interface. Keep domain pure.",
            ("application", "infrastructure"): "Application should not directly depend on infrastructure. Use ports/adapters pattern.",
            ("application", "interface"): "Application should not depend on interface layer. Interface should call application.",
            ("infrastructure", "application"): "Infrastructure should not depend on application. Use interfaces/ports.",
            ("infrastructure", "interface"): "Infrastructure should not depend on interface layer."
        }

        key = (from_layer, to_layer)
        return suggestions.get(key, f"{from_layer} layer should not depend on {to_layer} layer")

    def to_dict(self, result: LayerCheckResult) -> dict:
        """Convert result to dictionary for JSON serialization.

        Args:
            result: LayerCheckResult

        Returns:
            Dictionary representation
        """
        return {
            "project_path": result.project_path,
            "violations": [
                {
                    "from_layer": v.from_layer,
                    "to_layer": v.to_layer,
                    "from_file": v.from_file,
                    "to_file": v.to_file,
                    "from_line": v.from_line,
                    "import_module": v.import_module,
                    "suggestion": v.suggestion
                }
                for v in result.violations
            ],
            "violation_count": result.violation_count,
            "layers_detected": result.layers_detected,
            "layer_stats": {
                layer: {
                    "name": stats.name,
                    "file_count": stats.file_count,
                    "import_count": stats.import_count,
                    "violation_count": stats.violation_count
                }
                for layer, stats in result.layer_stats.items()
            },
            "rules_applied": result.rules_applied,
            "message": result.message
        }
