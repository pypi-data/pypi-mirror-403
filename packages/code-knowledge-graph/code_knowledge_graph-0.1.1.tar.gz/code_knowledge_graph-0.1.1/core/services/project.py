"""Project management service.

This module provides high-level operations for scanning,
storing, and managing code projects with enhanced symbol
and call relationship storage.

Feature: code-knowledge-graph-enhancement
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from ..scanner import CodeScanner
from ..graph import GraphBuilder
from ..storage import StorageBackend
from ..storage.sqlite import SQLiteStorage, TransactionManager
from ..parsers import PythonParser, JsParser, GoParser

logger = logging.getLogger(__name__)


@dataclass
class ScanResult:
    """Result of a project scan operation."""

    project_id: int
    project_path: str
    project_name: str
    total_files: int
    file_types: dict[str, int]
    external_deps: list[str]
    scan_mode: str  # 'full' or 'incremental'
    stats: Optional[dict] = None  # For incremental updates
    symbol_stats: Optional[dict] = None  # Symbol extraction stats
    parse_errors: list[dict] = field(default_factory=list)  # Parse errors


@dataclass
class GoPackageInfo:
    """Information about a Go package."""
    package_name: str
    module_path: Optional[str]
    files: list[str]  # Files in this package


class ProjectService:
    """Project management service.

    Provides high-level methods for scanning projects,
    managing storage, and querying project data.
    Integrates enhanced symbol storage and call relationship tracking.
    """


    # Current parser version - increment when parser logic changes
    PARSER_VERSION = "1.0.0"

    def __init__(self, storage: StorageBackend):
        """Initialize project service.

        Args:
            storage: Storage backend instance
        """
        self.storage = storage
        self._parsers = {
            "python": PythonParser(),
            "javascript": JsParser(),
            "typescript": JsParser(),
            "go": GoParser(),
        }
        # Transaction manager for atomic updates
        if isinstance(storage, SQLiteStorage):
            self._transaction_manager = TransactionManager(storage)
        else:
            self._transaction_manager = None

    def scan_project(
        self,
        project_path: str | Path,
        incremental: bool = True
    ) -> ScanResult:
        """Scan a project and store the results.

        Performs enhanced scanning with symbol extraction and call
        relationship tracking. Supports incremental updates based on
        file modification time and schema version.

        Args:
            project_path: Path to the project directory
            incremental: If True, only update modified files

        Returns:
            ScanResult with scan statistics
        """
        path = Path(project_path).resolve()

        if not path.exists():
            raise FileNotFoundError(f"Project path does not exist: {path}")

        if not path.is_dir():
            raise ValueError(f"Project path is not a directory: {path}")

        logger.info(f"Scanning project: {path}")

        # Check if full rebuild is needed due to schema/parser version change
        if isinstance(self.storage, SQLiteStorage):
            if self.storage.needs_full_rebuild():
                logger.info("Schema or parser version changed, forcing full rebuild")
                incremental = False
                # Update schema version
                self.storage.set_schema_version(
                    SQLiteStorage.CURRENT_SCHEMA_VERSION,
                    self.PARSER_VERSION
                )

        # Scan files
        scanner = CodeScanner(path)
        files = scanner.scan()

        # Build dependency graph
        builder = GraphBuilder(path)
        graph = builder.build(files)
        graph_dict = graph.to_dict()

        # Count file types
        file_types: dict[str, int] = {}
        for file_info in files:
            ft = file_info.file_type
            file_types[ft] = file_types.get(ft, 0) + 1

        # Save to storage (basic file info)
        if incremental:
            project_id, stats = self.storage.save_project_incremental(
                path, files, graph_dict
            )
            scan_mode = "incremental"
        else:
            project_id = self.storage.save_project(path, files, graph_dict)
            stats = {"added": len(files), "updated": 0, "unchanged": 0, "removed": 0}
            scan_mode = "full"

        # Extract and store enhanced symbols and call relationships
        symbol_stats, parse_errors = self._extract_and_store_symbols(
            project_id, path, files, incremental, stats
        )

        # Handle Go project special processing
        if "go" in file_types:
            self._process_go_project(project_id, path, files)

        return ScanResult(
            project_id=project_id,
            project_path=str(path),
            project_name=path.name,
            total_files=len(files),
            file_types=file_types,
            external_deps=list(graph.external_deps),
            scan_mode=scan_mode,
            stats=stats,
            symbol_stats=symbol_stats,
            parse_errors=parse_errors
        )

    def _extract_and_store_symbols(
        self,
        project_id: int,
        project_path: Path,
        files: list,
        incremental: bool,
        stats: dict
    ) -> tuple[dict, list[dict]]:
        """Extract symbols and call relationships from files.

        Uses enhanced parsers to extract symbols (functions, classes, methods,
        structs, interfaces) and function call relationships.

        Args:
            project_id: Project ID
            project_path: Project root path
            files: List of FileInfo objects
            incremental: Whether this is an incremental update
            stats: Update stats from basic scan

        Returns:
            Tuple of (symbol_stats, parse_errors)
        """
        symbol_stats = {
            "total_symbols": 0,
            "total_calls": 0,
            "files_processed": 0,
            "files_skipped": 0,
        }
        parse_errors: list[dict] = []

        # Determine which files need symbol extraction
        if incremental:
            # Use modification time based filtering
            files_to_process = self._get_files_needing_symbol_update(
                project_id, project_path, files
            )
            symbol_stats["files_skipped"] = len(files) - len(files_to_process)
        else:
            files_to_process = files

        for file_info in files_to_process:
            try:
                result = self._process_file_symbols(
                    project_id, project_path, file_info
                )
                if result:
                    symbol_stats["total_symbols"] += result.get("symbols", 0)
                    symbol_stats["total_calls"] += result.get("calls", 0)
                    symbol_stats["files_processed"] += 1
                else:
                    symbol_stats["files_skipped"] += 1
            except Exception as e:
                logger.warning(f"Failed to process symbols for {file_info.relative_path}: {e}")
                parse_errors.append({
                    "file": file_info.relative_path,
                    "error": str(e)
                })
                # Record parse error in storage
                self._record_parse_error(project_id, file_info.relative_path, str(e))

        logger.info(
            f"Symbol extraction: {symbol_stats['files_processed']} files processed, "
            f"{symbol_stats['files_skipped']} skipped, "
            f"{symbol_stats['total_symbols']} symbols, {symbol_stats['total_calls']} calls"
        )

        # Resolve target_symbol_id for function calls
        if isinstance(self.storage, SQLiteStorage):
            resolved_count = self._resolve_target_symbol_ids(project_id)
            logger.info(f"Resolved {resolved_count} target symbol IDs")

        return symbol_stats, parse_errors

    def _resolve_target_symbol_ids(self, project_id: int) -> int:
        """Resolve target_symbol_id for enhanced function calls.

        Matches target_symbol_name to actual symbol IDs in the same project.
        This enables proper call chain tracing with file/line information.

        Args:
            project_id: Project ID

        Returns:
            Number of resolved target symbol IDs
        """
        cursor = self.storage._get_cursor()

        # Update target_symbol_id where we can match by name
        # For methods, we try to match both container.method and just method
        cursor.execute("""
            UPDATE enhanced_function_calls
            SET target_symbol_id = (
                SELECT s.id FROM symbols s
                JOIN files f ON s.file_id = f.id
                WHERE f.project_id = :project_id
                  AND (
                      -- Exact name match for functions
                      (s.name = enhanced_function_calls.target_symbol_name
                       AND s.symbol_type IN ('function', 'method'))
                      -- Or match method name when container matches call_context
                      OR (s.name = enhanced_function_calls.target_symbol_name
                          AND s.container_name = enhanced_function_calls.call_context
                          AND s.symbol_type = 'method')
                  )
                LIMIT 1
            )
            WHERE source_file_id IN (
                SELECT id FROM files WHERE project_id = :project_id
            )
            AND target_symbol_id IS NULL
        """, {"project_id": project_id})

        resolved_count = cursor.rowcount
        self.storage.conn.commit()
        return resolved_count

    def _get_modified_files(self, stats: dict) -> set[str]:
        """Get set of modified file paths from stats.

        Args:
            stats: Stats dict from incremental scan

        Returns:
            Set of relative file paths that were added or updated
        """
        # The stats dict contains counts, not file lists
        # Return empty set to process all files - the actual filtering
        # is done in _extract_and_store_symbols based on file modification time
        return set()

    def _get_files_needing_symbol_update(
        self,
        project_id: int,
        project_path: Path,
        files: list
    ) -> list:
        """Get files that need symbol extraction based on modification time.

        Compares file modification times with stored symbol data to determine
        which files need re-processing.

        Args:
            project_id: Project ID
            project_path: Project root path
            files: List of FileInfo objects

        Returns:
            List of FileInfo objects that need symbol extraction
        """
        if not isinstance(self.storage, SQLiteStorage):
            return files

        cursor = self.storage._get_cursor()
        files_to_update = []

        for file_info in files:
            # Check if file has symbols
            file_record = self.storage.get_file_by_path(
                project_id, file_info.relative_path
            )
            if not file_record:
                files_to_update.append(file_info)
                continue

            # Check if file has any symbols
            cursor.execute(
                "SELECT COUNT(*) FROM symbols WHERE file_id = ?",
                (file_record.id,)
            )
            symbol_count = cursor.fetchone()[0]

            if symbol_count == 0:
                # No symbols yet, needs processing
                files_to_update.append(file_info)
                continue

            # Check modification time
            try:
                full_path = project_path / file_info.relative_path
                current_mtime = full_path.stat().st_mtime

                stored_mtime = file_record.modified_time
                if isinstance(stored_mtime, str):
                    from datetime import datetime
                    stored_mtime = datetime.fromisoformat(stored_mtime)

                if hasattr(stored_mtime, 'timestamp'):
                    stored_timestamp = stored_mtime.timestamp()
                else:
                    stored_timestamp = 0

                # If file is newer than stored time, needs update
                if current_mtime > stored_timestamp + 1:  # 1 second tolerance
                    files_to_update.append(file_info)

            except (OSError, FileNotFoundError):
                # Can't check modification time, include for safety
                files_to_update.append(file_info)

        return files_to_update

    def _process_file_symbols(
        self,
        project_id: int,
        project_path: Path,
        file_info
    ) -> Optional[dict]:
        """Process a single file to extract symbols and calls.

        Args:
            project_id: Project ID
            project_path: Project root path
            file_info: FileInfo object

        Returns:
            Dict with counts or None if file type not supported
        """
        file_type = file_info.file_type
        parser = self._parsers.get(file_type)

        if not parser:
            return None

        # Get file ID
        file_record = self.storage.get_file_by_path(
            project_id, file_info.relative_path
        )
        if not file_record:
            logger.warning(f"File not found in storage: {file_info.relative_path}")
            return None

        file_id = file_record.id

        # Read file content
        try:
            full_path = project_path / file_info.relative_path
            content = full_path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            logger.warning(f"Failed to read file {file_info.relative_path}: {e}")
            return None

        # Parse file using enhanced parser
        try:
            if hasattr(parser, 'parse_enhanced'):
                parse_result = parser.parse_enhanced(content, full_path)
            else:
                parse_result = parser.parse_full(content, full_path)
        except Exception as e:
            logger.warning(f"Parse error for {file_info.relative_path}: {e}")
            self._record_parse_error(project_id, file_info.relative_path, str(e))
            return None

        # Convert parse result to symbols and calls
        symbols, calls = self._convert_parse_result(parse_result, file_type)

        # Store using transaction manager for atomicity
        if self._transaction_manager:
            result = self._transaction_manager.update_file_index(
                file_id, symbols, calls
            )
            return result
        else:
            # Fallback to direct storage
            symbol_ids = self.storage.save_symbols(file_id, symbols)
            # Save calls with source symbol mapping
            call_records = self._prepare_call_records(
                file_id, symbols, calls, symbol_ids
            )
            if call_records:
                self.storage.save_enhanced_function_calls(call_records)
            return {"symbols": len(symbols), "calls": len(call_records)}

    def _convert_parse_result(self, parse_result, file_type: str) -> tuple[list[dict], list[dict]]:
        """Convert parser result to symbol and call dicts.

        Args:
            parse_result: ParseResult or EnhancedParseResult from parser
            file_type: File type (python, javascript, go, etc.)

        Returns:
            Tuple of (symbols_list, calls_list)
        """
        symbols = []
        calls = []

        # Handle enhanced parse result (Go)
        if hasattr(parse_result, 'structs'):
            # Process structs
            for struct in parse_result.structs:
                symbols.append({
                    "name": struct.name,
                    "symbol_type": "struct",
                    "container_name": None,
                    "signature": f"type {struct.name} struct",
                    "docstring": struct.docstring,
                    "start_line": struct.start_line,
                    "end_line": struct.end_line,
                    "is_exported": struct.name[0].isupper() if struct.name else True,
                })

        if hasattr(parse_result, 'interfaces'):
            # Process interfaces
            for interface in parse_result.interfaces:
                symbols.append({
                    "name": interface.name,
                    "symbol_type": "interface",
                    "container_name": None,
                    "signature": f"type {interface.name} interface",
                    "docstring": interface.docstring,
                    "start_line": interface.start_line,
                    "end_line": interface.end_line,
                    "is_exported": interface.name[0].isupper() if interface.name else True,
                })
                # Add interface methods
                for method in interface.methods:
                    symbols.append({
                        "name": method.name,
                        "symbol_type": "method",
                        "container_name": interface.name,
                        "signature": method.signature,
                        "docstring": None,
                        "start_line": method.line,
                        "end_line": method.line,
                        "is_exported": method.name[0].isupper() if method.name else True,
                    })

        # Process functions
        for func in parse_result.functions:
            # Determine symbol type and container
            symbol_type = "function"
            container_name = None

            if hasattr(func, 'is_method') and func.is_method:
                symbol_type = "method"
                # For Go methods, extract receiver type as container
                if hasattr(func, 'receiver_type') and func.receiver_type:
                    container_name = func.receiver_type.lstrip('*')

            # Determine if exported (Go)
            is_exported = True
            if file_type == "go" and func.name:
                is_exported = func.name[0].isupper()

            symbols.append({
                "name": func.name,
                "symbol_type": symbol_type,
                "container_name": container_name,
                "signature": func.signature,
                "docstring": getattr(func, 'docstring', None),
                "start_line": func.start_line,
                "end_line": func.end_line,
                "is_exported": is_exported,
            })

            # Process function calls
            for call_name in func.calls:
                call_type = "direct"
                actual_name = call_name

                # Handle Go defer/go prefixes
                if call_name.startswith("defer:"):
                    call_type = "deferred"
                    actual_name = call_name[6:]
                elif call_name.startswith("go:"):
                    call_type = "async"
                    actual_name = call_name[3:]

                calls.append({
                    "source_name": func.name,
                    "source_container": container_name,
                    "target_symbol_name": actual_name,
                    "call_type": call_type,
                    "line_number": func.start_line,  # Approximate
                })

        # Process classes (Python/JS)
        if hasattr(parse_result, 'classes'):
            for cls in parse_result.classes:
                symbols.append({
                    "name": cls.name,
                    "symbol_type": "class",
                    "container_name": None,
                    "signature": cls.signature if hasattr(cls, 'signature') else f"class {cls.name}",
                    "docstring": getattr(cls, 'docstring', None),
                    "start_line": cls.start_line,
                    "end_line": cls.end_line,
                    "is_exported": True,
                })
                # Add class methods
                if hasattr(cls, 'methods'):
                    for method in cls.methods:
                        symbols.append({
                            "name": method.name,
                            "symbol_type": "method",
                            "container_name": cls.name,
                            "signature": method.signature,
                            "docstring": getattr(method, 'docstring', None),
                            "start_line": method.start_line,
                            "end_line": method.end_line,
                            "is_exported": True,
                        })

        # Process global variables
        if hasattr(parse_result, 'global_variables'):
            for var in parse_result.global_variables:
                is_exported = True
                if file_type == "go" and var.name:
                    is_exported = var.name[0].isupper()

                symbols.append({
                    "name": var.name,
                    "symbol_type": "variable",
                    "container_name": None,
                    "signature": f"{var.name}: {var.type_annotation}" if var.type_annotation else var.name,
                    "docstring": None,
                    "start_line": var.line,
                    "end_line": var.line,
                    "is_exported": is_exported,
                })

        return symbols, calls

    def _prepare_call_records(
        self,
        file_id: int,
        symbols: list[dict],
        calls: list[dict],
        symbol_ids: list[int]
    ) -> list[dict]:
        """Prepare call records with source symbol IDs.

        Args:
            file_id: File ID
            symbols: List of symbol dicts
            calls: List of call dicts
            symbol_ids: List of created symbol IDs

        Returns:
            List of call records ready for storage
        """
        # Build name to ID mapping
        name_to_id = {}
        for i, symbol in enumerate(symbols):
            key = f"{symbol['name']}:{symbol.get('container_name', '')}"
            if i < len(symbol_ids):
                name_to_id[key] = symbol_ids[i]

        call_records = []
        for call in calls:
            source_key = f"{call['source_name']}:{call.get('source_container', '')}"
            source_id = name_to_id.get(source_key)

            if source_id:
                call_records.append({
                    "source_symbol_id": source_id,
                    "source_file_id": file_id,
                    "target_symbol_id": None,  # Will be resolved later
                    "target_symbol_name": call["target_symbol_name"],
                    "call_type": call.get("call_type", "direct"),
                    "call_context": call.get("call_context"),
                    "line_number": call.get("line_number", 0),
                })

        return call_records

    def _record_parse_error(
        self,
        project_id: int,
        file_path: str,
        error_message: str
    ) -> None:
        """Record a parse error in storage.

        Args:
            project_id: Project ID
            file_path: Relative file path
            error_message: Error message
        """
        if not isinstance(self.storage, SQLiteStorage):
            return

        file_record = self.storage.get_file_by_path(project_id, file_path)
        if file_record:
            self.storage.save_parse_error(file_record.id, error_message)

    def _process_go_project(
        self,
        project_id: int,
        project_path: Path,
        files: list
    ) -> None:
        """Process Go project special handling.

        - Parse go.mod to get module path
        - Handle cross-file symbols in same package
        - Calculate struct method set fingerprints

        Args:
            project_id: Project ID
            project_path: Project root path
            files: List of FileInfo objects
        """
        # Parse go.mod if exists
        go_mod_path = project_path / "go.mod"
        if go_mod_path.exists():
            try:
                content = go_mod_path.read_text(encoding="utf-8")
                go_parser = self._parsers.get("go")
                if go_parser and hasattr(go_parser, 'parse_go_mod'):
                    module_path = go_parser.parse_go_mod(content)
                    if module_path:
                        self.storage.save_go_module(project_id, module_path)
                        logger.info(f"Saved Go module path: {module_path}")
            except Exception as e:
                logger.warning(f"Failed to parse go.mod: {e}")

        # Group Go files by package
        go_packages = self._group_go_files_by_package(project_id, project_path, files)

        # Update package names in files table
        self._update_go_package_names(project_id, go_packages)

        # Calculate struct method set fingerprints
        self._update_struct_method_fingerprints(project_id)

    def _group_go_files_by_package(
        self,
        project_id: int,
        project_path: Path,
        files: list
    ) -> dict[str, GoPackageInfo]:
        """Group Go files by their package name.

        Args:
            project_id: Project ID
            project_path: Project root path
            files: List of FileInfo objects

        Returns:
            Dict mapping directory path to GoPackageInfo
        """
        packages: dict[str, GoPackageInfo] = {}
        go_parser = self._parsers.get("go")

        for file_info in files:
            if file_info.file_type != "go":
                continue

            # Get directory path
            dir_path = str(Path(file_info.relative_path).parent)

            # Parse file to get package name
            try:
                full_path = project_path / file_info.relative_path
                content = full_path.read_text(encoding="utf-8", errors="ignore")

                if go_parser and hasattr(go_parser, 'parse_enhanced'):
                    result = go_parser.parse_enhanced(content, full_path)
                    package_name = result.package_name
                else:
                    package_name = None

                if dir_path not in packages:
                    packages[dir_path] = GoPackageInfo(
                        package_name=package_name or "main",
                        module_path=None,
                        files=[]
                    )
                packages[dir_path].files.append(file_info.relative_path)

                # Update package name if found
                if package_name:
                    packages[dir_path].package_name = package_name

            except Exception as e:
                logger.debug(f"Failed to get package name for {file_info.relative_path}: {e}")

        return packages

    def _update_go_package_names(
        self,
        project_id: int,
        packages: dict[str, GoPackageInfo]
    ) -> None:
        """Update package_name column in files table for Go files.

        Args:
            project_id: Project ID
            packages: Dict mapping directory to GoPackageInfo
        """
        if not isinstance(self.storage, SQLiteStorage):
            return

        cursor = self.storage._get_cursor()

        for dir_path, pkg_info in packages.items():
            for file_path in pkg_info.files:
                try:
                    cursor.execute(
                        """
                        UPDATE files SET package_name = ?
                        WHERE project_id = ? AND relative_path = ?
                        """,
                        (pkg_info.package_name, project_id, file_path)
                    )
                except Exception as e:
                    logger.debug(f"Failed to update package name for {file_path}: {e}")

        self.storage.conn.commit()

    def _update_struct_method_fingerprints(self, project_id: int) -> None:
        """Calculate and update method set fingerprints for all structs.

        This enables Go interface implementation detection.

        Args:
            project_id: Project ID
        """
        if not isinstance(self.storage, SQLiteStorage):
            return

        # Import GoInterfaceResolver for fingerprint calculation
        try:
            from .go_interface import GoInterfaceResolver
            resolver = GoInterfaceResolver(self.storage)
        except ImportError:
            logger.warning("GoInterfaceResolver not available")
            return

        # Get all structs in the project
        cursor = self.storage._get_cursor()
        cursor.execute(
            """
            SELECT DISTINCT s.name
            FROM symbols s
            JOIN files f ON s.file_id = f.id
            WHERE f.project_id = ? AND s.symbol_type = 'struct'
            """,
            (project_id,)
        )

        struct_names = [row[0] for row in cursor.fetchall()]

        for struct_name in struct_names:
            try:
                resolver.update_struct_method_fingerprint(project_id, struct_name)
            except Exception as e:
                logger.debug(f"Failed to update fingerprint for struct {struct_name}: {e}")

    def rescan_project(
        self,
        project_path: str | Path
    ) -> ScanResult:
        """Force a full rescan of a project.

        Args:
            project_path: Path to the project directory

        Returns:
            ScanResult with scan statistics
        """
        return self.scan_project(project_path, incremental=False)

    def update_single_file(
        self,
        project_path: str | Path,
        file_path: str
    ) -> Optional[dict]:
        """Update index for a single file.

        Useful for real-time updates when a file is saved.

        Args:
            project_path: Path to the project directory
            file_path: Relative path to the file

        Returns:
            Dict with update stats or None if failed
        """
        path = Path(project_path).resolve()
        full_path = path / file_path

        if not full_path.exists():
            logger.warning(f"File not found: {full_path}")
            return None

        # Get project
        project = self.storage.get_project(str(path))
        if not project:
            logger.warning(f"Project not found: {path}")
            return None

        # Get file record
        file_record = self.storage.get_file_by_path(project.id, file_path)
        if not file_record:
            logger.warning(f"File not in index: {file_path}")
            return None

        # Determine file type
        suffix = full_path.suffix.lower()
        file_type_map = {
            ".py": "python",
            ".js": "javascript",
            ".jsx": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".go": "go",
        }
        file_type = file_type_map.get(suffix)

        if not file_type:
            return None

        parser = self._parsers.get(file_type)
        if not parser:
            return None

        # Read and parse file
        try:
            content = full_path.read_text(encoding="utf-8", errors="ignore")

            if hasattr(parser, 'parse_enhanced'):
                parse_result = parser.parse_enhanced(content, full_path)
            else:
                parse_result = parser.parse_full(content, full_path)

            symbols, calls = self._convert_parse_result(parse_result, file_type)

            # Update using transaction manager
            if self._transaction_manager:
                result = self._transaction_manager.update_file_index(
                    file_record.id, symbols, calls
                )
                logger.info(f"Updated {file_path}: {result['symbols']} symbols, {result['calls']} calls")
                return result
            else:
                # Fallback
                self.storage.delete_symbols_by_file(file_record.id)
                symbol_ids = self.storage.save_symbols(file_record.id, symbols)
                call_records = self._prepare_call_records(
                    file_record.id, symbols, calls, symbol_ids
                )
                if call_records:
                    self.storage.save_enhanced_function_calls(call_records)
                return {"symbols": len(symbols), "calls": len(call_records)}

        except Exception as e:
            logger.error(f"Failed to update {file_path}: {e}")
            self._record_parse_error(project.id, file_path, str(e))
            return None

    def get_project_info(
        self,
        project_path: str
    ) -> Optional[dict]:
        """Get basic information about a stored project.

        Args:
            project_path: Path to the project

        Returns:
            Dictionary with project info or None if not found
        """
        project = self.storage.get_project(project_path)
        if not project:
            return None

        return {
            "id": project.id,
            "path": project.path,
            "name": project.name,
            "last_scanned": project.last_scanned.isoformat()
                if hasattr(project.last_scanned, 'isoformat')
                else str(project.last_scanned),
            "file_count": project.file_count
        }

    def list_projects(self) -> list[dict]:
        """List all stored projects.

        Returns:
            List of project info dictionaries
        """
        if hasattr(self.storage, 'list_projects'):
            projects = self.storage.list_projects()
            return [
                {
                    "id": p.id,
                    "path": p.path,
                    "name": p.name,
                    "last_scanned": p.last_scanned.isoformat()
                        if hasattr(p.last_scanned, 'isoformat')
                        else str(p.last_scanned),
                    "file_count": p.file_count
                }
                for p in projects
            ]
        return []

    def delete_project(
        self,
        project_path: str
    ) -> bool:
        """Delete a project from storage.

        Args:
            project_path: Path to the project

        Returns:
            True if deleted, False if not found
        """
        project = self.storage.get_project(project_path)
        if not project:
            return False

        return self.storage.delete_project(project.id)

    def get_file_info(
        self,
        project_path: str,
        file_path: str
    ) -> Optional[dict]:
        """Get information about a specific file.

        Args:
            project_path: Path to the project
            file_path: Relative path to the file

        Returns:
            Dictionary with file info or None if not found
        """
        project = self.storage.get_project(project_path)
        if not project:
            return None

        file_record = self.storage.get_file_by_path(project.id, file_path)
        if not file_record:
            return None

        imports = self.storage.get_imports_by_file(file_record.id)
        functions = self.storage.get_functions_by_file(file_record.id)
        summaries = self.storage.get_summaries_by_file(file_record.id)

        # Get enhanced symbols if available
        symbols = []
        if hasattr(self.storage, 'get_symbols_by_file'):
            symbols = self.storage.get_symbols_by_file(file_record.id)

        return {
            "id": file_record.id,
            "relative_path": file_record.relative_path,
            "file_type": file_record.file_type,
            "size": file_record.size,
            "depth": file_record.depth,
            "modified_time": file_record.modified_time.isoformat()
                if hasattr(file_record.modified_time, 'isoformat')
                else str(file_record.modified_time),
            "imports": [
                {
                    "module": imp.module,
                    "type": imp.import_type,
                    "line": imp.line,
                    "is_external": imp.is_external()
                }
                for imp in imports
            ],
            "functions": [
                {
                    "name": f.name,
                    "signature": f.signature,
                    "start_line": f.start_line,
                    "end_line": f.end_line
                }
                for f in functions
            ],
            "symbols": [
                {
                    "name": s.name,
                    "type": s.symbol_type,
                    "container": s.container_name,
                    "signature": s.signature,
                    "start_line": s.start_line,
                    "end_line": s.end_line,
                    "is_exported": s.is_exported
                }
                for s in symbols
            ],
            "summaries": [
                {
                    "entity_name": s.entity_name,
                    "entity_type": s.entity_type,
                    "summary": s.summary
                }
                for s in summaries
            ]
        }

    def get_dependency_graph(
        self,
        project_path: str
    ) -> Optional[dict]:
        """Get the dependency graph for a project.

        Args:
            project_path: Path to the project

        Returns:
            Dictionary with nodes and edges, or None if not found
        """
        project = self.storage.get_project(project_path)
        if not project:
            return None

        files = self.storage.get_files_by_project(project.id)

        nodes = []
        edges = []

        for file_record in files:
            nodes.append({
                "id": file_record.relative_path,
                "type": file_record.file_type,
                "size": file_record.size
            })

            imports = self.storage.get_file_imports(
                project.id,
                file_record.relative_path
            )
            for imp_path in imports:
                edges.append({
                    "source": file_record.relative_path,
                    "target": imp_path
                })

        return {
            "nodes": nodes,
            "edges": edges,
            "node_count": len(nodes),
            "edge_count": len(edges)
        }

    def get_parse_errors(self, project_path: str) -> list[dict]:
        """Get parse errors for a project.

        Args:
            project_path: Path to the project

        Returns:
            List of parse error dicts
        """
        project = self.storage.get_project(project_path)
        if not project:
            return []

        if not isinstance(self.storage, SQLiteStorage):
            return []

        errors = self.storage.get_parse_errors(project.id)
        return [
            {
                "file_id": e.file_id,
                "error_message": e.error_message,
                "error_line": e.error_line,
                "created_at": str(e.created_at)
            }
            for e in errors
        ]
