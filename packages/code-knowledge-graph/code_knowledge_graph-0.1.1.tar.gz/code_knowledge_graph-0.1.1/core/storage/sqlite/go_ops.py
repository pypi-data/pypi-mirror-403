"""Go module operations mixin for SQLite storage.

This module contains Go-specific database operations.
"""

import logging
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    import sqlite3

from ..base import GoModuleRecord

logger = logging.getLogger(__name__)


class GoOpsMixin:
    """Mixin class for Go module-related database operations."""

    conn: "sqlite3.Connection"

    def _get_cursor(self) -> "sqlite3.Cursor":
        """Get a database cursor."""
        return self.conn.cursor()

    def save_go_module(
        self,
        project_id: int,
        module_path: str
    ) -> int:
        """Save Go module information.

        Args:
            project_id: Project ID
            module_path: Module path from go.mod

        Returns:
            Created go_module ID
        """
        cursor = self._get_cursor()

        # Delete existing module for this project
        cursor.execute(
            "DELETE FROM go_modules WHERE project_id = ?",
            (project_id,)
        )

        cursor.execute(
            """
            INSERT INTO go_modules (project_id, module_path)
            VALUES (?, ?)
            """,
            (project_id, module_path)
        )
        module_id = cursor.lastrowid
        self.conn.commit()
        return module_id

    def get_go_module(self, project_id: int) -> Optional[GoModuleRecord]:
        """Get Go module information for a project.

        Args:
            project_id: Project ID

        Returns:
            GoModuleRecord if found, None otherwise
        """
        cursor = self._get_cursor()
        cursor.execute(
            "SELECT * FROM go_modules WHERE project_id = ?",
            (project_id,)
        )
        row = cursor.fetchone()
        if row:
            return GoModuleRecord(
                id=row["id"],
                project_id=row["project_id"],
                module_path=row["module_path"]
            )
        return None
