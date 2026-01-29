"""Language parsers for import and function extraction."""

from typing import Optional

from .base import (
    BaseParser, ImportInfo, FunctionInfo, ClassInfo, ParseResult, ParseError, ParseStats,
    DecoratorInfo, AttributeInfo, GlobalVariableInfo, StructFieldInfo, InterfaceMethodInfo,
    StructInfo, InterfaceInfo, EnhancedFunctionInfo, EnhancedClassInfo, EnhancedParseResult,
    ParseErrorHandler
)
from .python_parser import PythonParser
from .js_parser import JsParser
from .vue_parser import VueParser
from .go_parser import GoParser


# Singleton parser instances
_python_parser = PythonParser()
_js_parser = JsParser()
_vue_parser = VueParser()
_go_parser = GoParser()

# Map file extensions to parsers
_PARSER_MAP: dict[str, BaseParser] = {
    ".py": _python_parser,
    ".pyw": _python_parser,
    ".js": _js_parser,
    ".jsx": _js_parser,
    ".mjs": _js_parser,
    ".cjs": _js_parser,
    ".ts": _js_parser,
    ".tsx": _js_parser,
    ".vue": _vue_parser,
    ".go": _go_parser,
}


def get_parser(extension: str) -> Optional[BaseParser]:
    """Get parser for a file extension.

    Args:
        extension: File extension including dot (e.g., '.py', '.js')

    Returns:
        Parser instance or None if extension not supported
    """
    return _PARSER_MAP.get(extension.lower())


__all__ = [
    "BaseParser",
    "ImportInfo",
    "FunctionInfo",
    "ClassInfo",
    "ParseResult",
    "ParseError",
    "ParseStats",
    "ParseErrorHandler",
    "DecoratorInfo",
    "AttributeInfo",
    "GlobalVariableInfo",
    "StructFieldInfo",
    "InterfaceMethodInfo",
    "StructInfo",
    "InterfaceInfo",
    "EnhancedFunctionInfo",
    "EnhancedClassInfo",
    "EnhancedParseResult",
    "PythonParser",
    "JsParser",
    "VueParser",
    "GoParser",
    "get_parser",
]
