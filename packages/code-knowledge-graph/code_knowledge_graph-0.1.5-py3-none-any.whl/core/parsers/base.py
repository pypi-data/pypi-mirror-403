"""Base parser class for import and function extraction."""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# Configure parser logger
logger = logging.getLogger("code_knowledge_graph.parser")


@dataclass
class ParseError:
    """Represents a parsing error."""
    file_path: str
    error_type: str  # syntax_error, encoding_error, timeout, unknown
    message: str
    line: int | None = None


@dataclass
class ParseStats:
    """Statistics for parsing operations."""
    total_files: int = 0
    successful: int = 0
    failed: int = 0
    errors: list[ParseError] = field(default_factory=list)
    
    def add_success(self):
        self.total_files += 1
        self.successful += 1
    
    def add_error(self, error: ParseError):
        self.total_files += 1
        self.failed += 1
        self.errors.append(error)
    
    def to_dict(self) -> dict:
        return {
            "total_files": self.total_files,
            "successful": self.successful,
            "failed": self.failed,
            "success_rate": f"{(self.successful / self.total_files * 100):.1f}%" if self.total_files > 0 else "N/A",
            "errors": [
                {
                    "file": e.file_path,
                    "type": e.error_type,
                    "message": e.message,
                    "line": e.line
                }
                for e in self.errors
            ]
        }


@dataclass
class ImportInfo:
    """Represents an import statement."""

    module: str  # The imported module path
    import_type: str  # static, dynamic, require
    line: int  # Line number in source file

    def is_relative(self) -> bool:
        """Check if this is a relative import."""
        return self.module.startswith(".") or self.module.startswith("@/")

    def is_external(self) -> bool:
        """Check if this is likely an external package."""
        if self.is_relative():
            return False
        # External packages don't start with . or have path separators at start
        first_part = self.module.split("/")[0].split("\\")[0]
        # Common external indicators
        return not first_part.startswith(".")


@dataclass
class FunctionInfo:
    """Represents a function or method definition."""

    name: str
    signature: str  # Full signature (without body)
    start_line: int
    end_line: int
    calls: list[str] = field(default_factory=list)  # Functions called within
    is_method: bool = False  # True if it's a class method
    is_async: bool = False
    docstring: Optional[str] = None


@dataclass
class ClassInfo:
    """Represents a class definition."""

    name: str
    signature: str  # Class declaration line
    start_line: int
    end_line: int
    methods: list[FunctionInfo] = field(default_factory=list)
    bases: list[str] = field(default_factory=list)  # Base classes
    docstring: Optional[str] = None


@dataclass
class ParseResult:
    """Complete parsing result for a file."""

    imports: list[ImportInfo] = field(default_factory=list)
    functions: list[FunctionInfo] = field(default_factory=list)
    classes: list[ClassInfo] = field(default_factory=list)


@dataclass
class DecoratorInfo:
    """Represents a decorator applied to a function or class."""
    
    name: str  # Decorator name (e.g., "app.get", "staticmethod")
    arguments: list[str] = field(default_factory=list)  # Decorator arguments
    line: int = 0  # Line number


@dataclass
class AttributeInfo:
    """Represents a class attribute or instance attribute."""
    
    name: str  # Attribute name
    type_annotation: Optional[str] = None  # Type annotation if present
    default_value: Optional[str] = None  # Default value if present
    line: int = 0  # Line number
    is_class_var: bool = False  # True if ClassVar


@dataclass
class GlobalVariableInfo:
    """Represents a global/module-level variable definition."""
    
    name: str  # Variable name
    type_annotation: Optional[str] = None  # Type annotation if present
    value: Optional[str] = None  # Value (may be truncated for long literals)
    line: int = 0  # Line number


@dataclass
class StructFieldInfo:
    """Represents a Go struct field."""
    
    name: str  # Field name
    type_annotation: str  # Field type
    tag: Optional[str] = None  # Struct tag (e.g., `json:"name"`)
    line: int = 0  # Line number


@dataclass
class InterfaceMethodInfo:
    """Represents a Go interface method signature."""
    
    name: str  # Method name
    signature: str  # Method signature
    line: int = 0  # Line number


@dataclass
class StructInfo:
    """Represents a Go struct definition."""
    
    name: str
    fields: list[StructFieldInfo] = field(default_factory=list)
    start_line: int = 0
    end_line: int = 0
    docstring: Optional[str] = None


@dataclass
class InterfaceInfo:
    """Represents a Go interface definition."""
    
    name: str
    methods: list[InterfaceMethodInfo] = field(default_factory=list)
    start_line: int = 0
    end_line: int = 0
    docstring: Optional[str] = None


@dataclass
class EnhancedFunctionInfo(FunctionInfo):
    """Enhanced function info with decorators and receiver info."""
    
    decorators: list[DecoratorInfo] = field(default_factory=list)
    receiver_type: Optional[str] = None  # Go receiver type (e.g., "*Server")
    receiver_name: Optional[str] = None  # Go receiver name (e.g., "s")
    call_type: str = "direct"  # direct, deferred, async (goroutine)


