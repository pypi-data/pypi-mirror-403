"""Function call operations mixin for SQLite storage.

This module contains function call-related database operations (both legacy and enhanced).
"""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import sqlite3

from ..base import FunctionRecord, FunctionCallRecord, EnhancedFunctionCallRecord

logger = logging.getLogger(__name__)


class CallOpsMixin:
    """Mixin class for function call-related database operations."""

    conn: "sqlite3.Connection"

    def _get_cursor(self) -> "sqlite3.Cursor":
        """Get a database cursor."""
        return self.conn.cursor()

    # =========================================================================
    # Legacy Function/Call Methods
    # =========================================================================

    def save_functions(
        self,
        file_id: int,
        functions: list[dict]
    ) -> list[int]:
        """Save function records for a file."""
        cursor = self._get_cursor()
        function_ids = []

        for func in functions:
            cursor.execute(
                """
                INSERT INTO functions (file_id, name, signature, start_line, end_line)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    file_id,
                    func["name"],
                    func.get("signature", ""),
                    func.get("start_line", 0),
                    func.get("end_line", 0)
                )
            )
            function_ids.append(cursor.lastrowid)

        self.conn.commit()
        return function_ids

    def get_functions_by_file(self, file_id: int) -> list[FunctionRecord]:
        """Get all functions for a file."""
        cursor = self._get_cursor()
        cursor.execute(
            "SELECT * FROM functions WHERE file_id = ?",
            (file_id,)
        )
        rows = cursor.fetchall()

        return [
            FunctionRecord(
                id=row["id"],
                file_id=row["file_id"],
                name=row["name"],
                signature=row["signature"] or "",
                start_line=row["start_line"],
                end_line=row["end_line"]
            )
            for row in rows
        ]

    def save_function_calls(
        self,
        caller_function_id: int,
        calls: list[dict]
    ) -> list[int]:
        """Save function call records."""
        cursor = self._get_cursor()
        call_ids = []

        for call in calls:
            cursor.execute(
                """
                INSERT INTO function_calls
                (caller_function_id, callee_name, callee_function_id, line)
                VALUES (?, ?, ?, ?)
                """,
                (
                    caller_function_id,
                    call["callee_name"],
                    call.get("callee_function_id"),
                    call.get("line", 0)
                )
            )
            call_ids.append(cursor.lastrowid)

        self.conn.commit()
        return call_ids

    def get_function_calls(
        self,
        function_id: int
    ) -> list[FunctionCallRecord]:
        """Get all function calls made by a function."""
        cursor = self._get_cursor()
        cursor.execute(
            "SELECT * FROM function_calls WHERE caller_function_id = ?",
            (function_id,)
        )
        rows = cursor.fetchall()

        return [
            FunctionCallRecord(
                id=row["id"],
                caller_function_id=row["caller_function_id"],
                callee_name=row["callee_name"],
                callee_function_id=row["callee_function_id"],
                line=row["line"]
            )
            for row in rows
        ]

    # =========================================================================
    # Enhanced Function Calls Methods
    # =========================================================================

    def save_enhanced_function_calls(
        self,
        calls: list[dict]
    ) -> list[int]:
        """Save enhanced function call records.

        Args:
            calls: List of call dicts with source_symbol_id, source_file_id,
                  target_symbol_id, target_symbol_name, call_type, call_context,
                  line_number

        Returns:
            List of created call IDs
        """
        cursor = self._get_cursor()
        call_ids = []

        for call in calls:
            cursor.execute(
                """
                INSERT INTO enhanced_function_calls
                (source_symbol_id, source_file_id, target_symbol_id,
                 target_symbol_name, call_type, call_context, line_number)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    call["source_symbol_id"],
                    call["source_file_id"],
                    call.get("target_symbol_id"),
                    call["target_symbol_name"],
                    call.get("call_type", "direct"),
                    call.get("call_context"),
                    call.get("line_number", 0)
                )
            )
            call_ids.append(cursor.lastrowid)

        self.conn.commit()
        return call_ids

    def get_enhanced_function_calls(
        self,
        symbol_id: int
    ) -> list[EnhancedFunctionCallRecord]:
        """Get all enhanced function calls made by a symbol.

        Args:
            symbol_id: Source symbol ID

        Returns:
            List of EnhancedFunctionCallRecord objects
        """
        cursor = self._get_cursor()
        cursor.execute(
            "SELECT * FROM enhanced_function_calls WHERE source_symbol_id = ?",
            (symbol_id,)
        )
        rows = cursor.fetchall()

        return [
            EnhancedFunctionCallRecord(
                id=row["id"],
                source_symbol_id=row["source_symbol_id"],
                source_file_id=row["source_file_id"],
                target_symbol_id=row["target_symbol_id"],
                target_symbol_name=row["target_symbol_name"],
                call_type=row["call_type"],
                call_context=row["call_context"],
                line_number=row["line_number"]
            )
            for row in rows
        ]

    def delete_enhanced_function_calls_by_file(self, file_id: int) -> int:
        """Delete all enhanced function calls from a file.

        Args:
            file_id: Source file ID

        Returns:
            Number of deleted calls
        """
        cursor = self._get_cursor()
        cursor.execute(
            "DELETE FROM enhanced_function_calls WHERE source_file_id = ?",
            (file_id,)
        )
        deleted = cursor.rowcount
        self.conn.commit()
        return deleted
