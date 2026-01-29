"""SQLite storage backend implementation.

This module implements the StorageBackend interface using SQLite database.

The storage is organized into mixins for maintainability:
- ProjectOpsMixin: Project CRUD operations
- FileOpsMixin: File operations
- StatsOpsMixin: Statistics queries
- SymbolOpsMixin: Symbol table operations
- CallOpsMixin: Function call operations (legacy + enhanced)
- SummaryOpsMixin: Code summary and embedding operations
- GoOpsMixin: Go module operations
- ErrorOpsMixin: Parse error operations
"""

import logging
import sqlite3
from typing import Optional

from ..base import StorageBackend

from .schema import (
    SCHEMA_SQL,
    ENHANCED_SCHEMA_SQL,
    FTS5_SCHEMA_SQL,
    FTS5_TRIGGERS_SQL,
    CURRENT_SCHEMA_VERSION,
    CURRENT_PARSER_VERSION,
)
from .project_ops import ProjectOpsMixin
from .file_ops import FileOpsMixin
from .stats_ops import StatsOpsMixin
from .symbol_ops import SymbolOpsMixin
from .call_ops import CallOpsMixin
from .summary_ops import SummaryOpsMixin
from .go_ops import GoOpsMixin
from .error_ops import ErrorOpsMixin

logger = logging.getLogger(__name__)


