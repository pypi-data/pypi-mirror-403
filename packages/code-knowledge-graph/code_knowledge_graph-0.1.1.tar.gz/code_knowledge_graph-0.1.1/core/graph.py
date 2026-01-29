"""Dependency graph builder."""

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

from .scanner import CodeScanner, FileInfo


@dataclass
class Node:
    """Graph node representing a file."""

    id: str  # Relative path
    type: str  # python, javascript, typescript, vue, env, external
    size: int = 0
    label: str = ""  # Display name

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Edge:
    """Graph edge representing a dependency."""

    source: str  # From file (importer)
    target: str  # To file (imported)
    import_type: str = "static"  # static, dynamic, require

    def to_dict(self) -> dict[str, Any]:
        return {"from": self.source, "to": self.target, "type": self.import_type}


@dataclass
class GraphData:
    """Complete dependency graph data."""

    nodes: list[Node] = field(default_factory=list)
    edges: list[Edge] = field(default_factory=list)
    external_deps: set[str] = field(default_factory=set)

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
            "external": sorted(self.external_deps),
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


class GraphBuilder:
    """Builds dependency graph from scanned files."""

    # Common index file names for resolution
    INDEX_FILES = ["index.js", "index.ts", "index.jsx", "index.tsx", "index.vue"]

    def __init__(self, root_path: str | Path):
        self.root_path = Path(root_path).resolve()
        self._file_map: dict[str, FileInfo] = {}
        self._path_aliases: dict[str, str] = {}
        self._go_module_path: str | None = None
        self._load_path_aliases()
        self._load_go_module()

    def build(self, files: list[FileInfo]) -> GraphData:
        """Build dependency graph from file list."""
        graph = GraphData()

        # Build file map for path resolution
        self._file_map = {f.relative_path: f for f in files}

        # Add file nodes
        for file_info in files:
            node = Node(
                id=file_info.relative_path,
                type=file_info.file_type,
                size=file_info.size,
                label=Path(file_info.relative_path).name,
            )
            graph.nodes.append(node)

        # Add edges based on imports
        for file_info in files:
            self._add_edges(file_info, graph)

        # Add external dependency nodes
        for ext_dep in graph.external_deps:
            node = Node(
                id=f"external:{ext_dep}",
                type="external",
                size=0,
                label=ext_dep,
            )
            graph.nodes.append(node)

        return graph

    def _add_edges(self, file_info: FileInfo, graph: GraphData) -> None:
        """Add edges for all imports in a file."""
        for imp in file_info.imports:
            # Special handling for Go module imports - connect to all files in package
            if self._go_module_path and imp.module.startswith(self._go_module_path + "/"):
                relative_path = imp.module[len(self._go_module_path) + 1:]
                package_files = self._resolve_go_package_all(relative_path)
                if package_files:
                    for target_file in package_files:
                        edge = Edge(
                            source=file_info.relative_path,
                            target=target_file,
                            import_type=imp.import_type,
                        )
                        graph.edges.append(edge)
                    continue
                # If no files found, fall through to external dependency handling

            resolved = self._resolve_import(imp.module, file_info.relative_path)

            if resolved is None:
                # External dependency
                module_name = self._get_package_name(imp.module)
                graph.external_deps.add(module_name)
                edge = Edge(
                    source=file_info.relative_path,
                    target=f"external:{module_name}",
                    import_type=imp.import_type,
                )
            else:
                edge = Edge(
                    source=file_info.relative_path,
                    target=resolved,
                    import_type=imp.import_type,
                )

            graph.edges.append(edge)

    def _resolve_import(self, module: str, from_file: str) -> str | None:
        """
        Resolve import path to actual file path.

        Returns None if the import is external.
        """
        # Handle Go module imports (e.g., "mymodule/internal/pkg")
        if self._go_module_path and module.startswith(self._go_module_path + "/"):
            # Strip module prefix to get project-relative path
            relative_path = module[len(self._go_module_path) + 1:]
            return self._resolve_go_package(relative_path)

        # Handle path aliases like @/
        if module.startswith("@/"):
            module = self._resolve_alias(module)

        # Handle relative imports
        if module.startswith("."):
            return self._resolve_relative(module, from_file)

        # Handle Python-style imports (dotted)
        if "." in module and "/" not in module and "\\" not in module:
            return self._resolve_python_import(module)

        # Try direct resolution (for JS absolute imports within project)
        return self._find_file(module)

    def _resolve_relative(self, module: str, from_file: str) -> str | None:
        """Resolve relative import path."""
        from_dir = str(Path(from_file).parent).replace("\\", "/")

        # Normalize the path
        if from_dir == ".":
            from_dir = ""

        # Handle Python relative imports like .foo, ..foo, ...foo
        # Convert leading dots to proper relative path
        dot_count = 0
        for c in module:
            if c == ".":
                dot_count += 1
            else:
                break

        # Get the actual module name after dots
        module_name = module[dot_count:]

        # Build the base directory by going up (dot_count - 1) levels
        # . means current dir, .. means parent, etc.
        base_parts = from_dir.split("/") if from_dir else []
        levels_up = dot_count - 1  # . = 0 levels up, .. = 1 level up

        if levels_up > 0:
            base_parts = base_parts[:-levels_up] if levels_up < len(base_parts) else []

        # Combine base with module name
        if module_name:
            # Handle both Python dotted notation and JS path notation
            if "/" in module_name:
                path_parts = module_name.split("/")
            else:
                path_parts = module_name.split(".")

            full_parts = base_parts + path_parts
        else:
            full_parts = base_parts

        normalized = "/".join(full_parts)
        return self._find_file(normalized)

    def _resolve_python_import(self, module: str) -> str | None:
        """Resolve Python dotted import to file path."""
        # Convert dots to path separators
        path = module.replace(".", "/")
        return self._find_file(path)

    def _resolve_go_package(self, package_path: str) -> str | None:
        """Resolve Go package path to actual file(s).

        Go packages are directories, not individual files.
        Returns the first .go file in the package directory as representative.

        Args:
            package_path: Package path relative to module root (e.g., "internal/domain/user")

        Returns:
            File path of a representative .go file, or None if not found
        """
        files = self._resolve_go_package_all(package_path)
        return files[0] if files else None

    def _resolve_go_package_all(self, package_path: str) -> list[str]:
        """Resolve Go package path to all files in the package.

        Go packages are directories containing multiple .go files.
        Returns all .go files in the package directory (excluding test files).

        Args:
            package_path: Package path relative to module root (e.g., "internal/domain/user")

        Returns:
            List of file paths for all .go files in the package
        """
        # Normalize path separators
        package_path = package_path.replace("\\", "/")
        result = []

        # Look for .go files in this package directory
        for file_path in self._file_map:
            normalized_file = file_path.replace("\\", "/")
            # Check if file is in the target package directory
            if normalized_file.startswith(package_path + "/"):
                # Ensure it's a direct child, not in a subdirectory
                remaining = normalized_file[len(package_path) + 1:]
                if "/" not in remaining:
                    # Skip test files
                    if normalized_file.endswith(".go") and not normalized_file.endswith("_test.go"):
                        result.append(file_path)

        return result

    def _find_file(self, path: str) -> str | None:
        """Find actual file for a given import path."""
        # Direct match
        if path in self._file_map:
            return path

        # Try with common extensions
        extensions = [".py", ".js", ".ts", ".jsx", ".tsx", ".vue"]
        for ext in extensions:
            candidate = path + ext
            if candidate in self._file_map:
                return candidate

        # Try index files for directory imports
        for index_file in self.INDEX_FILES:
            candidate = f"{path}/{index_file}"
            if candidate in self._file_map:
                return candidate

        # Try __init__.py for Python packages
        candidate = f"{path}/__init__.py"
        if candidate in self._file_map:
            return candidate

        return None

    def _get_package_name(self, module: str) -> str:
        """Extract package name from import path."""
        # Handle scoped packages like @vue/core
        if module.startswith("@"):
            parts = module.split("/")
            if len(parts) >= 2:
                return f"{parts[0]}/{parts[1]}"
            return module

        # Regular package - first part before /
        return module.split("/")[0].split("\\")[0]

    def _load_go_module(self) -> None:
        """Load Go module path from go.mod."""
        go_mod_path = self.root_path / "go.mod"
        if go_mod_path.exists():
            try:
                content = go_mod_path.read_text(encoding="utf-8")
                for line in content.split('\n'):
                    line = line.strip()
                    if line.startswith("module "):
                        module_path = line[7:].strip()
                        # Remove trailing comments
                        if "//" in module_path:
                            module_path = module_path.split("//")[0].strip()
                        self._go_module_path = module_path
                        break
            except Exception:
                pass

    def _load_path_aliases(self) -> None:
        """Load path aliases from tsconfig/jsconfig."""
        for config_name in ["tsconfig.json", "jsconfig.json"]:
            config_path = self.root_path / config_name
            if config_path.exists():
                try:
                    config = json.loads(config_path.read_text(encoding="utf-8"))
                    paths = config.get("compilerOptions", {}).get("paths", {})
                    base_url = config.get("compilerOptions", {}).get("baseUrl", ".")

                    for alias, targets in paths.items():
                        if targets:
                            # Remove trailing /* from alias
                            clean_alias = alias.rstrip("/*")
                            # Remove trailing /* from target and combine with baseUrl
                            target = targets[0].rstrip("/*")
                            self._path_aliases[clean_alias] = str(
                                Path(base_url) / target
                            ).replace("\\", "/")
                    break
                except Exception:
                    pass

    def _resolve_alias(self, module: str) -> str:
        """Resolve path alias to actual path."""
        for alias, target in self._path_aliases.items():
            if module.startswith(alias):
                return module.replace(alias, target, 1)

        # Default: @ -> src
        if module.startswith("@/"):
            return module.replace("@/", "src/", 1)

        return module
