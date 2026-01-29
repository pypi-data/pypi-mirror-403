"""Symbol operations mixin for SQLite storage.

This module contains symbol-related database operations.
"""

import logging
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    import sqlite3

from ..base import SymbolRecord

logger = logging.getLogger(__name__)


class SymbolOpsMixin:
    """Mixin class for symbol-related database operations."""

    conn: "sqlite3.Connection"

    def _get_cursor(self) -> "sqlite3.Cursor":
        """Get a database cursor."""
        return self.conn.cursor()

    def save_symbols(
        self,
        file_id: int,
        symbols: list[dict]
    ) -> list[int]:
        """Save symbol records for a file.

        Args:
            file_id: File ID
            symbols: List of symbol dicts with name, symbol_type, container_name,
                    signature, docstring, start_line, end_line, is_exported,
                    method_set_signature

        Returns:
            List of created symbol IDs
        """
        cursor = self._get_cursor()
        symbol_ids = []

        for symbol in symbols:
            cursor.execute(
                """
                INSERT INTO symbols
                (file_id, name, symbol_type, container_name, signature,
                 docstring, start_line, end_line, is_exported, method_set_signature)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    file_id,
                    symbol["name"],
                    symbol["symbol_type"],
                    symbol.get("container_name"),
                    symbol.get("signature", ""),
                    symbol.get("docstring"),
                    symbol.get("start_line", 0),
                    symbol.get("end_line", 0),
                    symbol.get("is_exported", True),
                    symbol.get("method_set_signature")
                )
            )
            symbol_ids.append(cursor.lastrowid)

        self.conn.commit()
        return symbol_ids

    def get_symbols_by_file(self, file_id: int) -> list[SymbolRecord]:
        """Get all symbols for a file.

        Args:
            file_id: File ID

        Returns:
            List of SymbolRecord objects
        """
        cursor = self._get_cursor()
        cursor.execute(
            "SELECT * FROM symbols WHERE file_id = ?",
            (file_id,)
        )
        rows = cursor.fetchall()

        return [
            SymbolRecord(
                id=row["id"],
                file_id=row["file_id"],
                name=row["name"],
                symbol_type=row["symbol_type"],
                container_name=row["container_name"],
                signature=row["signature"] or "",
                docstring=row["docstring"],
                start_line=row["start_line"],
                end_line=row["end_line"],
                is_exported=bool(row["is_exported"]),
                method_set_signature=row["method_set_signature"]
            )
            for row in rows
        ]

    def get_symbol_by_name(
        self,
        project_id: int,
        name: str,
        symbol_type: Optional[str] = None
    ) -> list[SymbolRecord]:
        """Get symbols by name within a project.

        Args:
            project_id: Project ID
            name: Symbol name
            symbol_type: Optional symbol type filter

        Returns:
            List of matching SymbolRecord objects
        """
        cursor = self._get_cursor()

        if symbol_type:
            cursor.execute(
                """
                SELECT s.* FROM symbols s
                JOIN files f ON s.file_id = f.id
                WHERE f.project_id = ? AND s.name = ? AND s.symbol_type = ?
                """,
                (project_id, name, symbol_type)
            )
        else:
            cursor.execute(
                """
                SELECT s.* FROM symbols s
                JOIN files f ON s.file_id = f.id
                WHERE f.project_id = ? AND s.name = ?
                """,
                (project_id, name)
            )

        rows = cursor.fetchall()

        return [
            SymbolRecord(
                id=row["id"],
                file_id=row["file_id"],
                name=row["name"],
                symbol_type=row["symbol_type"],
                container_name=row["container_name"],
                signature=row["signature"] or "",
                docstring=row["docstring"],
                start_line=row["start_line"],
                end_line=row["end_line"],
                is_exported=bool(row["is_exported"]),
                method_set_signature=row["method_set_signature"]
            )
            for row in rows
        ]

    def delete_symbols_by_file(self, file_id: int) -> int:
        """Delete all symbols for a file.

        Args:
            file_id: File ID

        Returns:
            Number of deleted symbols
        """
        cursor = self._get_cursor()
        cursor.execute("DELETE FROM symbols WHERE file_id = ?", (file_id,))
        deleted = cursor.rowcount
        self.conn.commit()
        return deleted
