"""Parse error operations mixin for SQLite storage.

This module contains parse error-related database operations.
"""

import logging
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    import sqlite3

from ..base import ParseErrorRecord

logger = logging.getLogger(__name__)


class ErrorOpsMixin:
    """Mixin class for parse error-related database operations."""

    conn: "sqlite3.Connection"

    def _get_cursor(self) -> "sqlite3.Cursor":
        """Get a database cursor."""
        return self.conn.cursor()

    def save_parse_error(
        self,
        file_id: int,
        error_message: str,
        error_line: Optional[int] = None
    ) -> int:
        """Save a parse error record.

        Args:
            file_id: File ID
            error_message: Error message
            error_line: Optional error line number

        Returns:
            Created parse_error ID
        """
        cursor = self._get_cursor()
        cursor.execute(
            """
            INSERT INTO parse_errors (file_id, error_message, error_line)
            VALUES (?, ?, ?)
            """,
            (file_id, error_message, error_line)
        )
        error_id = cursor.lastrowid
        self.conn.commit()
        return error_id

    def get_parse_errors(self, project_id: int) -> list[ParseErrorRecord]:
        """Get all parse errors for a project.

        Args:
            project_id: Project ID

        Returns:
            List of ParseErrorRecord objects
        """
        cursor = self._get_cursor()
        cursor.execute(
            """
            SELECT pe.* FROM parse_errors pe
            JOIN files f ON pe.file_id = f.id
            WHERE f.project_id = ?
            ORDER BY pe.created_at DESC
            """,
            (project_id,)
        )
        rows = cursor.fetchall()

        return [
            ParseErrorRecord(
                id=row["id"],
                file_id=row["file_id"],
                error_message=row["error_message"],
                error_line=row["error_line"],
                created_at=row["created_at"]
            )
            for row in rows
        ]

    def clear_parse_errors(self, file_id: int) -> int:
        """Clear parse errors for a file.

        Args:
            file_id: File ID

        Returns:
            Number of deleted errors
        """
        cursor = self._get_cursor()
        cursor.execute(
            "DELETE FROM parse_errors WHERE file_id = ?",
            (file_id,)
        )
        deleted = cursor.rowcount
        self.conn.commit()
        return deleted

    def clear_all_parse_errors(self, project_id: int) -> int:
        """Clear all parse errors for a project.

        Args:
            project_id: Project ID

        Returns:
            Number of deleted errors
        """
        cursor = self._get_cursor()
        cursor.execute(
            """
            DELETE FROM parse_errors WHERE file_id IN (
                SELECT id FROM files WHERE project_id = ?
            )
            """,
            (project_id,)
        )
        deleted = cursor.rowcount
        self.conn.commit()
        return deleted