class SQLiteStorage(
    ProjectOpsMixin,
    FileOpsMixin,
    StatsOpsMixin,
    SymbolOpsMixin,
    CallOpsMixin,
    SummaryOpsMixin,
    GoOpsMixin,
    ErrorOpsMixin,
    StorageBackend
):
    """SQLite storage backend implementation.

    Uses mixin classes to organize functionality:
    - ProjectOpsMixin: save_project, get_project, list_projects, delete_project
    - FileOpsMixin: get_files_by_project, get_file_by_path, get_imports_by_file
    - StatsOpsMixin: get_file_stats, get_reference_ranking, get_depth_stats
    - SymbolOpsMixin: save_symbols, get_symbols_by_file, get_symbol_by_name
    - CallOpsMixin: save_functions, get_function_calls, save_enhanced_function_calls
    - SummaryOpsMixin: save_summaries, get_summary, search_by_embedding
    - GoOpsMixin: save_go_module, get_go_module
    - ErrorOpsMixin: save_parse_error, get_parse_errors, clear_parse_errors
    """

    # Schema constants
    SCHEMA_SQL = SCHEMA_SQL
    ENHANCED_SCHEMA_SQL = ENHANCED_SCHEMA_SQL
    FTS5_SCHEMA_SQL = FTS5_SCHEMA_SQL
    FTS5_TRIGGERS_SQL = FTS5_TRIGGERS_SQL
    CURRENT_SCHEMA_VERSION = CURRENT_SCHEMA_VERSION
    CURRENT_PARSER_VERSION = CURRENT_PARSER_VERSION

    def __init__(self, db_path: str = "code_knowledge.db"):
        """Initialize SQLite storage.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._init_schema()

    def _init_schema(self) -> None:
        """Initialize database schema."""
        cursor = self.conn.cursor()
        cursor.executescript(self.SCHEMA_SQL)
        self.conn.commit()

        # Initialize enhanced schema
        self._init_enhanced_schema()

        # Run legacy migrations
        self._migrate_schema()

    def _init_enhanced_schema(self) -> None:
        """Initialize enhanced schema for code knowledge graph v2."""
        cursor = self.conn.cursor()

        # Create enhanced tables
        cursor.executescript(self.ENHANCED_SCHEMA_SQL)
        self.conn.commit()

        # Add package_name column to files table if not exists
        cursor.execute("PRAGMA table_info(files)")
        columns = {col[1] for col in cursor.fetchall()}
        if "package_name" not in columns:
            try:
                cursor.execute("ALTER TABLE files ADD COLUMN package_name TEXT")
                logger.info("Added package_name column to files table")
            except sqlite3.Error as e:
                logger.warning(f"Failed to add package_name column: {e}")

        # Create FTS5 virtual table (separate due to syntax)
        try:
            cursor.executescript(self.FTS5_SCHEMA_SQL)
            self.conn.commit()
        except sqlite3.Error as e:
            logger.warning(f"FTS5 table creation failed (may already exist): {e}")

        # Create FTS5 triggers
        try:
            cursor.executescript(self.FTS5_TRIGGERS_SQL)
            self.conn.commit()
        except sqlite3.Error as e:
            logger.warning(f"FTS5 triggers creation failed (may already exist): {e}")

        # Initialize schema version if not exists
        cursor.execute("SELECT COUNT(*) FROM schema_version")
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                """
                INSERT INTO schema_version (id, version, parser_version)
                VALUES (1, ?, ?)
                """,
                (self.CURRENT_SCHEMA_VERSION, self.CURRENT_PARSER_VERSION)
            )
            self.conn.commit()
            logger.info(f"Initialized schema version to {self.CURRENT_SCHEMA_VERSION}")

    def _migrate_schema(self) -> None:
        """Apply schema migrations for compatibility."""
        cursor = self._get_cursor()

        # Check if code_summaries table needs migration
        cursor.execute("PRAGMA table_info(code_summaries)")
        columns = {col[1] for col in cursor.fetchall()}

        # Add new columns if they don't exist
        migrations = [
            ("summary_en", "ALTER TABLE code_summaries ADD COLUMN summary_en TEXT"),
            ("summary_zh", "ALTER TABLE code_summaries ADD COLUMN summary_zh TEXT"),
            ("embedding", "ALTER TABLE code_summaries ADD COLUMN embedding BLOB"),
        ]

        for col_name, migration_sql in migrations:
            if col_name not in columns:
                try:
                    cursor.execute(migration_sql)
                    logger.info(f"Migrated code_summaries: added {col_name} column")
                except sqlite3.Error as e:
                    logger.warning(f"Migration failed for {col_name}: {e}")

        self.conn.commit()

    def _get_cursor(self) -> sqlite3.Cursor:
        """Get a database cursor."""
        return self.conn.cursor()

    # =========================================================================
    # Schema Version Methods
    # =========================================================================

    def get_schema_version(self) -> tuple[int, str]:
        """Get current schema version.

        Returns:
            Tuple of (version_number, parser_version)
        """
        cursor = self._get_cursor()
        cursor.execute("SELECT version, parser_version FROM schema_version WHERE id = 1")
        row = cursor.fetchone()
        if row:
            return (row["version"], row["parser_version"] or "")
        return (0, "")

    def set_schema_version(self, version: int, parser_version: str) -> None:
        """Set schema version.

        Args:
            version: Schema version number
            parser_version: Parser version string
        """
        cursor = self._get_cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO schema_version (id, version, parser_version, updated_at)
            VALUES (1, ?, ?, CURRENT_TIMESTAMP)
            """,
            (version, parser_version)
        )
        self.conn.commit()

    def needs_full_rebuild(self) -> bool:
        """Check if full index rebuild is needed.

        Returns:
            True if schema or parser version has changed
        """
        current_version, current_parser = self.get_schema_version()
        return (
            current_version < self.CURRENT_SCHEMA_VERSION or
            current_parser != self.CURRENT_PARSER_VERSION
        )

    # =========================================================================
    # FTS5 Search Methods
    # =========================================================================

    def rebuild_fts5_index(self) -> None:
        """Rebuild the FTS5 full-text search index."""
        cursor = self._get_cursor()
        try:
            cursor.execute("INSERT INTO symbols_fts(symbols_fts) VALUES('rebuild')")
            self.conn.commit()
            logger.info("FTS5 index rebuilt successfully")
        except sqlite3.Error as e:
            logger.error(f"Failed to rebuild FTS5 index: {e}")

    def close(self) -> None:
        """Close the storage connection."""
        if self.conn:
            self.conn.close()
            self.conn = None


# Re-export for backward compatibility
from .migration import SchemaMigrator as SchemaMigration
from .transaction import TransactionManager

__all__ = [
    "SQLiteStorage",
    "SchemaMigration",
    "TransactionManager",
    # Schema constants
    "SCHEMA_SQL",
    "ENHANCED_SCHEMA_SQL",
    "FTS5_SCHEMA_SQL",
    "FTS5_TRIGGERS_SQL",
    "CURRENT_SCHEMA_VERSION",
    "CURRENT_PARSER_VERSION",
]
