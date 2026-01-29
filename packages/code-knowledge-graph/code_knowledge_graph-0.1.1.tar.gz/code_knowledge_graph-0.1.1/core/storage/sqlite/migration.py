"""Schema migration module for SQLite storage.

This module handles database schema migrations.
"""

import logging
import sqlite3
from typing import TYPE_CHECKING

from .schema import CURRENT_SCHEMA_VERSION

if TYPE_CHECKING:
    from . import SQLiteStorage

logger = logging.getLogger(__name__)


class SchemaMigrator:
    """Database schema migration handler.

    Handles migration from legacy schema to enhanced schema v2.
    """

    CURRENT_SCHEMA_VERSION = CURRENT_SCHEMA_VERSION

    def __init__(self, storage: "SQLiteStorage"):
        """Initialize schema migration.

        Args:
            storage: SQLiteStorage instance
        """
        self.storage = storage
        self.conn = storage.conn

    def migrate(self) -> bool:
        """Execute schema migration if needed.

        Returns:
            True if migration was performed, False if already up to date
        """
        current_version, _ = self.storage.get_schema_version()

        if current_version >= self.CURRENT_SCHEMA_VERSION:
            logger.info(f"Schema already at version {current_version}, no migration needed")
            return False

        logger.info(f"Migrating schema from version {current_version} to {self.CURRENT_SCHEMA_VERSION}")

        if current_version < 2:
            self._migrate_to_v2()

        from .schema import CURRENT_PARSER_VERSION
        self.storage.set_schema_version(
            self.CURRENT_SCHEMA_VERSION,
            CURRENT_PARSER_VERSION
        )

        logger.info(f"Schema migration completed to version {self.CURRENT_SCHEMA_VERSION}")
        return True

    def _migrate_to_v2(self) -> None:
        """Migrate from v1 to v2 (functions -> symbols)."""
        cursor = self.conn.cursor()

        # Check if functions table has data to migrate
        cursor.execute("SELECT COUNT(*) FROM functions")
        function_count = cursor.fetchone()[0]

        if function_count == 0:
            logger.info("No functions to migrate")
            return

        logger.info(f"Migrating {function_count} functions to symbols table")

        # Migrate functions to symbols
        cursor.execute("""
            INSERT INTO symbols (file_id, name, symbol_type, container_name,
                                signature, docstring, start_line, end_line, is_exported)
            SELECT file_id, name, 'function', NULL, signature, NULL,
                   start_line, end_line, 1
            FROM functions
        """)

        self.conn.commit()
        logger.info(f"Migrated {function_count} functions to symbols table")

        # Rebuild FTS5 index
        self.storage.rebuild_fts5_index()
