"""File operations mixin for SQLite storage.

This module contains file-related database operations.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    import sqlite3

from ..base import FileRecord, ImportRecord

logger = logging.getLogger(__name__)


class FileOpsMixin:
    """Mixin class for file-related database operations."""

    conn: "sqlite3.Connection"

    def _get_cursor(self) -> "sqlite3.Cursor":
        """Get a database cursor."""
        return self.conn.cursor()

    def get_files_by_project(
        self,
        project_id: int,
        file_type: Optional[str] = None,
        subdirectory: Optional[str] = None
    ) -> list[FileRecord]:
        """Get all files for a project."""
        cursor = self._get_cursor()

        query = "SELECT * FROM files WHERE project_id = ?"
        params: list = [project_id]

        if file_type:
            query += " AND file_type = ?"
            params.append(file_type)

        if subdirectory:
            # Filter by subdirectory prefix
            query += " AND relative_path LIKE ?"
            params.append(f"{subdirectory}%")

        cursor.execute(query, params)
        rows = cursor.fetchall()

        return [
            FileRecord(
                id=row["id"],
                project_id=row["project_id"],
                relative_path=row["relative_path"],
                file_type=row["file_type"],
                size=row["size"],
                depth=row["depth"],
                modified_time=row["modified_time"]
            )
            for row in rows
        ]

    def get_file_by_path(
        self,
        project_id: int,
        relative_path: str
    ) -> Optional[FileRecord]:
        """Get a file record by its relative path."""
        cursor = self._get_cursor()
        cursor.execute(
            """
            SELECT * FROM files
            WHERE project_id = ? AND relative_path = ?
            """,
            (project_id, relative_path)
        )
        row = cursor.fetchone()
        if row:
            return FileRecord(
                id=row["id"],
                project_id=row["project_id"],
                relative_path=row["relative_path"],
                file_type=row["file_type"],
                size=row["size"],
                depth=row["depth"],
                modified_time=row["modified_time"]
            )
        return None

    def get_imports_by_file(self, file_id: int) -> list[ImportRecord]:
        """Get all imports for a file."""
        cursor = self._get_cursor()
        cursor.execute(
            "SELECT * FROM imports WHERE file_id = ?",
            (file_id,)
        )
        rows = cursor.fetchall()

        return [
            ImportRecord(
                id=row["id"],
                file_id=row["file_id"],
                module=row["module"],
                import_type=row["import_type"],
                line=row["line"],
                resolved_file_id=row["resolved_file_id"]
            )
            for row in rows
        ]

    def get_file_imports(
        self,
        project_id: int,
        file_path: str
    ) -> list[str]:
        """Get files that the target file imports (outgoing dependencies)."""
        cursor = self._get_cursor()
        cursor.execute(
            """
            SELECT DISTINCT rf.relative_path
            FROM files f
            JOIN imports i ON i.file_id = f.id
            JOIN files rf ON i.resolved_file_id = rf.id
            WHERE f.project_id = ? AND f.relative_path = ?
            """,
            (project_id, file_path)
        )
        return [row["relative_path"] for row in cursor.fetchall()]

    def get_file_importers(
        self,
        project_id: int,
        file_path: str
    ) -> list[str]:
        """Get files that import the target file (incoming dependencies)."""
        cursor = self._get_cursor()
        cursor.execute(
            """
            SELECT DISTINCT sf.relative_path
            FROM files f
            JOIN imports i ON i.resolved_file_id = f.id
            JOIN files sf ON i.file_id = sf.id
            WHERE f.project_id = ? AND f.relative_path = ?
            """,
            (project_id, file_path)
        )
        return [row["relative_path"] for row in cursor.fetchall()]

    def get_files_needing_update(
        self,
        project_path: Path,
        file_paths: list[str]
    ) -> list[str]:
        """Get list of files that need updating based on modification time."""
        from .project_ops import ProjectOpsMixin

        project = self.get_project(str(project_path.resolve()))
        if not project:
            return file_paths  # All files need update if project doesn't exist

        cursor = self._get_cursor()
        needs_update = []

        for rel_path in file_paths:
            cursor.execute(
                """
                SELECT modified_time FROM files
                WHERE project_id = ? AND relative_path = ?
                """,
                (project.id, rel_path)
            )
            row = cursor.fetchone()

            if not row:
                needs_update.append(rel_path)
                continue

            try:
                current_mtime = datetime.fromtimestamp(
                    Path(project_path / rel_path).stat().st_mtime
                )
            except (OSError, FileNotFoundError):
                needs_update.append(rel_path)
                continue

            stored_mtime = row["modified_time"]
            if isinstance(stored_mtime, str):
                stored_mtime = datetime.fromisoformat(stored_mtime)

            if abs((current_mtime - stored_mtime).total_seconds()) > 1:
                needs_update.append(rel_path)

        return needs_update

    def _module_matches_path(self, module: str, path: str) -> bool:
        """Check if a module name could match a file path."""
        # Normalize module to path-like format
        module_path = module.replace(".", "/")
        path_without_ext = Path(path).with_suffix("").as_posix()

        return (
            path_without_ext.endswith(module_path) or
            module_path in path_without_ext or
            module in path
        )
