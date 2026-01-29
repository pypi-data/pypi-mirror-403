"""Symbol Usage Finder Service for code knowledge graph.

This module implements symbol usage finding functionality,
combining symbol search with function call analysis to find
all usages of a symbol across the codebase.

Supports detailed usage type classification:
- import: Import statements
- call: Function/method calls
- method_call: Method invocations on objects
- type_instantiation: Type instantiation (&Tenant{}, new(Tenant))
- function_parameter: Used as function parameter type
- function_return: Used as return type
- type_assertion: Type assertions (t.(*Tenant))
- reference: General reference

Feature: code-knowledge-graph-enhancement
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from core.storage.sqlite import SQLiteStorage

logger = logging.getLogger(__name__)


# Detailed usage type constants
class UsageType:
    """Constants for usage type classification."""
    IMPORT = "import"
    CALL = "call"
    METHOD_CALL = "method_call"
    TYPE_INSTANTIATION = "type_instantiation"
    FUNCTION_PARAMETER = "function_parameter"
    FUNCTION_RETURN = "function_return"
    TYPE_ASSERTION = "type_assertion"
    REFERENCE = "reference"


@dataclass
class SymbolDefinition:
    """Definition location of a symbol."""
    file_path: str
    line_number: int
    symbol_type: str
    signature: Optional[str] = None
    container_name: Optional[str] = None


@dataclass
class SymbolUsage:
    """A single usage of a symbol."""
    file_path: str
    line_number: int
    usage_type: str  # "import", "call", "method_call", "type_instantiation", etc.
    context: str  # Code snippet around the usage
    container_name: Optional[str] = None  # Containing function/class


@dataclass
class UsagesByType:
    """Usages organized by type."""
    imports: list[SymbolUsage] = field(default_factory=list)
    calls: list[SymbolUsage] = field(default_factory=list)
    method_calls: list[SymbolUsage] = field(default_factory=list)
    type_instantiations: list[SymbolUsage] = field(default_factory=list)
    function_parameters: list[SymbolUsage] = field(default_factory=list)
    function_returns: list[SymbolUsage] = field(default_factory=list)
    type_assertions: list[SymbolUsage] = field(default_factory=list)
    references: list[SymbolUsage] = field(default_factory=list)

    def to_dict(self) -> dict[str, list[dict]]:
        """Convert to dictionary format."""
        return {
            "import": [self._usage_to_dict(u) for u in self.imports],
            "call": [self._usage_to_dict(u) for u in self.calls],
            "method_call": [self._usage_to_dict(u) for u in self.method_calls],
            "type_instantiation": [self._usage_to_dict(u) for u in self.type_instantiations],
            "function_parameter": [self._usage_to_dict(u) for u in self.function_parameters],
            "function_return": [self._usage_to_dict(u) for u in self.function_returns],
            "type_assertion": [self._usage_to_dict(u) for u in self.type_assertions],
            "reference": [self._usage_to_dict(u) for u in self.references],
        }

    def _usage_to_dict(self, usage: SymbolUsage) -> dict:
        """Convert usage to dict."""
        return {
            "file_path": usage.file_path,
            "line_number": usage.line_number,
            "context": usage.context,
            "container_name": usage.container_name,
        }

    def get_summary(self) -> dict[str, int]:
        """Get count summary by type."""
        return {
            "import": len(self.imports),
            "call": len(self.calls),
            "method_call": len(self.method_calls),
            "type_instantiation": len(self.type_instantiations),
            "function_parameter": len(self.function_parameters),
            "function_return": len(self.function_returns),
            "type_assertion": len(self.type_assertions),
            "reference": len(self.references),
        }


@dataclass
class FindUsagesResult:
    """Result of finding all usages of a symbol."""
    symbol_name: str
    symbol_type: Optional[str]
    definition: Optional[SymbolDefinition]
    usages: list[SymbolUsage]
    total: int
    usages_by_type: Optional[UsagesByType] = None
    summary: Optional[dict[str, int]] = None
    message: Optional[str] = None


class UsageFinderService:
    """Service for finding all usages of a symbol.

    Combines data from:
    - symbols table (definitions)
    - enhanced_function_calls table (call usages)
    - imports table (import usages)
    """

    def __init__(self, storage: SQLiteStorage):
        """Initialize usage finder service.

        Args:
            storage: SQLite storage backend instance
        """
        self.storage = storage

    def find_all_usages(
        self,
        project_path: str,
        symbol_name: str,
        symbol_type: Optional[str] = None,
        limit: int = 100,
        classify_types: bool = True
    ) -> FindUsagesResult:
        """Find all usages of a symbol in the project.

        Args:
            project_path: Path to the project
            symbol_name: Name of the symbol to find
            symbol_type: Optional type filter ("function", "class", "variable", etc.)
            limit: Maximum number of usages to return
            classify_types: Whether to classify usages by type (default True)

        Returns:
            FindUsagesResult containing definition and all usages
        """
        # Validate limit
        limit = max(1, min(500, limit))

        # Get project
        project = self.storage.get_project(project_path)
        if not project:
            return FindUsagesResult(
                symbol_name=symbol_name,
                symbol_type=symbol_type,
                definition=None,
                usages=[],
                total=0,
                message=f"Project not found: {project_path}"
            )

        cursor = self.storage._get_cursor()

        # Find symbol definition
        definition = self._find_definition(cursor, project.id, symbol_name, symbol_type)

        # Find all usages
        usages: list[SymbolUsage] = []

        # 1. Find import usages (where the symbol is imported)
        import_usages = self._find_import_usages(
            cursor, project.id, symbol_name, limit
        )
        usages.extend(import_usages)

        # 2. Find call usages (where the symbol is called)
        call_usages = self._find_call_usages(
            cursor, project.id, symbol_name, limit - len(usages)
        )
        usages.extend(call_usages)

        # 3. Find reference usages from enhanced_function_calls
        ref_usages = self._find_reference_usages(
            cursor, project.id, symbol_name, limit - len(usages)
        )
        usages.extend(ref_usages)

        # Sort by file path and line number
        usages.sort(key=lambda u: (u.file_path, u.line_number))

        # Remove duplicates
        seen = set()
        unique_usages = []
        for usage in usages:
            key = (usage.file_path, usage.line_number, usage.usage_type)
            if key not in seen:
                seen.add(key)
                unique_usages.append(usage)

        # Apply limit
        unique_usages = unique_usages[:limit]

        # Classify usages by type if requested
        usages_by_type = None
        summary = None
        if classify_types:
            usages_by_type = self._classify_usages(unique_usages)
            summary = usages_by_type.get_summary()

        return FindUsagesResult(
            symbol_name=symbol_name,
            symbol_type=symbol_type,
            definition=definition,
            usages=unique_usages,
            total=len(unique_usages),
            usages_by_type=usages_by_type,
            summary=summary,
            message=None
        )

    def _classify_usages(self, usages: list[SymbolUsage]) -> UsagesByType:
        """Classify usages by their usage type.

        Analyzes the context of each usage to determine its specific type:
        - import: Import statements
        - call: Direct function calls
        - method_call: Method invocations on objects (obj.method())
        - type_instantiation: Type instantiation (&Type{}, new(Type))
        - function_parameter: Used as parameter type
        - function_return: Used as return type
        - type_assertion: Type assertions
        - reference: Other references

        Args:
            usages: List of usages to classify

        Returns:
            UsagesByType with classified usages
        """
        classified = UsagesByType()

        for usage in usages:
            # Determine detailed type based on usage_type and context
            context = usage.context.lower()

            if usage.usage_type == UsageType.IMPORT:
                classified.imports.append(usage)
            elif usage.usage_type == UsageType.CALL:
                # Distinguish between direct calls and method calls
                if "." in usage.context and not usage.context.startswith("defer:"):
                    classified.method_calls.append(usage)
                else:
                    classified.calls.append(usage)
            elif usage.usage_type == UsageType.REFERENCE:
                # Analyze context for more specific classification
                if self._is_type_instantiation(usage.context):
                    usage.usage_type = UsageType.TYPE_INSTANTIATION
                    classified.type_instantiations.append(usage)
                elif self._is_type_assertion(usage.context):
                    usage.usage_type = UsageType.TYPE_ASSERTION
                    classified.type_assertions.append(usage)
                else:
                    classified.references.append(usage)
            else:
                # Default to reference
                classified.references.append(usage)

        return classified

    def _is_type_instantiation(self, context: str) -> bool:
        """Check if context indicates type instantiation.

        Patterns:
        - Go: &Type{}, Type{}, new(Type)
        - Python: Type(), Type(args)
        - JS/TS: new Type(), new Type(args)

        Args:
            context: Code context

        Returns:
            True if type instantiation
        """
        # Go patterns
        if "&" in context and "{" in context:
            return True
        if context.endswith("{}") or context.endswith("{})"):
            return True
        if "new(" in context.lower():
            return True

        # JS/TS patterns
        if context.lower().startswith("new "):
            return True

        return False

    def _is_type_assertion(self, context: str) -> bool:
        """Check if context indicates type assertion.

        Patterns:
        - Go: x.(*Type), x.(Type)
        - TypeScript: <Type>x, x as Type

        Args:
            context: Code context

        Returns:
            True if type assertion
        """
        # Go pattern
        if ".(*" in context or ".(" in context:
            return True

        # TypeScript patterns
        if context.startswith("<") and ">" in context:
            return True
        if " as " in context.lower():
            return True

        return False

    def _find_definition(
        self,
        cursor,
        project_id: int,
        symbol_name: str,
        symbol_type: Optional[str]
    ) -> Optional[SymbolDefinition]:
        """Find the definition of a symbol.

        Args:
            cursor: Database cursor
            project_id: Project ID
            symbol_name: Symbol name
            symbol_type: Optional type filter

        Returns:
            SymbolDefinition if found, None otherwise
        """
        if symbol_type:
            cursor.execute(
                """
                SELECT s.*, f.relative_path
                FROM symbols s
                JOIN files f ON s.file_id = f.id
                WHERE f.project_id = ?
                  AND s.name = ?
                  AND s.symbol_type = ?
                ORDER BY s.is_exported DESC, f.relative_path
                LIMIT 1
                """,
                (project_id, symbol_name, symbol_type)
            )
        else:
            cursor.execute(
                """
                SELECT s.*, f.relative_path
                FROM symbols s
                JOIN files f ON s.file_id = f.id
                WHERE f.project_id = ?
                  AND s.name = ?
                ORDER BY s.is_exported DESC, f.relative_path
                LIMIT 1
                """,
                (project_id, symbol_name)
            )

        row = cursor.fetchone()
        if row:
            return SymbolDefinition(
                file_path=row["relative_path"],
                line_number=row["start_line"] or 0,
                symbol_type=row["symbol_type"],
                signature=row["signature"],
                container_name=row["container_name"]
            )

        return None

    def _find_import_usages(
        self,
        cursor,
        project_id: int,
        symbol_name: str,
        limit: int
    ) -> list[SymbolUsage]:
        """Find import usages of a symbol.

        Args:
            cursor: Database cursor
            project_id: Project ID
            symbol_name: Symbol name
            limit: Maximum results

        Returns:
            List of import usages
        """
        usages = []

        # Find imports that reference this symbol
        cursor.execute(
            """
            SELECT
                f.relative_path,
                i.line,
                i.module,
                i.import_type
            FROM imports i
            JOIN files f ON i.file_id = f.id
            WHERE f.project_id = ?
              AND (
                  i.module LIKE ?
                  OR i.module LIKE ?
                  OR i.module = ?
              )
            ORDER BY f.relative_path, i.line
            LIMIT ?
            """,
            (project_id, f"%{symbol_name}", f"%.{symbol_name}", symbol_name, limit)
        )

        for row in cursor.fetchall():
            context = f"import {row['module']}"
            if row["import_type"] == "from":
                context = f"from ... import {symbol_name}"

            usages.append(SymbolUsage(
                file_path=row["relative_path"],
                line_number=row["line"] or 0,
                usage_type="import",
                context=context,
                container_name=None
            ))

        return usages

    def _find_call_usages(
        self,
        cursor,
        project_id: int,
        symbol_name: str,
        limit: int
    ) -> list[SymbolUsage]:
        """Find call usages of a symbol from enhanced_function_calls.

        Args:
            cursor: Database cursor
            project_id: Project ID
            symbol_name: Symbol name
            limit: Maximum results

        Returns:
            List of call usages
        """
        usages = []

        if limit <= 0:
            return usages

        # Find function calls to this symbol
        cursor.execute(
            """
            SELECT
                f.relative_path,
                efc.line_number,
                efc.call_type,
                efc.call_context,
                s.name as caller_name,
                s.container_name as caller_container
            FROM enhanced_function_calls efc
            JOIN files f ON efc.source_file_id = f.id
            JOIN symbols s ON efc.source_symbol_id = s.id
            WHERE f.project_id = ?
              AND efc.target_symbol_name = ?
            ORDER BY f.relative_path, efc.line_number
            LIMIT ?
            """,
            (project_id, symbol_name, limit)
        )

        for row in cursor.fetchall():
            context = f"{symbol_name}()"
            if row["call_context"]:
                context = f"{row['call_context']}.{symbol_name}()"

            container = row["caller_name"]
            if row["caller_container"]:
                container = f"{row['caller_container']}.{row['caller_name']}"

            usages.append(SymbolUsage(
                file_path=row["relative_path"],
                line_number=row["line_number"] or 0,
                usage_type="call",
                context=context,
                container_name=container
            ))

        return usages

    def _find_reference_usages(
        self,
        cursor,
        project_id: int,
        symbol_name: str,
        limit: int
    ) -> list[SymbolUsage]:
        """Find reference usages where symbol is the target.

        Args:
            cursor: Database cursor
            project_id: Project ID
            symbol_name: Symbol name
            limit: Maximum results

        Returns:
            List of reference usages
        """
        usages = []

        if limit <= 0:
            return usages

        # Find references via target_symbol_id join
        cursor.execute(
            """
            SELECT
                f.relative_path,
                efc.line_number,
                efc.call_type,
                efc.call_context,
                src.name as caller_name,
                src.container_name as caller_container,
                tgt.name as target_name
            FROM enhanced_function_calls efc
            JOIN files f ON efc.source_file_id = f.id
            JOIN symbols src ON efc.source_symbol_id = src.id
            JOIN symbols tgt ON efc.target_symbol_id = tgt.id
            WHERE f.project_id = ?
              AND tgt.name = ?
            ORDER BY f.relative_path, efc.line_number
            LIMIT ?
            """,
            (project_id, symbol_name, limit)
        )

        for row in cursor.fetchall():
            context = f"{symbol_name}()"
            if row["call_context"]:
                context = f"{row['call_context']}.{symbol_name}()"

            container = row["caller_name"]
            if row["caller_container"]:
                container = f"{row['caller_container']}.{row['caller_name']}"

            usages.append(SymbolUsage(
                file_path=row["relative_path"],
                line_number=row["line_number"] or 0,
                usage_type="reference",
                context=context,
                container_name=container
            ))

        return usages

    def find_usages_in_file(
        self,
        project_path: str,
        file_path: str,
        symbol_name: str
    ) -> FindUsagesResult:
        """Find all usages of a symbol within a specific file.

        Args:
            project_path: Path to the project
            file_path: Relative path to the file
            symbol_name: Name of the symbol to find

        Returns:
            FindUsagesResult containing usages in the file
        """
        # Get project
        project = self.storage.get_project(project_path)
        if not project:
            return FindUsagesResult(
                symbol_name=symbol_name,
                symbol_type=None,
                definition=None,
                usages=[],
                total=0,
                message=f"Project not found: {project_path}"
            )

        cursor = self.storage._get_cursor()

        # Get file
        file_record = self.storage.get_file_by_path(project.id, file_path)
        if not file_record:
            return FindUsagesResult(
                symbol_name=symbol_name,
                symbol_type=None,
                definition=None,
                usages=[],
                total=0,
                message=f"File not found: {file_path}"
            )

        usages: list[SymbolUsage] = []

        # Find calls in this file
        cursor.execute(
            """
            SELECT
                efc.line_number,
                efc.call_type,
                efc.call_context,
                s.name as caller_name,
                s.container_name
            FROM enhanced_function_calls efc
            JOIN symbols s ON efc.source_symbol_id = s.id
            WHERE efc.source_file_id = ?
              AND efc.target_symbol_name = ?
            ORDER BY efc.line_number
            """,
            (file_record.id, symbol_name)
        )

        for row in cursor.fetchall():
            context = f"{symbol_name}()"
            if row["call_context"]:
                context = f"{row['call_context']}.{symbol_name}()"

            usages.append(SymbolUsage(
                file_path=file_path,
                line_number=row["line_number"] or 0,
                usage_type="call",
                context=context,
                container_name=row["caller_name"]
            ))

        return FindUsagesResult(
            symbol_name=symbol_name,
            symbol_type=None,
            definition=None,
            usages=usages,
            total=len(usages),
            message=None
        )
