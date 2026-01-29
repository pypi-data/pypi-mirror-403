"""Base storage backend interface and data models.

This module defines the abstract storage interface and data classes
for persisting code knowledge graph data.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class ProjectRecord:
    """Project record stored in database."""

    id: int
    path: str
    name: str
    last_scanned: datetime
    file_count: int

    def __post_init__(self):
        if isinstance(self.last_scanned, str):
            self.last_scanned = datetime.fromisoformat(self.last_scanned)


@dataclass
class FileRecord:
    """File record stored in database."""

    id: int
    project_id: int
    relative_path: str
    file_type: str
    size: int
    depth: int
    modified_time: datetime

    def __post_init__(self):
        if isinstance(self.modified_time, str):
            self.modified_time = datetime.fromisoformat(self.modified_time)


@dataclass
class ImportRecord:
    """Import record stored in database."""

    id: int
    file_id: int
    module: str
    import_type: str  # 'static', 'dynamic', 'require'
    line: int
    resolved_file_id: Optional[int] = None  # NULL if external dependency

    def is_external(self) -> bool:
        """Check if this import is an external dependency."""
        return self.resolved_file_id is None


@dataclass
class FunctionRecord:
    """Function record stored in database."""

    id: int
    file_id: int
    name: str
    signature: str
    start_line: int
    end_line: int


@dataclass
class FunctionCallRecord:
    """Function call record stored in database (legacy)."""

    id: int
    caller_function_id: int
    callee_name: str
    callee_function_id: Optional[int] = None  # NULL if external call
    line: int = 0

    def is_external(self) -> bool:
        """Check if this is an external function call."""
        return self.callee_function_id is None


@dataclass
class SymbolRecord:
    """Symbol record stored in database (enhanced)."""

    id: int
    file_id: int
    name: str
    symbol_type: str  # function, class, method, variable, struct, interface
    container_name: Optional[str]
    signature: str
    docstring: Optional[str]
    start_line: int
    end_line: int
    is_exported: bool = True
    method_set_signature: Optional[str] = None  # Go interface matching


@dataclass
class EnhancedFunctionCallRecord:
    """Enhanced function call record stored in database."""

    id: int
    source_symbol_id: int
    source_file_id: int
    target_symbol_id: Optional[int]
    target_symbol_name: str
    call_type: str  # direct, potential, deferred, async
    call_context: Optional[str]
    line_number: int

    def is_external(self) -> bool:
        """Check if this is an external function call."""
        return self.target_symbol_id is None


@dataclass
class GoModuleRecord:
    """Go module record stored in database."""

    id: int
    project_id: int
    module_path: str


@dataclass
class ParseErrorRecord:
    """Parse error record stored in database."""

    id: int
    file_id: int
    error_message: str
    error_line: Optional[int]
    created_at: datetime

    def __post_init__(self):
        if isinstance(self.created_at, str):
            self.created_at = datetime.fromisoformat(self.created_at)


@dataclass
class CodeSummaryRecord:
    """Code summary record stored in database (LLM-generated)."""

    id: int
    file_id: int
    entity_type: str  # 'function' or 'class'
    entity_name: str
    signature: str
    summary: str  # LLM-generated bilingual summary (format: "English | 中文")
    line_number: int
    summary_en: str = ""  # English-only summary
    summary_zh: str = ""  # Chinese-only summary
    embedding: Optional[list[float]] = None  # Vector embedding for semantic search
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if isinstance(self.created_at, str):
            self.created_at = datetime.fromisoformat(self.created_at)


@dataclass
class FileTypeStats:
    """File type statistics."""

    file_type: str
    count: int
    percentage: float
    total_size: int


@dataclass
class DepthStats:
    """Directory and file depth statistics."""

    max_directory_depth: int
    max_file_depth: int
    min_file_depth: int
    avg_file_depth: float
    depth_distribution: dict[int, int]  # {depth: file_count}


@dataclass
class ReferenceRankingItem:
    """Reference ranking item."""

    file_path: str
    reference_count: int
    referencing_files: list[str]


class StorageBackend(ABC):
    """Abstract storage backend interface.

    This class defines the interface for all storage backends.
    Implementations include SQLite, graph databases, and vector stores.
    """

    @abstractmethod
    def save_project(
        self,
        path: Path,
        files: list,
        graph: dict
    ) -> int:
        """Save project data to storage.

        Args:
            path: Project root path
            files: List of FileInfo objects from scanner
            graph: Dependency graph data

        Returns:
            project_id: The ID of the saved/updated project
        """
        pass

    @abstractmethod
    def get_project(self, path: str) -> Optional[ProjectRecord]:
        """Get project record by path.

        Args:
            path: Project root path

        Returns:
            ProjectRecord if found, None otherwise
        """
        pass

    @abstractmethod
    def get_project_by_id(self, project_id: int) -> Optional[ProjectRecord]:
        """Get project record by ID.

        Args:
            project_id: Project ID

        Returns:
            ProjectRecord if found, None otherwise
        """
        pass

    @abstractmethod
    def get_files_by_project(
        self,
        project_id: int,
        file_type: Optional[str] = None,
        subdirectory: Optional[str] = None
    ) -> list[FileRecord]:
        """Get all files for a project.

        Args:
            project_id: Project ID
            file_type: Optional filter by file type
            subdirectory: Optional filter by subdirectory path

        Returns:
            List of FileRecord objects
        """
        pass

    @abstractmethod
    def get_file_by_path(
        self,
        project_id: int,
        relative_path: str
    ) -> Optional[FileRecord]:
        """Get a file record by its relative path.

        Args:
            project_id: Project ID
            relative_path: File path relative to project root

        Returns:
            FileRecord if found, None otherwise
        """
        pass

    @abstractmethod
    def get_imports_by_file(self, file_id: int) -> list[ImportRecord]:
        """Get all imports for a file.

        Args:
            file_id: File ID

        Returns:
            List of ImportRecord objects
        """
        pass

    @abstractmethod
    def get_file_stats(
        self,
        project_id: int,
        subdirectory: Optional[str] = None
    ) -> list[FileTypeStats]:
        """Get file type statistics for a project.

        Args:
            project_id: Project ID
            subdirectory: Optional filter by subdirectory

        Returns:
            List of FileTypeStats objects
        """
        pass

    @abstractmethod
    def get_reference_ranking(
        self,
        project_id: int,
        limit: int = 20,
        file_type: Optional[str] = None
    ) -> list[ReferenceRankingItem]:
        """Get files ranked by incoming reference count.

        Args:
            project_id: Project ID
            limit: Maximum number of results
            file_type: Optional filter by file type

        Returns:
            List of ReferenceRankingItem objects, sorted by reference count
        """
        pass

    @abstractmethod
    def get_depth_stats(
        self,
        project_id: int,
        subdirectory: Optional[str] = None
    ) -> DepthStats:
        """Get directory and file depth statistics.

        Args:
            project_id: Project ID
            subdirectory: Optional filter by subdirectory

        Returns:
            DepthStats object
        """
        pass

    @abstractmethod
    def get_file_imports(
        self,
        project_id: int,
        file_path: str
    ) -> list[str]:
        """Get files that the target file imports (outgoing dependencies).

        Args:
            project_id: Project ID
            file_path: Target file path

        Returns:
            List of file paths that the target imports
        """
        pass

    @abstractmethod
    def get_file_importers(
        self,
        project_id: int,
        file_path: str
    ) -> list[str]:
        """Get files that import the target file (incoming dependencies).

        Args:
            project_id: Project ID
            file_path: Target file path

        Returns:
            List of file paths that import the target
        """
        pass

    @abstractmethod
    def save_functions(
        self,
        file_id: int,
        functions: list[dict]
    ) -> list[int]:
        """Save function records for a file.

        Args:
            file_id: File ID
            functions: List of function info dicts with name, signature, start_line, end_line

        Returns:
            List of created function IDs
        """
        pass

    @abstractmethod
    def get_functions_by_file(self, file_id: int) -> list[FunctionRecord]:
        """Get all functions for a file.

        Args:
            file_id: File ID

        Returns:
            List of FunctionRecord objects
        """
        pass

    @abstractmethod
    def save_function_calls(
        self,
        caller_function_id: int,
        calls: list[dict]
    ) -> list[int]:
        """Save function call records.

        Args:
            caller_function_id: Caller function ID
            calls: List of call info dicts with callee_name, line, callee_function_id

        Returns:
            List of created call IDs
        """
        pass

    @abstractmethod
    def get_function_calls(
        self,
        function_id: int
    ) -> list[FunctionCallRecord]:
        """Get all function calls made by a function.

        Args:
            function_id: Function ID

        Returns:
            List of FunctionCallRecord objects
        """
        pass

    @abstractmethod
    def save_summaries(
        self,
        summaries: list[dict]
    ) -> list[int]:
        """Save code summaries.

        Args:
            summaries: List of summary dicts with file_id, entity_type, entity_name,
                      signature, summary, line_number

        Returns:
            List of created summary IDs
        """
        pass

    @abstractmethod
    def get_summary(
        self,
        file_id: int,
        entity_name: str
    ) -> Optional[CodeSummaryRecord]:
        """Get code summary for an entity.

        Args:
            file_id: File ID
            entity_name: Function or class name

        Returns:
            CodeSummaryRecord if found, None otherwise
        """
        pass

    @abstractmethod
    def get_summaries_by_file(
        self,
        file_id: int
    ) -> list[CodeSummaryRecord]:
        """Get all summaries for a file.

        Args:
            file_id: File ID

        Returns:
            List of CodeSummaryRecord objects
        """
        pass

    @abstractmethod
    def list_projects(self) -> list[ProjectRecord]:
        """List all stored projects.

        Returns:
            List of ProjectRecord objects
        """
        pass

    @abstractmethod
    def delete_project(self, project_id: int) -> bool:
        """Delete a project and all its data.

        Args:
            project_id: Project ID

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """Close the storage connection."""
        pass
