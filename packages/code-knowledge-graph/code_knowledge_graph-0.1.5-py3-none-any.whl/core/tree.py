"""Directory tree generator."""

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Literal

from .scanner import CodeScanner


@dataclass
class TreeNode:
    """Node in the directory tree."""

    name: str
    path: str  # Relative path
    type: Literal["file", "directory"]
    file_type: str | None = None  # python, javascript, etc.
    size: int | None = None
    children: list["TreeNode"] | None = None

    def to_dict(self) -> dict[str, Any]:
        result = {
            "name": self.name,
            "path": self.path,
            "type": self.type,
        }
        if self.file_type:
            result["file_type"] = self.file_type
        if self.size is not None:
            result["size"] = self.size
        if self.children is not None:
            result["children"] = [c.to_dict() for c in self.children]
        return result


class TreeBuilder:
    """Builds directory tree structure."""

    def __init__(self, root_path: str | Path):
        self.root_path = Path(root_path).resolve()
        self._scanner = CodeScanner(root_path)

    def build(
        self, 
        directories_only: bool = False, 
        max_depth: int = -1
    ) -> TreeNode:
        """Build and return the directory tree.
        
        Args:
            directories_only: If True, only return directories (no files)
            max_depth: Maximum depth to traverse (-1 for unlimited)
        """
        files = self._scanner.scan()

        # Build tree from file list
        root = TreeNode(
            name=self.root_path.name,
            path="",
            type="directory",
            children=[],
        )

        # Create directory structure
        dir_map: dict[str, TreeNode] = {"": root}

        for file_info in files:
            # Ensure parent directories exist
            parts = file_info.relative_path.split("/")
            current_path = ""

            for i, part in enumerate(parts[:-1]):
                # Check depth limit
                if max_depth >= 0 and i >= max_depth:
                    break
                    
                parent_path = current_path
                current_path = f"{current_path}/{part}" if current_path else part

                if current_path not in dir_map:
                    dir_node = TreeNode(
                        name=part,
                        path=current_path,
                        type="directory",
                        children=[],
                    )
                    dir_map[current_path] = dir_node
                    dir_map[parent_path].children.append(dir_node)

            # Add file node (skip if directories_only)
            if not directories_only:
                # Check depth limit for files
                file_depth = len(parts) - 1
                if max_depth >= 0 and file_depth > max_depth:
                    continue
                    
                file_node = TreeNode(
                    name=parts[-1],
                    path=file_info.relative_path,
                    type="file",
                    file_type=file_info.file_type,
                    size=file_info.size,
                )

                parent_path = "/".join(parts[:-1])
                if parent_path in dir_map:
                    dir_map[parent_path].children.append(file_node)
                else:
                    root.children.append(file_node)

        # Sort children: directories first, then files, both alphabetically
        self._sort_tree(root)

        return root

    def _sort_tree(self, node: TreeNode) -> None:
        """Sort tree children recursively."""
        if node.children is None:
            return

        node.children.sort(
            key=lambda n: (0 if n.type == "directory" else 1, n.name.lower())
        )

        for child in node.children:
            self._sort_tree(child)

    def to_json(self, indent: int = 2, directories_only: bool = False, max_depth: int = -1) -> str:
        """Build tree and return as JSON string."""
        tree = self.build(directories_only=directories_only, max_depth=max_depth)
        return json.dumps(tree.to_dict(), indent=indent, ensure_ascii=False)

    def to_ascii(self, directories_only: bool = False, max_depth: int = -1) -> str:
        """Build tree and return as ASCII art."""
        tree = self.build(directories_only=directories_only, max_depth=max_depth)
        lines: list[str] = [tree.name]
        self._ascii_tree(tree, "", lines)
        return "\n".join(lines)

    def _ascii_tree(
        self, node: TreeNode, prefix: str, lines: list[str]
    ) -> None:
        """Generate ASCII tree representation."""
        if node.children is None:
            return

        for i, child in enumerate(node.children):
            is_last = i == len(node.children) - 1
            connector = "└── " if is_last else "├── "
            extension = "    " if is_last else "│   "

            # Add file type indicator
            if child.type == "file" and child.file_type:
                type_indicator = f" [{child.file_type}]"
            else:
                type_indicator = ""

            lines.append(f"{prefix}{connector}{child.name}{type_indicator}")

            if child.type == "directory":
                self._ascii_tree(child, prefix + extension, lines)
