"""Related Code Context Service (Repo Map).

This module provides services for retrieving related code context,
including file signatures and dependencies within N hops.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Union

from ..parsers import (
    PythonParser,
    JsParser,
    VueParser,
    FunctionInfo,
    ClassInfo,
)
from ..storage import StorageBackend, CodeSummaryRecord
from .skeleton import SkeletonMode, SkeletonExtractor, SkeletonContent


@dataclass
class SignatureInfo:
    """Signature information for a function or class."""

    name: str
    entity_type: str  # "function" or "class"
    signature: str
    line: int
    summary: Optional[str] = None


@dataclass
class FileContext:
    """File context information."""

    file_path: str
    file_type: str
    signatures: list[SignatureInfo] = field(default_factory=list)
    relation: str = "target"  # "target", "imports", "imported_by"
    hop_distance: int = 0
    skeleton_content: Optional[str] = None  # Skeleton string representation


@dataclass
class RelatedCodeContext:
    """Related code context response."""

    target_file: FileContext
    related_files: list[FileContext] = field(default_factory=list)
    total_files: int = 1
    truncated: bool = False
    message: Optional[str] = None


class RelatedContextService:
    """Service for retrieving related code context (Repo Map).

    Provides BFS traversal of dependency graph to find related files
    within N hops and extracts their signatures.
    
    Supports skeleton extraction modes:
    - full: Complete file content
    - skeleton: Signatures, docstrings, imports, global variables (default)
    - signature_only: Only function/class names and signatures
    """

    MAX_FILES = 50
    MAX_HOPS = 3

    def __init__(self, storage: StorageBackend, project_root: Optional[Path] = None):
        """Initialize related context service.

        Args:
            storage: Storage backend for accessing project data
            project_root: Optional project root path for reading files
        """
        self.storage = storage
        self.project_root = project_root
        self.parsers = [
            PythonParser(),
            JsParser(),
            VueParser(),
        ]
        self.skeleton_extractor = SkeletonExtractor(
            storage=storage,
            project_root=project_root
        )

    def get_related_context(
        self,
        project_path: str,
        file_path: str,
        hops: int = 1,
        include_external: bool = False,
        mode: Union[str, SkeletonMode] = SkeletonMode.SKELETON
    ) -> RelatedCodeContext:
        """Get related code context for a file.

        Uses BFS traversal to find files within N hops of the target file,
        extracting content based on the specified mode.
        
        **Validates: Requirements 2.1, 2.2, 2.3, 2.6**

        Args:
            project_path: Path to the project
            file_path: Relative path to the target file
            hops: Number of dependency hops to traverse (1-3)
            include_external: Whether to include external dependencies
            mode: Skeleton extraction mode (full, skeleton, signature_only)
                  Default is skeleton mode for optimized token usage.

        Returns:
            RelatedCodeContext with target file and related files
        """
        # Convert string mode to enum
        if isinstance(mode, str):
            try:
                mode = SkeletonMode(mode)
            except ValueError:
                mode = SkeletonMode.SKELETON
        
        hops = min(max(hops, 1), self.MAX_HOPS)

        # Get project
        project = self.storage.get_project(project_path)
        if not project:
            return RelatedCodeContext(
                target_file=FileContext(
                    file_path=file_path,
                    file_type="unknown",
                    relation="target"
                ),
                message=f"Project not found: {project_path}"
            )

        project_id = project.id
        project_root = Path(project_path)

        # Get target file
        target_file = self.storage.get_file_by_path(project_id, file_path)
        if not target_file:
            return RelatedCodeContext(
                target_file=FileContext(
                    file_path=file_path,
                    file_type="unknown",
                    relation="target"
                ),
                message=f"File not found: {file_path}"
            )

        # Get target file context
        target_context = self._get_file_context(
            project_id=project_id,
            project_root=project_root,
            file_path=file_path,
            file_type=target_file.file_type,
            relation="target",
            hop_distance=0,
            mode=mode
        )

        # BFS traversal to find related files
        visited = {file_path}
        related_files: list[FileContext] = []
        current_level = [file_path]

        for hop in range(1, hops + 1):
            if len(related_files) >= self.MAX_FILES:
                break

            next_level = []

            for current_file in current_level:
                # Get outgoing dependencies (files this file imports)
                imports = self.storage.get_file_imports(project_id, current_file)
                for imp_path in imports:
                    if imp_path not in visited:
                        visited.add(imp_path)
                        next_level.append(imp_path)

                        imp_file = self.storage.get_file_by_path(
                            project_id, imp_path
                        )
                        if imp_file:
                            context = self._get_file_context(
                                project_id=project_id,
                                project_root=project_root,
                                file_path=imp_path,
                                file_type=imp_file.file_type,
                                relation="imports",
                                hop_distance=hop,
                                mode=mode
                            )
                            related_files.append(context)

                        if len(related_files) >= self.MAX_FILES:
                            break

                if len(related_files) >= self.MAX_FILES:
                    break

                # Get incoming dependencies (files that import this file)
                importers = self.storage.get_file_importers(project_id, current_file)
                for importer_path in importers:
                    if importer_path not in visited:
                        visited.add(importer_path)
                        next_level.append(importer_path)

                        importer_file = self.storage.get_file_by_path(
                            project_id, importer_path
                        )
                        if importer_file:
                            context = self._get_file_context(
                                project_id=project_id,
                                project_root=project_root,
                                file_path=importer_path,
                                file_type=importer_file.file_type,
                                relation="imported_by",
                                hop_distance=hop,
                                mode=mode
                            )
                            related_files.append(context)

                        if len(related_files) >= self.MAX_FILES:
                            break

                if len(related_files) >= self.MAX_FILES:
                    break

            current_level = next_level

        # Check if truncated
        truncated = len(related_files) >= self.MAX_FILES
        message = None
        if truncated:
            message = f"Results truncated to {self.MAX_FILES} files"

        return RelatedCodeContext(
            target_file=target_context,
            related_files=related_files[:self.MAX_FILES],
            total_files=len(visited),
            truncated=truncated,
            message=message
        )

    def _get_file_context(
        self,
        project_id: int,
        project_root: Path,
        file_path: str,
        file_type: str,
        relation: str,
        hop_distance: int,
        mode: SkeletonMode = SkeletonMode.SKELETON
    ) -> FileContext:
        """Get context for a single file.

        Extracts content based on the specified mode and attaches summaries if available.

        Args:
            project_id: Project ID in storage
            project_root: Project root path
            file_path: Relative path to file
            file_type: Type of file (python, javascript, etc.)
            relation: Relationship to target ("target", "imports", "imported_by")
            hop_distance: Distance from target file in hops
            mode: Skeleton extraction mode

        Returns:
            FileContext with signatures and metadata
        """
        # Use skeleton extractor for content extraction
        skeleton = self.skeleton_extractor.extract(file_path, mode)
        skeleton_content = self.skeleton_extractor.to_string(skeleton, mode)
        
        # Also extract signatures for backward compatibility
        signatures = self._extract_signatures(project_root, file_path)

        # Attach summaries if available
        file_record = self.storage.get_file_by_path(project_id, file_path)
        if file_record:
            summaries_by_name = {}
            file_summaries = self.storage.get_summaries_by_file(file_record.id)
            for summary in file_summaries:
                summaries_by_name[summary.entity_name] = summary.summary

            for sig in signatures:
                if sig.name in summaries_by_name:
                    sig.summary = summaries_by_name[sig.name]

        return FileContext(
            file_path=file_path,
            file_type=file_type,
            signatures=signatures,
            relation=relation,
            hop_distance=hop_distance,
            skeleton_content=skeleton_content
        )

    def _extract_signatures(
        self,
        project_root: Path,
        file_path: str
    ) -> list[SignatureInfo]:
        """Extract function and class signatures from a file.

        Only extracts the signature line, not the implementation body.

        Args:
            project_root: Project root path
            file_path: Relative path to file

        Returns:
            List of SignatureInfo objects
        """
        signatures: list[SignatureInfo] = []
        full_path = project_root / file_path

        if not full_path.exists():
            return signatures

        # Find appropriate parser
        parser = None
        for p in self.parsers:
            if p.can_parse(full_path):
                parser = p
                break

        if not parser:
            return signatures

        try:
            content = full_path.read_text(encoding="utf-8", errors="ignore")
            result = parser.parse_full(content, full_path)

            # Extract function signatures
            for func in result.functions:
                signatures.append(SignatureInfo(
                    name=func.name,
                    entity_type="function",
                    signature=func.signature,
                    line=func.start_line,
                    summary=func.docstring
                ))

            # Extract class signatures and their methods
            for cls in result.classes:
                signatures.append(SignatureInfo(
                    name=cls.name,
                    entity_type="class",
                    signature=cls.signature,
                    line=cls.start_line,
                    summary=cls.docstring
                ))

                # Include method signatures
                for method in cls.methods:
                    signatures.append(SignatureInfo(
                        name=f"{cls.name}.{method.name}",
                        entity_type="method",
                        signature=method.signature,
                        line=method.start_line,
                        summary=method.docstring
                    ))

        except Exception:
            pass

        return signatures

    def to_dict(self, result: RelatedCodeContext) -> dict:
        """Convert RelatedCodeContext to dictionary for JSON serialization.

        Args:
            result: RelatedCodeContext to convert

        Returns:
            Dictionary representation
        """
        return {
            "target_file": self._file_context_to_dict(result.target_file),
            "related_files": [
                self._file_context_to_dict(f) for f in result.related_files
            ],
            "total_files": result.total_files,
            "truncated": result.truncated,
            "message": result.message
        }

    def _file_context_to_dict(self, context: FileContext) -> dict:
        """Convert FileContext to dictionary."""
        result = {
            "file_path": context.file_path,
            "file_type": context.file_type,
            "signatures": [
                {
                    "name": sig.name,
                    "type": sig.entity_type,
                    "signature": sig.signature,
                    "line": sig.line,
                    "summary": sig.summary
                }
                for sig in context.signatures
            ],
            "relation": context.relation,
            "hop_distance": context.hop_distance
        }
        
        # Include skeleton content if available
        if context.skeleton_content:
            result["skeleton_content"] = context.skeleton_content
        
        return result
