"""SQL schema definitions and version constants.

This module contains all SQL schema definitions for the SQLite storage backend.
"""

# Current schema version
CURRENT_SCHEMA_VERSION = 2
CURRENT_PARSER_VERSION = "1.0.0"

# Base schema SQL
SCHEMA_SQL = """
-- Projects table
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    last_scanned TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    file_count INTEGER DEFAULT 0
);

-- Files table
CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    relative_path TEXT NOT NULL,
    file_type TEXT NOT NULL,
    size INTEGER DEFAULT 0,
    depth INTEGER DEFAULT 0,
    modified_time TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    UNIQUE(project_id, relative_path)
);

-- Imports table
CREATE TABLE IF NOT EXISTS imports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER NOT NULL,
    module TEXT NOT NULL,
    import_type TEXT DEFAULT 'static',
    line INTEGER,
    resolved_file_id INTEGER,
    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE,
    FOREIGN KEY (resolved_file_id) REFERENCES files(id) ON DELETE SET NULL
);

-- Functions table (legacy, kept for backward compatibility)
CREATE TABLE IF NOT EXISTS functions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    signature TEXT,
    start_line INTEGER,
    end_line INTEGER,
    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
);

-- Function calls table (legacy, kept for backward compatibility)
CREATE TABLE IF NOT EXISTS function_calls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    caller_function_id INTEGER NOT NULL,
    callee_name TEXT NOT NULL,
    callee_function_id INTEGER,
    line INTEGER,
    FOREIGN KEY (caller_function_id) REFERENCES functions(id) ON DELETE CASCADE,
    FOREIGN KEY (callee_function_id) REFERENCES functions(id) ON DELETE SET NULL
);

-- Code summaries table (LLM-generated)
CREATE TABLE IF NOT EXISTS code_summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER NOT NULL,
    entity_type TEXT NOT NULL,
    entity_name TEXT NOT NULL,
    signature TEXT NOT NULL,
    summary TEXT NOT NULL,
    summary_en TEXT,
    summary_zh TEXT,
    embedding BLOB,
    line_number INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE,
    UNIQUE(file_id, entity_type, entity_name)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_files_project ON files(project_id);
CREATE INDEX IF NOT EXISTS idx_files_type ON files(file_type);
CREATE INDEX IF NOT EXISTS idx_files_depth ON files(depth);
CREATE INDEX IF NOT EXISTS idx_imports_file ON imports(file_id);
CREATE INDEX IF NOT EXISTS idx_imports_resolved ON imports(resolved_file_id);
CREATE INDEX IF NOT EXISTS idx_functions_file ON functions(file_id);
CREATE INDEX IF NOT EXISTS idx_function_calls_caller ON function_calls(caller_function_id);
CREATE INDEX IF NOT EXISTS idx_summaries_file ON code_summaries(file_id);
CREATE INDEX IF NOT EXISTS idx_summaries_entity ON code_summaries(entity_name);
"""

# Enhanced schema for code knowledge graph (v2)
ENHANCED_SCHEMA_SQL = """
-- Unified symbols table (replaces functions table for new features)
CREATE TABLE IF NOT EXISTS symbols (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    symbol_type TEXT NOT NULL,  -- function, class, method, variable, struct, interface
    container_name TEXT,        -- Parent class/struct name
    signature TEXT,             -- Full signature for skeleton mode
    docstring TEXT,
    start_line INTEGER,
    end_line INTEGER,
    is_exported BOOLEAN DEFAULT 1,
    -- Go interface matching: method set signature
    method_set_signature TEXT,
    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
);

-- Symbol search indexes
CREATE INDEX IF NOT EXISTS idx_symbols_name ON symbols(name);
CREATE INDEX IF NOT EXISTS idx_symbols_type ON symbols(symbol_type);
CREATE INDEX IF NOT EXISTS idx_symbols_file ON symbols(file_id);
CREATE INDEX IF NOT EXISTS idx_symbols_container ON symbols(container_name);

-- Enhanced function calls table (references symbols table)
CREATE TABLE IF NOT EXISTS enhanced_function_calls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_symbol_id INTEGER NOT NULL,  -- Calling symbol ID
    source_file_id INTEGER NOT NULL,    -- Calling file ID

    -- Target resolution: prefer ID, fallback to name
    target_symbol_id INTEGER,           -- Called symbol ID (if resolved)
    target_symbol_name TEXT NOT NULL,   -- Called symbol name

    call_type TEXT DEFAULT 'direct',    -- direct, potential(interface), deferred, async
    call_context TEXT,                  -- Call context (e.g., obj type in obj.method())
    line_number INTEGER,

    FOREIGN KEY (source_symbol_id) REFERENCES symbols(id) ON DELETE CASCADE,
    FOREIGN KEY (source_file_id) REFERENCES files(id) ON DELETE CASCADE,
    FOREIGN KEY (target_symbol_id) REFERENCES symbols(id) ON DELETE SET NULL
);

-- Call chain query indexes (optimized for recursive CTE)
CREATE INDEX IF NOT EXISTS idx_enhanced_function_calls_source ON enhanced_function_calls(source_symbol_id);
CREATE INDEX IF NOT EXISTS idx_enhanced_function_calls_target ON enhanced_function_calls(target_symbol_id);
CREATE INDEX IF NOT EXISTS idx_enhanced_function_calls_target_name ON enhanced_function_calls(target_symbol_name);

-- Go modules table
CREATE TABLE IF NOT EXISTS go_modules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    module_path TEXT NOT NULL,  -- Module path from go.mod
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

-- Parse errors table
CREATE TABLE IF NOT EXISTS parse_errors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER NOT NULL,
    error_message TEXT,
    error_line INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
);

-- Schema version table (for triggering full rebuilds)
CREATE TABLE IF NOT EXISTS schema_version (
    id INTEGER PRIMARY KEY,
    version INTEGER NOT NULL,
    parser_version TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

# FTS5 full-text search schema (created separately due to virtual table syntax)
FTS5_SCHEMA_SQL = """
-- FTS5 full-text search virtual table for symbol search
CREATE VIRTUAL TABLE IF NOT EXISTS symbols_fts USING fts5(
    name,
    signature,
    docstring,
    content='symbols',
    content_rowid='id'
);
"""

# FTS5 sync triggers (created separately)
FTS5_TRIGGERS_SQL = """
-- FTS5 sync trigger: INSERT
CREATE TRIGGER IF NOT EXISTS symbols_ai AFTER INSERT ON symbols BEGIN
    INSERT INTO symbols_fts(rowid, name, signature, docstring)
    VALUES (new.id, new.name, new.signature, new.docstring);
END;

-- FTS5 sync trigger: DELETE
CREATE TRIGGER IF NOT EXISTS symbols_ad AFTER DELETE ON symbols BEGIN
    INSERT INTO symbols_fts(symbols_fts, rowid, name, signature, docstring)
    VALUES ('delete', old.id, old.name, old.signature, old.docstring);
END;

-- FTS5 sync trigger: UPDATE
CREATE TRIGGER IF NOT EXISTS symbols_au AFTER UPDATE ON symbols BEGIN
    INSERT INTO symbols_fts(symbols_fts, rowid, name, signature, docstring)
    VALUES ('delete', old.id, old.name, old.signature, old.docstring);
    INSERT INTO symbols_fts(rowid, name, signature, docstring)
    VALUES (new.id, new.name, new.signature, new.docstring);
END;
"""