@dataclass
class EnhancedClassInfo(ClassInfo):
    """Enhanced class info with decorators and attributes."""
    
    decorators: list[DecoratorInfo] = field(default_factory=list)
    attributes: list[AttributeInfo] = field(default_factory=list)


@dataclass
class EnhancedParseResult(ParseResult):
    """Enhanced parsing result with additional information."""
    
    global_variables: list[GlobalVariableInfo] = field(default_factory=list)
    structs: list[StructInfo] = field(default_factory=list)  # Go structs
    interfaces: list[InterfaceInfo] = field(default_factory=list)  # Go interfaces
    package_name: Optional[str] = None  # Go package name
    decorators: list[DecoratorInfo] = field(default_factory=list)  # Top-level decorators


class ParseErrorHandler:
    """Handler for parse errors that allows partial parsing to continue.
    
    This class records parse errors without interrupting the indexing process,
    supporting partial parsing of files with syntax errors.
    """
    
    def __init__(self):
        self.errors: list[ParseError] = []
    
    def record_error(
        self,
        file_path: str,
        error_type: str,
        message: str,
        line: Optional[int] = None
    ) -> None:
        """Record a parse error.
        
        Args:
            file_path: Path to the file with the error
            error_type: Type of error (syntax_error, encoding_error, timeout, unknown)
            message: Error message
            line: Optional line number where error occurred
        """
        self.errors.append(ParseError(
            file_path=file_path,
            error_type=error_type,
            message=message,
            line=line
        ))
    
    def record_exception(
        self,
        file_path: str,
        exception: Exception,
        line: Optional[int] = None
    ) -> None:
        """Record an exception as a parse error.
        
        Args:
            file_path: Path to the file with the error
            exception: The exception that occurred
            line: Optional line number where error occurred
        """
        error_type = "syntax_error"
        if isinstance(exception, UnicodeDecodeError):
            error_type = "encoding_error"
        elif isinstance(exception, TimeoutError):
            error_type = "timeout"
        elif not isinstance(exception, SyntaxError):
            error_type = "unknown"
        
        self.record_error(
            file_path=file_path,
            error_type=error_type,
            message=str(exception),
            line=line
        )
    
    def get_errors(self) -> list[ParseError]:
        """Get all recorded errors."""
        return self.errors.copy()
    
    def get_errors_for_file(self, file_path: str) -> list[ParseError]:
        """Get errors for a specific file."""
        return [e for e in self.errors if e.file_path == file_path]
    
    def clear_errors(self) -> None:
        """Clear all recorded errors."""
        self.errors.clear()
    
    def clear_errors_for_file(self, file_path: str) -> None:
        """Clear errors for a specific file."""
        self.errors = [e for e in self.errors if e.file_path != file_path]
    
    def has_errors(self) -> bool:
        """Check if any errors have been recorded."""
        return len(self.errors) > 0
    
    def to_stats(self) -> ParseStats:
        """Convert errors to ParseStats object."""
        stats = ParseStats()
        stats.errors = self.errors.copy()
        stats.failed = len(self.errors)
        return stats


class BaseParser(ABC):
    """Abstract base class for language-specific parsers."""

    supported_extensions: list[str] = []

    @abstractmethod
    def parse(self, content: str, file_path: Path) -> list[ImportInfo]:
        """
        Parse source code and extract import statements.

        Args:
            content: Source code content
            file_path: Path to the source file (for context)

        Returns:
            List of ImportInfo objects
        """
        pass

    def parse_full(self, content: str, file_path: Path) -> ParseResult:
        """
        Parse source code and extract all information.

        Args:
            content: Source code content
            file_path: Path to the source file (for context)

        Returns:
            ParseResult with imports, functions, and classes
        """
        # Default implementation: only parse imports
        return ParseResult(imports=self.parse(content, file_path))

    def extract_functions(
        self,
        content: str,
        file_path: Path
    ) -> list[FunctionInfo]:
        """
        Extract function definitions from source code.

        Args:
            content: Source code content
            file_path: Path to the source file (for context)

        Returns:
            List of FunctionInfo objects
        """
        result = self.parse_full(content, file_path)
        return result.functions

    def extract_classes(
        self,
        content: str,
        file_path: Path
    ) -> list[ClassInfo]:
        """
        Extract class definitions from source code.

        Args:
            content: Source code content
            file_path: Path to the source file (for context)

        Returns:
            List of ClassInfo objects
        """
        result = self.parse_full(content, file_path)
        return result.classes

    @classmethod
    def can_parse(cls, file_path: Path) -> bool:
        """Check if this parser can handle the given file."""
        return file_path.suffix.lower() in cls.supported_extensions
