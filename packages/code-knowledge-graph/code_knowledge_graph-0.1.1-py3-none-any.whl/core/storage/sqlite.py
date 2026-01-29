"""SQLite storage backend implementation.

This module re-exports from the refactored sqlite package for backward compatibility.

The actual implementation is now in core/storage/sqlite/ directory:
- __init__.py: Main SQLiteStorage class (combines all mixins)
- schema.py: SQL schema definitions
- project_ops.py: Project operations mixin
- file_ops.py: File operations mixin
- stats_ops.py: Statistics operations mixin
- symbol_ops.py: Symbol operations mixin
- call_ops.py: Function call operations mixin
- summary_ops.py: Code summary operations mixin
- go_ops.py: Go module operations mixin
- error_ops.py: Parse error operations mixin
- migration.py: Schema migration handler
- transaction.py: Transaction manager
"""

# Re-export everything from the new package
from .sqlite import (
    SQLiteStorage,
    SchemaMigration,
    TransactionManager,
    SCHEMA_SQL,
    ENHANCED_SCHEMA_SQL,
    FTS5_SCHEMA_SQL,
    FTS5_TRIGGERS_SQL,
    CURRENT_SCHEMA_VERSION,
    CURRENT_PARSER_VERSION,
)

__all__ = [
    "SQLiteStorage",
    "SchemaMigration",
    "TransactionManager",
    "SCHEMA_SQL",
    "ENHANCED_SCHEMA_SQL",
    "FTS5_SCHEMA_SQL",
    "FTS5_TRIGGERS_SQL",
    "CURRENT_SCHEMA_VERSION",
    "CURRENT_PARSER_VERSION",
]
