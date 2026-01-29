"""Directory scanner for code files."""

from pathlib import Path
from dataclasses import dataclass
from typing import Iterator

from .parsers import BaseParser, ImportInfo, PythonParser, JsParser, VueParser, GoParser


@dataclass
class FileInfo:
    """Information about a scanned file."""

    path: Path  # Absolute path
    relative_path: str  # Path relative to project root
    file_type: str  # python, javascript, typescript, vue, go, env
    size: int  # File size in bytes
    imports: list[ImportInfo]  # Extracted imports


class CodeScanner:
    """Scans directory for code files and extracts imports."""

    # File extensions to scan
    CODE_EXTENSIONS = {
        ".py": "python",
        ".pyw": "python",
        ".js": "javascript",
        ".jsx": "javascript",
        ".mjs": "javascript",
        ".cjs": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".vue": "vue",
        ".go": "go",
    }

    ENV_FILES = {".env", ".env.local", ".env.development", ".env.production"}

    # Directories to ignore
    IGNORE_DIRS = {
        "node_modules",
        "__pycache__",
        ".git",
        ".svn",
        ".hg",
        "venv",
        ".venv",
        "env",
        ".env",
        "dist",
        "build",
        ".next",
        ".nuxt",
        "coverage",
        ".pytest_cache",
        ".mypy_cache",
        ".tox",
        "eggs",
        "*.egg-info",
    }

    def __init__(self, root_path: str | Path):
        self.root_path = Path(root_path).resolve()
        self._parsers: list[BaseParser] = [
            PythonParser(),
            JsParser(),
            VueParser(),
            GoParser(),
        ]

    def scan(self) -> list[FileInfo]:
        """Scan the directory and return file information with imports."""
        files: list[FileInfo] = []

        for file_path in self._iter_files():
            file_info = self._process_file(file_path)
            if file_info:
                files.append(file_info)

        return files

    def _iter_files(self) -> Iterator[Path]:
        """Iterate over all relevant files in the directory."""
        for path in self.root_path.rglob("*"):
            if not path.is_file():
                continue

            # Skip ignored directories
            if self._should_ignore(path):
                continue

            # Check if it's a code file or env file
            if self._is_code_file(path) or self._is_env_file(path):
                yield path

    def _should_ignore(self, path: Path) -> bool:
        """Check if path should be ignored."""
        parts = path.relative_to(self.root_path).parts
        for part in parts[:-1]:  # Check directory parts, not filename
            if part in self.IGNORE_DIRS:
                return True
            # Handle wildcard patterns like *.egg-info
            for pattern in self.IGNORE_DIRS:
                if "*" in pattern and path.match(pattern):
                    return True
        return False

    def _is_code_file(self, path: Path) -> bool:
        """Check if file is a code file."""
        return path.suffix.lower() in self.CODE_EXTENSIONS

    def _is_env_file(self, path: Path) -> bool:
        """Check if file is an env file."""
        return path.name in self.ENV_FILES or path.name.startswith(".env")

    def _get_file_type(self, path: Path) -> str:
        """Get the file type for a given path."""
        if self._is_env_file(path):
            return "env"
        return self.CODE_EXTENSIONS.get(path.suffix.lower(), "unknown")

    def _process_file(self, path: Path) -> FileInfo | None:
        """Process a single file and extract imports."""
        try:
            relative_path = str(path.relative_to(self.root_path)).replace("\\", "/")
            file_type = self._get_file_type(path)
            size = path.stat().st_size

            # Extract imports for code files
            imports: list[ImportInfo] = []
            if file_type != "env":
                content = path.read_text(encoding="utf-8", errors="ignore")
                for parser in self._parsers:
                    if parser.can_parse(path):
                        imports = parser.parse(content, path)
                        break

            return FileInfo(
                path=path,
                relative_path=relative_path,
                file_type=file_type,
                size=size,
                imports=imports,
            )
        except Exception as e:
            print(f"Warning: Failed to process {path}: {e}")
            return None
