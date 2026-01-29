"""Transaction management module for SQLite storage.

This module provides atomic transaction support for file index updates.
"""

import logging
from contextlib import contextmanager
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from . import SQLiteStorage

logger = logging.getLogger(__name__)


class TransactionManager:
    """Transaction manager for atomic file index updates.

    Ensures single file index updates are atomic:
    - Either completely succeed or completely rollback
    - Prevents partial symbol/call data states
    """

    def __init__(self, storage: "SQLiteStorage"):
        """Initialize transaction manager.

        Args:
            storage: SQLiteStorage instance
        """
        self.storage = storage
        self.conn = storage.conn

    @contextmanager
    def transaction(self):
        """Transaction context manager.

        Ensures atomic operations with automatic rollback on failure.

        Yields:
            Database cursor
        """
        cursor = self.conn.cursor()
        try:
            cursor.execute("BEGIN TRANSACTION")
            yield cursor
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Transaction rolled back due to error: {e}")
            raise

    def update_file_index(
        self,
        file_id: int,
        symbols: list[dict],
        function_calls: list[dict]
    ) -> dict[str, int]:
        """Atomically update file index.

        Performs in a single transaction:
        1. Delete old symbols and calls for the file
        2. Insert new symbols
        3. Insert new function calls

        Args:
            file_id: File ID
            symbols: List of symbol dicts
            function_calls: List of function call dicts

        Returns:
            Dict with counts: {"symbols": n, "calls": m}
        """
        symbol_id_map: dict[str, int] = {}  # name -> id

        with self.transaction() as cursor:
            # 1. Delete old data (cascade deletes enhanced_function_calls)
            cursor.execute(
                "DELETE FROM symbols WHERE file_id = ?",
                (file_id,)
            )
            cursor.execute(
                "DELETE FROM enhanced_function_calls WHERE source_file_id = ?",
                (file_id,)
            )

            # 2. Insert new symbols
            for symbol in symbols:
                cursor.execute("""
                    INSERT INTO symbols
                    (file_id, name, symbol_type, container_name, signature,
                     docstring, start_line, end_line, is_exported, method_set_signature)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
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
                ))
                # Map symbol name to ID for call resolution
                key = f"{symbol['name']}:{symbol.get('container_name', '')}"
                symbol_id_map[key] = cursor.lastrowid

            # 3. Insert new function calls
            calls_inserted = 0
            for call in function_calls:
                # Resolve source symbol ID
                source_key = f"{call['source_name']}:{call.get('source_container', '')}"
                source_id = symbol_id_map.get(source_key)

                if source_id:
                    cursor.execute("""
                        INSERT INTO enhanced_function_calls
                        (source_symbol_id, source_file_id, target_symbol_id,
                         target_symbol_name, call_type, call_context, line_number)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        source_id,
                        file_id,
                        call.get("target_symbol_id"),
                        call["target_symbol_name"],
                        call.get("call_type", "direct"),
                        call.get("call_context"),
                        call.get("line_number", 0)
                    ))
                    calls_inserted += 1

        return {
            "symbols": len(symbols),
            "calls": calls_inserted
        }

    def delete_file_cascade(self, file_id: int) -> dict[str, int]:
        """Cascade delete file and all associated data.

        Due to foreign key constraints with ON DELETE CASCADE,
        deleting a file automatically deletes associated:
        - symbols
        - enhanced_function_calls
        - parse_errors
        - imports

        Args:
            file_id: File ID

        Returns:
            Dict with counts of deleted items
        """
        with self.transaction() as cursor:
            # Count items before deletion
            cursor.execute(
                "SELECT COUNT(*) FROM symbols WHERE file_id = ?",
                (file_id,)
            )
            symbols_count = cursor.fetchone()[0]

            cursor.execute(
                "SELECT COUNT(*) FROM enhanced_function_calls WHERE source_file_id = ?",
                (file_id,)
            )
            calls_count = cursor.fetchone()[0]

            cursor.execute(
                "SELECT COUNT(*) FROM parse_errors WHERE file_id = ?",
                (file_id,)
            )
            errors_count = cursor.fetchone()[0]

            # Delete file (cascades to related tables)
            cursor.execute("DELETE FROM files WHERE id = ?", (file_id,))

        return {
            "symbols": symbols_count,
            "calls": calls_count,
            "errors": errors_count
        }
