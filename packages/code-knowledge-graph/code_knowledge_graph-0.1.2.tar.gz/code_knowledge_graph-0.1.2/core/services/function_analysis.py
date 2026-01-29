"""Function-level dependency analysis service.

This module provides services for analyzing function-level
dependencies between specified files.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from ..parsers import (
    PythonParser,
    JsParser,
    VueParser,
    GoParser,
    FunctionInfo,
    ClassInfo,
    ParseResult,
    EnhancedFunctionInfo,
)


@dataclass
class FunctionRelation:
    """Represents a function call relationship."""

    caller_function: str
    caller_file: str
    caller_line: int
    callee_function: str
    callee_file: Optional[str]  # None if external or unresolved
    callee_line: Optional[int]  # None if external or unresolved
    is_external: bool = False


@dataclass
class FileAnalysis:
    """Analysis result for a single file."""

    file_path: str
    functions: list[FunctionInfo]
    classes: list[ClassInfo]
    all_function_names: set[str] = field(default_factory=set)


@dataclass
class FunctionRelationsResult:
    """Complete function relations analysis result."""

    files: list[str]
    file_analyses: list[FileAnalysis]
    relations: list[FunctionRelation]
    call_graph: dict[str, list[str]]  # {caller: [callees]}
    external_calls: set[str]


class FunctionAnalysisService:
    """Service for analyzing function-level dependencies.

    Analyzes function definitions and call relationships
    between a specified set of files (maximum 50).

    Supports Python, JavaScript/TypeScript, Vue, and Go files.
    For Go methods, properly handles receiver types to build
    relations like Tenant.IsActive.
    """

    MAX_FILES = 50  # Increased from 10

    def __init__(self):
        """Initialize function analysis service."""
        self.parsers = [
            PythonParser(),
            JsParser(),
            VueParser(),
            GoParser(),
        ]

    def analyze_files(
        self,
        file_paths: list[str | Path]
    ) -> FunctionRelationsResult:
        """Analyze function relations between specified files.

        Args:
            file_paths: List of file paths to analyze (max 10)

        Returns:
            FunctionRelationsResult with all analysis data

        Raises:
            ValueError: If more than 10 files are specified
        """
        if len(file_paths) > self.MAX_FILES:
            raise ValueError(
                f"Maximum {self.MAX_FILES} files allowed, "
                f"got {len(file_paths)}"
            )

        # Convert all paths to Path objects
        paths = [Path(p) if isinstance(p, str) else p for p in file_paths]

        # Analyze each file
        file_analyses: list[FileAnalysis] = []
        all_functions: dict[str, tuple[str, int]] = {}  # name -> (file, line)

        for path in paths:
            analysis = self._analyze_file(path)
            if analysis:
                file_analyses.append(analysis)
                # Build function name index
                for func in analysis.functions:
                    key = func.name
                    all_functions[key] = (str(path), func.start_line)

                    # For Go methods, also store with receiver type prefix
                    # e.g., for `func (t *Tenant) IsActive()`, store as both
                    # "IsActive" and "Tenant.IsActive"
                    if isinstance(func, EnhancedFunctionInfo) and func.receiver_type:
                        # Extract base type from pointer type (e.g., *Tenant -> Tenant)
                        base_type = func.receiver_type.lstrip('*')
                        qualified_name = f"{base_type}.{func.name}"
                        all_functions[qualified_name] = (str(path), func.start_line)

                for cls in analysis.classes:
                    for method in cls.methods:
                        # Store methods with class prefix for unique identification
                        key = f"{cls.name}.{method.name}"
                        all_functions[key] = (str(path), method.start_line)
                        # Also store just the method name for simpler lookups
                        all_functions[method.name] = (str(path), method.start_line)

        # Build relations
        relations: list[FunctionRelation] = []
        call_graph: dict[str, list[str]] = {}
        external_calls: set[str] = set()

        for analysis in file_analyses:
            for func in analysis.functions:
                # For Go methods with receiver, use qualified name
                caller_name = func.name
                if isinstance(func, EnhancedFunctionInfo) and func.receiver_type:
                    base_type = func.receiver_type.lstrip('*')
                    caller_name = f"{base_type}.{func.name}"

                caller_key = f"{analysis.file_path}:{caller_name}"
                callees = []

                for call_name in func.calls:
                    relation = self._resolve_call(
                        caller_func=caller_name,
                        caller_file=analysis.file_path,
                        caller_line=func.start_line,
                        callee_name=call_name,
                        all_functions=all_functions
                    )
                    relations.append(relation)
                    callees.append(call_name)

                    if relation.is_external:
                        external_calls.add(call_name)

                if callees:
                    call_graph[caller_key] = callees

            # Also process class methods
            for cls in analysis.classes:
                for method in cls.methods:
                    caller_key = f"{analysis.file_path}:{cls.name}.{method.name}"
                    callees = []

                    for call_name in method.calls:
                        relation = self._resolve_call(
                            caller_func=f"{cls.name}.{method.name}",
                            caller_file=analysis.file_path,
                            caller_line=method.start_line,
                            callee_name=call_name,
                            all_functions=all_functions
                        )
                        relations.append(relation)
                        callees.append(call_name)

                        if relation.is_external:
                            external_calls.add(call_name)

                    if callees:
                        call_graph[caller_key] = callees

        return FunctionRelationsResult(
            files=[str(p) for p in paths],
            file_analyses=file_analyses,
            relations=relations,
            call_graph=call_graph,
            external_calls=external_calls
        )

    def _analyze_file(self, path: Path) -> Optional[FileAnalysis]:
        """Analyze a single file for functions and classes."""
        if not path.exists():
            return None

        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return None

        # Find appropriate parser
        parser = None
        for p in self.parsers:
            if p.can_parse(path):
                parser = p
                break

        if not parser:
            return None

        # Parse the file
        result = parser.parse_full(content, path)

        # Collect all function names
        all_names: set[str] = set()
        for func in result.functions:
            all_names.add(func.name)
        for cls in result.classes:
            all_names.add(cls.name)
            for method in cls.methods:
                all_names.add(method.name)
                all_names.add(f"{cls.name}.{method.name}")

        return FileAnalysis(
            file_path=str(path),
            functions=result.functions,
            classes=result.classes,
            all_function_names=all_names
        )

    def _resolve_call(
        self,
        caller_func: str,
        caller_file: str,
        caller_line: int,
        callee_name: str,
        all_functions: dict[str, tuple[str, int]]
    ) -> FunctionRelation:
        """Resolve a function call to its definition if possible."""
        if callee_name in all_functions:
            callee_file, callee_line = all_functions[callee_name]
            return FunctionRelation(
                caller_function=caller_func,
                caller_file=caller_file,
                caller_line=caller_line,
                callee_function=callee_name,
                callee_file=callee_file,
                callee_line=callee_line,
                is_external=False
            )
        else:
            return FunctionRelation(
                caller_function=caller_func,
                caller_file=caller_file,
                caller_line=caller_line,
                callee_function=callee_name,
                callee_file=None,
                callee_line=None,
                is_external=True
            )

    def get_function_callers(
        self,
        file_paths: list[str | Path],
        function_name: str
    ) -> list[FunctionRelation]:
        """Find all functions that call a specific function.

        Args:
            file_paths: Files to search in
            function_name: Function name to find callers for

        Returns:
            List of FunctionRelation objects where callee is the target
        """
        result = self.analyze_files(file_paths)
        return [
            r for r in result.relations
            if r.callee_function == function_name
        ]

    def get_function_callees(
        self,
        file_paths: list[str | Path],
        function_name: str
    ) -> list[FunctionRelation]:
        """Find all functions called by a specific function.

        Args:
            file_paths: Files to search in
            function_name: Function name to find callees for

        Returns:
            List of FunctionRelation objects where caller is the target
        """
        result = self.analyze_files(file_paths)
        return [
            r for r in result.relations
            if r.caller_function == function_name or
               r.caller_function.endswith(f".{function_name}")
        ]

    def to_dict(self, result: FunctionRelationsResult) -> dict:
        """Convert analysis result to dictionary for JSON serialization."""
        return {
            "files": result.files,
            "functions": [
                {
                    "file": a.file_path,
                    "functions": [
                        {
                            "name": f.name,
                            "signature": f.signature,
                            "start_line": f.start_line,
                            "end_line": f.end_line,
                            "calls": f.calls,
                            "is_async": f.is_async
                        }
                        for f in a.functions
                    ],
                    "classes": [
                        {
                            "name": c.name,
                            "signature": c.signature,
                            "start_line": c.start_line,
                            "end_line": c.end_line,
                            "methods": [
                                {
                                    "name": m.name,
                                    "signature": m.signature,
                                    "start_line": m.start_line,
                                    "end_line": m.end_line,
                                    "calls": m.calls
                                }
                                for m in c.methods
                            ]
                        }
                        for c in a.classes
                    ]
                }
                for a in result.file_analyses
            ],
            "relations": [
                {
                    "caller_function": r.caller_function,
                    "caller_file": r.caller_file,
                    "caller_line": r.caller_line,
                    "callee_function": r.callee_function,
                    "callee_file": r.callee_file,
                    "callee_line": r.callee_line,
                    "is_external": r.is_external
                }
                for r in result.relations
            ],
            "call_graph": result.call_graph,
            "external_calls": list(result.external_calls)
        }
