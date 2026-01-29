"""Skeleton Extractor Service for code knowledge graph.

This module implements skeleton extraction from source code files,
supporting three modes: full, skeleton, and signature_only.

Feature: code-knowledge-graph-enhancement
"""

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

from ast_grep_py import SgRoot

from core.parsers import PythonParser, JsParser
from core.storage.sqlite import SQLiteStorage

logger = logging.getLogger(__name__)


class SkeletonMode(Enum):
    """Skeleton extraction mode.
    
    Defines the level of detail to include in the extracted skeleton.
    
    Attributes:
        FULL: Return complete file content (no extraction)
        SKELETON: Return signatures, docstrings, imports, and global variables
        SIGNATURE_ONLY: Return only function/class names and signatures
    """
    FULL = "full"
    SKELETON = "skeleton"
    SIGNATURE_ONLY = "signature_only"


@dataclass
class FunctionSkeleton:
    """Function skeleton information.
    
    Represents a function or method with its signature and metadata,
    without the implementation body.
    
    Attributes:
        name: Function name
        signature: Full function signature (def line)
        docstring: Documentation string if available
        start_line: Starting line number in source
        end_line: Ending line number in source
        is_async: Whether the function is async
        is_method: Whether this is a class method
    """
    name: str
    signature: str
    docstring: Optional[str] = None
    start_line: int = 0
    end_line: int = 0
    is_async: bool = False
    is_method: bool = False


@dataclass
class ClassSkeleton:
    """Class skeleton information.
    
    Represents a class or struct with its signature, attributes, and methods,
    without method implementation bodies.
    
    Attributes:
        name: Class/struct name
        signature: Class declaration line
        docstring: Documentation string if available
        attributes: List of class attribute definitions
        methods: List of method skeletons
        start_line: Starting line number in source
        end_line: Ending line number in source
        struct_tags: Go struct field tags (e.g., json:"name")
    """
    name: str
    signature: str
    docstring: Optional[str] = None
    attributes: list[str] = field(default_factory=list)
    methods: list[FunctionSkeleton] = field(default_factory=list)
    start_line: int = 0
    end_line: int = 0
    struct_tags: Optional[dict[str, str]] = None  # For Go structs


@dataclass
class SkeletonContent:
    """Complete skeleton content for a file.
    
    Contains all extracted skeleton information from a source file,
    organized by type (imports, globals, classes, functions).
    
    Attributes:
        file_path: Relative path to the source file
        language: Programming language (python, javascript, go, etc.)
        imports: List of import statement strings
        global_vars: List of global variable definition strings
        classes: List of class skeletons
        functions: List of top-level function skeletons
        raw_content: Original file content (for full mode)
    """
    file_path: str
    language: str = ""
    imports: list[str] = field(default_factory=list)
    global_vars: list[str] = field(default_factory=list)
    classes: list[ClassSkeleton] = field(default_factory=list)
    functions: list[FunctionSkeleton] = field(default_factory=list)
    raw_content: Optional[str] = None


class SkeletonExtractor:
    """Skeleton extractor service.
    
    Extracts code skeletons from source files, supporting multiple modes:
    - full: Returns complete file content
    - skeleton: Returns signatures, docstrings, imports, global variables
    - signature_only: Returns only function/class names and signatures
    
    Supports Python, JavaScript/TypeScript, and Go files.
    
    **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.9, 2.10**
    """
    
    # Language detection by file extension
    LANGUAGE_MAP = {
        ".py": "python",
        ".pyw": "python",
        ".js": "javascript",
        ".jsx": "javascript",
        ".mjs": "javascript",
        ".cjs": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".go": "go",
    }
    
    # Tree-sitter language names
    TREESITTER_LANG_MAP = {
        "python": "python",
        "javascript": "javascript",
        "typescript": "typescript",
        "go": "go",
    }
    
    def __init__(
        self,
        storage: Optional[SQLiteStorage] = None,
        project_root: Optional[Path] = None
    ):
        """Initialize skeleton extractor.
        
        Args:
            storage: Optional storage backend for accessing project data
            project_root: Optional project root path for reading files
        """
        self.storage = storage
        self.project_root = project_root
        self.parsers = {
            "python": PythonParser(),
            "javascript": JsParser(),
            "typescript": JsParser(),
        }

    def extract(
        self,
        file_path: str,
        mode: SkeletonMode = SkeletonMode.SKELETON,
        content: Optional[str] = None
    ) -> SkeletonContent:
        """Extract skeleton from a file.
        
        Args:
            file_path: Relative path to the file
            mode: Extraction mode (full, skeleton, signature_only)
            content: Optional file content (if not provided, reads from disk)
            
        Returns:
            SkeletonContent with extracted skeleton data
        """
        # Determine language from file extension
        ext = Path(file_path).suffix.lower()
        language = self.LANGUAGE_MAP.get(ext, "")
        
        # Read file content if not provided
        if content is None:
            if self.project_root:
                full_path = self.project_root / file_path
            else:
                full_path = Path(file_path)
            
            if not full_path.exists():
                return SkeletonContent(
                    file_path=file_path,
                    language=language
                )
            
            try:
                content = full_path.read_text(encoding="utf-8", errors="ignore")
            except Exception as e:
                logger.warning(f"Failed to read file {file_path}: {e}")
                return SkeletonContent(
                    file_path=file_path,
                    language=language
                )
        
        # Handle full mode - return raw content
        if mode == SkeletonMode.FULL:
            return self._extract_full(file_path, language, content)
        
        # Handle skeleton and signature_only modes
        if language == "python":
            return self._extract_python(file_path, content, mode)
        elif language in ("javascript", "typescript"):
            return self._extract_javascript(file_path, content, mode, language)
        elif language == "go":
            return self._extract_go(file_path, content, mode)
        else:
            # Unsupported language - return raw content
            return SkeletonContent(
                file_path=file_path,
                language=language,
                raw_content=content
            )

    def _extract_full(
        self,
        file_path: str,
        language: str,
        content: str
    ) -> SkeletonContent:
        """Extract full mode - return complete file content.
        
        **Validates: Requirement 2.1** - full mode returns complete content.
        
        Args:
            file_path: Relative path to the file
            language: Programming language
            content: File content
            
        Returns:
            SkeletonContent with raw_content set
        """
        return SkeletonContent(
            file_path=file_path,
            language=language,
            raw_content=content
        )
    
    def _extract_python(
        self,
        file_path: str,
        content: str,
        mode: SkeletonMode
    ) -> SkeletonContent:
        """Extract skeleton from Python file.
        
        **Validates: Requirements 2.2, 2.3, 2.4, 2.5, 2.9, 2.10**
        
        Args:
            file_path: Relative path to the file
            content: File content
            mode: Extraction mode
            
        Returns:
            SkeletonContent with extracted Python skeleton
        """
        skeleton = SkeletonContent(
            file_path=file_path,
            language="python"
        )
        
        try:
            root = SgRoot(content, "python")
            node = root.root()
            lines = content.split('\n')
            
            # Extract imports
            skeleton.imports = self._extract_python_imports(node, lines)
            
            # Extract global variables (only in skeleton mode)
            if mode == SkeletonMode.SKELETON:
                skeleton.global_vars = self._extract_python_globals(node, lines)
            
            # Extract classes
            for class_node in node.find_all(kind="class_definition"):
                class_skeleton = self._extract_python_class(class_node, lines, mode)
                if class_skeleton:
                    skeleton.classes.append(class_skeleton)
            
            # Extract top-level functions
            for func_node in node.find_all(kind="function_definition"):
                # Check if this is a top-level function
                parent = func_node.parent()
                if parent and parent.kind() not in ("class_definition", "block"):
                    func_skeleton = self._extract_python_function(func_node, lines, mode)
                    if func_skeleton:
                        skeleton.functions.append(func_skeleton)
                elif parent and parent.kind() == "block":
                    grandparent = parent.parent()
                    if grandparent and grandparent.kind() == "module":
                        func_skeleton = self._extract_python_function(func_node, lines, mode)
                        if func_skeleton:
                            skeleton.functions.append(func_skeleton)
            
        except Exception as e:
            logger.warning(f"Failed to parse Python file {file_path}: {e}")
        
        return skeleton

    def _extract_python_imports(
        self,
        node,
        lines: list[str]
    ) -> list[str]:
        """Extract Python import statements.
        
        **Validates: Requirement 2.9** - preserve import statements.
        
        Args:
            node: AST root node
            lines: Source code lines
            
        Returns:
            List of import statement strings
        """
        imports = []
        
        # Find 'import xxx' statements
        for imp in node.find_all(kind="import_statement"):
            line_num = imp.range().start.line
            if 0 <= line_num < len(lines):
                imports.append(lines[line_num].rstrip())
        
        # Find 'from xxx import yyy' statements
        for imp in node.find_all(kind="import_from_statement"):
            start_line = imp.range().start.line
            end_line = imp.range().end.line
            # Handle multi-line imports
            if start_line == end_line:
                if 0 <= start_line < len(lines):
                    imports.append(lines[start_line].rstrip())
            else:
                # Multi-line import
                import_lines = []
                for i in range(start_line, min(end_line + 1, len(lines))):
                    import_lines.append(lines[i].rstrip())
                imports.append('\n'.join(import_lines))
        
        return imports
    
    def _extract_python_globals(
        self,
        node,
        lines: list[str]
    ) -> list[str]:
        """Extract Python global variable definitions.
        
        **Validates: Requirement 2.10** - preserve global variable definitions.
        
        Args:
            node: AST root node
            lines: Source code lines
            
        Returns:
            List of global variable definition strings
        """
        globals_list = []
        
        # Find top-level assignments
        for child in node.children():
            if child.kind() == "expression_statement":
                # Check if it's an assignment
                assignment = child.find(kind="assignment")
                if assignment:
                    line_num = child.range().start.line
                    end_line = child.range().end.line
                    
                    if 0 <= line_num < len(lines):
                        if line_num == end_line:
                            var_def = lines[line_num].rstrip()
                        else:
                            # Multi-line assignment - truncate if too long
                            var_lines = []
                            for i in range(line_num, min(end_line + 1, len(lines))):
                                var_lines.append(lines[i].rstrip())
                            var_def = '\n'.join(var_lines)
                            # Truncate long literal values
                            if len(var_def) > 200:
                                var_def = var_def[:200] + " ..."
                        
                        globals_list.append(var_def)
        
        return globals_list

    def _extract_python_function(
        self,
        func_node,
        lines: list[str],
        mode: SkeletonMode
    ) -> Optional[FunctionSkeleton]:
        """Extract Python function skeleton.
        
        **Validates: Requirements 2.2, 2.3, 2.4**
        
        Args:
            func_node: Function AST node
            lines: Source code lines
            mode: Extraction mode
            
        Returns:
            FunctionSkeleton or None if extraction fails
        """
        try:
            # Get function name
            name_node = func_node.find(kind="identifier")
            if not name_node:
                return None
            name = name_node.text()
            
            # Get line numbers
            start_line = func_node.range().start.line + 1
            end_line = func_node.range().end.line + 1
            
            # Build signature
            signature = self._build_python_signature(func_node, lines, start_line)
            
            # Check if async
            is_async = signature.strip().startswith('async ')
            
            # Extract docstring (only in skeleton mode)
            docstring = None
            if mode == SkeletonMode.SKELETON:
                docstring = self._extract_python_docstring(func_node)
            
            return FunctionSkeleton(
                name=name,
                signature=signature,
                docstring=docstring,
                start_line=start_line,
                end_line=end_line,
                is_async=is_async,
                is_method=False
            )
        except Exception:
            return None
    
    def _build_python_signature(
        self,
        func_node,
        lines: list[str],
        start_line: int
    ) -> str:
        """Build Python function signature from AST node.
        
        Args:
            func_node: Function AST node
            lines: Source code lines
            start_line: 1-indexed start line
            
        Returns:
            Function signature string
        """
        # Get the first line of the function
        if start_line <= len(lines):
            signature_line = lines[start_line - 1].rstrip()
            
            # Check if signature spans multiple lines
            if not signature_line.rstrip().endswith(':'):
                sig_lines = [signature_line]
                for i in range(start_line, min(start_line + 10, len(lines))):
                    line = lines[i].rstrip()
                    sig_lines.append(line)
                    if ':' in line:
                        break
                signature_line = ' '.join(l.strip() for l in sig_lines)
            
            return signature_line
        
        return ""

    def _extract_python_docstring(self, node) -> Optional[str]:
        """Extract docstring from Python function or class.
        
        **Validates: Requirement 2.4** - preserve docstrings.
        
        Args:
            node: Function or class AST node
            
        Returns:
            Docstring text or None
        """
        try:
            block = node.find(kind="block")
            if not block:
                return None
            
            children = list(block.children())
            if not children:
                return None
            
            first = children[0]
            if first.kind() == "expression_statement":
                string = first.find(kind="string")
                if string:
                    text = string.text()
                    # Remove quotes
                    if text.startswith('"""') and text.endswith('"""'):
                        return text[3:-3].strip()
                    elif text.startswith("'''") and text.endswith("'''"):
                        return text[3:-3].strip()
                    elif text.startswith('"') and text.endswith('"'):
                        return text[1:-1].strip()
                    elif text.startswith("'") and text.endswith("'"):
                        return text[1:-1].strip()
        except Exception:
            pass
        return None
    
    def _extract_python_class(
        self,
        class_node,
        lines: list[str],
        mode: SkeletonMode
    ) -> Optional[ClassSkeleton]:
        """Extract Python class skeleton.
        
        **Validates: Requirements 2.2, 2.4, 2.5**
        
        Args:
            class_node: Class AST node
            lines: Source code lines
            mode: Extraction mode
            
        Returns:
            ClassSkeleton or None if extraction fails
        """
        try:
            # Get class name
            name_node = class_node.find(kind="identifier")
            if not name_node:
                return None
            name = name_node.text()
            
            # Get line numbers
            start_line = class_node.range().start.line + 1
            end_line = class_node.range().end.line + 1
            
            # Build signature
            if start_line <= len(lines):
                signature = lines[start_line - 1].rstrip()
            else:
                signature = f"class {name}:"
            
            # Extract docstring (only in skeleton mode)
            docstring = None
            if mode == SkeletonMode.SKELETON:
                docstring = self._extract_python_docstring(class_node)
            
            # Extract class attributes (only in skeleton mode)
            attributes = []
            if mode == SkeletonMode.SKELETON:
                attributes = self._extract_python_class_attributes(class_node, lines)
            
            # Extract methods
            methods = []
            for func_node in class_node.find_all(kind="function_definition"):
                # Only direct children (not nested functions)
                func_skeleton = self._extract_python_function(func_node, lines, mode)
                if func_skeleton:
                    func_skeleton.is_method = True
                    methods.append(func_skeleton)
            
            return ClassSkeleton(
                name=name,
                signature=signature,
                docstring=docstring,
                attributes=attributes,
                methods=methods,
                start_line=start_line,
                end_line=end_line
            )
        except Exception:
            return None

    def _extract_python_class_attributes(
        self,
        class_node,
        lines: list[str]
    ) -> list[str]:
        """Extract Python class attributes.
        
        **Validates: Requirement 2.5** - preserve class attributes and type annotations.
        
        Args:
            class_node: Class AST node
            lines: Source code lines
            
        Returns:
            List of attribute definition strings
        """
        attributes = []
        
        try:
            block = class_node.find(kind="block")
            if not block:
                return attributes
            
            for child in block.children():
                # Class-level assignments (class attributes)
                if child.kind() == "expression_statement":
                    assignment = child.find(kind="assignment")
                    if assignment:
                        line_num = child.range().start.line
                        if 0 <= line_num < len(lines):
                            attr_line = lines[line_num].rstrip()
                            attributes.append(attr_line)
                
                # Type annotations (e.g., name: str)
                elif child.kind() == "type_alias_statement":
                    line_num = child.range().start.line
                    if 0 <= line_num < len(lines):
                        attr_line = lines[line_num].rstrip()
                        attributes.append(attr_line)
        except Exception:
            pass
        
        return attributes

    def _extract_javascript(
        self,
        file_path: str,
        content: str,
        mode: SkeletonMode,
        language: str
    ) -> SkeletonContent:
        """Extract skeleton from JavaScript/TypeScript file.
        
        **Validates: Requirements 2.2, 2.3, 2.4, 2.5, 2.9, 2.10**
        
        Args:
            file_path: Relative path to the file
            content: File content
            mode: Extraction mode
            language: javascript or typescript
            
        Returns:
            SkeletonContent with extracted JS/TS skeleton
        """
        skeleton = SkeletonContent(
            file_path=file_path,
            language=language
        )
        
        try:
            ts_lang = "typescript" if language == "typescript" else "javascript"
            root = SgRoot(content, ts_lang)
            node = root.root()
            lines = content.split('\n')
            
            # Extract imports
            skeleton.imports = self._extract_js_imports(node, lines)
            
            # Extract global variables (only in skeleton mode)
            if mode == SkeletonMode.SKELETON:
                skeleton.global_vars = self._extract_js_globals(node, lines)
            
            # Extract classes
            for class_node in node.find_all(kind="class_declaration"):
                class_skeleton = self._extract_js_class(class_node, lines, mode)
                if class_skeleton:
                    skeleton.classes.append(class_skeleton)
            
            # Extract top-level functions
            for func_node in node.find_all(kind="function_declaration"):
                func_skeleton = self._extract_js_function(func_node, lines, mode)
                if func_skeleton:
                    skeleton.functions.append(func_skeleton)
            
            # Extract arrow functions assigned to variables
            for var_node in node.find_all(kind="lexical_declaration"):
                func_skeleton = self._extract_js_arrow_function(var_node, lines, mode)
                if func_skeleton:
                    skeleton.functions.append(func_skeleton)
            
        except Exception as e:
            logger.warning(f"Failed to parse JS/TS file {file_path}: {e}")
        
        return skeleton
    
    def _extract_js_imports(
        self,
        node,
        lines: list[str]
    ) -> list[str]:
        """Extract JavaScript/TypeScript import statements.
        
        Args:
            node: AST root node
            lines: Source code lines
            
        Returns:
            List of import statement strings
        """
        imports = []
        
        # ES6 imports
        for imp in node.find_all(kind="import_statement"):
            start_line = imp.range().start.line
            end_line = imp.range().end.line
            if start_line == end_line:
                if 0 <= start_line < len(lines):
                    imports.append(lines[start_line].rstrip())
            else:
                import_lines = []
                for i in range(start_line, min(end_line + 1, len(lines))):
                    import_lines.append(lines[i].rstrip())
                imports.append('\n'.join(import_lines))
        
        # CommonJS require
        for call in node.find_all(kind="call_expression"):
            func = call.find(kind="identifier")
            if func and func.text() == "require":
                parent = call.parent()
                if parent:
                    line_num = parent.range().start.line
                    if 0 <= line_num < len(lines):
                        imports.append(lines[line_num].rstrip())
        
        return imports

    def _extract_js_globals(
        self,
        node,
        lines: list[str]
    ) -> list[str]:
        """Extract JavaScript/TypeScript global variable definitions.
        
        Args:
            node: AST root node
            lines: Source code lines
            
        Returns:
            List of global variable definition strings
        """
        globals_list = []
        
        # Find top-level variable declarations
        for child in node.children():
            if child.kind() in ("lexical_declaration", "variable_declaration"):
                # Skip if it's an arrow function (handled separately)
                arrow = child.find(kind="arrow_function")
                if arrow:
                    continue
                
                line_num = child.range().start.line
                end_line = child.range().end.line
                
                if 0 <= line_num < len(lines):
                    if line_num == end_line:
                        var_def = lines[line_num].rstrip()
                    else:
                        var_lines = []
                        for i in range(line_num, min(end_line + 1, len(lines))):
                            var_lines.append(lines[i].rstrip())
                        var_def = '\n'.join(var_lines)
                        if len(var_def) > 200:
                            var_def = var_def[:200] + " ..."
                    
                    globals_list.append(var_def)
        
        return globals_list
    
    def _extract_js_function(
        self,
        func_node,
        lines: list[str],
        mode: SkeletonMode
    ) -> Optional[FunctionSkeleton]:
        """Extract JavaScript/TypeScript function skeleton.
        
        Args:
            func_node: Function AST node
            lines: Source code lines
            mode: Extraction mode
            
        Returns:
            FunctionSkeleton or None
        """
        try:
            # Get function name
            name_node = func_node.find(kind="identifier")
            if not name_node:
                return None
            name = name_node.text()
            
            # Get line numbers
            start_line = func_node.range().start.line + 1
            end_line = func_node.range().end.line + 1
            
            # Build signature (function declaration line)
            signature = self._build_js_signature(func_node, lines, start_line)
            
            # Check if async
            is_async = "async " in signature
            
            # Extract JSDoc comment (only in skeleton mode)
            docstring = None
            if mode == SkeletonMode.SKELETON:
                docstring = self._extract_js_jsdoc(func_node, lines, start_line)
            
            return FunctionSkeleton(
                name=name,
                signature=signature,
                docstring=docstring,
                start_line=start_line,
                end_line=end_line,
                is_async=is_async,
                is_method=False
            )
        except Exception:
            return None

    def _build_js_signature(
        self,
        func_node,
        lines: list[str],
        start_line: int
    ) -> str:
        """Build JavaScript function signature.
        
        Args:
            func_node: Function AST node
            lines: Source code lines
            start_line: 1-indexed start line
            
        Returns:
            Function signature string
        """
        if start_line <= len(lines):
            signature_line = lines[start_line - 1].rstrip()
            
            # Find the opening brace
            if '{' not in signature_line:
                sig_lines = [signature_line]
                for i in range(start_line, min(start_line + 5, len(lines))):
                    line = lines[i].rstrip()
                    sig_lines.append(line)
                    if '{' in line:
                        break
                signature_line = ' '.join(l.strip() for l in sig_lines)
            
            # Remove the body, keep only up to opening brace
            brace_idx = signature_line.find('{')
            if brace_idx > 0:
                signature_line = signature_line[:brace_idx].rstrip()
            
            return signature_line
        
        return ""
    
    def _extract_js_jsdoc(
        self,
        func_node,
        lines: list[str],
        start_line: int
    ) -> Optional[str]:
        """Extract JSDoc comment before a function.
        
        Args:
            func_node: Function AST node
            lines: Source code lines
            start_line: 1-indexed function start line
            
        Returns:
            JSDoc comment text or None
        """
        try:
            # Look for JSDoc comment in lines before the function
            jsdoc_lines = []
            in_jsdoc = False
            
            for i in range(start_line - 2, max(start_line - 20, -1), -1):
                if i < 0:
                    break
                line = lines[i].strip()
                
                if line.endswith('*/'):
                    in_jsdoc = True
                    jsdoc_lines.insert(0, line)
                elif in_jsdoc:
                    jsdoc_lines.insert(0, line)
                    if line.startswith('/**'):
                        break
                elif line and not line.startswith('//'):
                    break
            
            if jsdoc_lines:
                # Clean up JSDoc
                jsdoc = '\n'.join(jsdoc_lines)
                # Remove /** and */
                jsdoc = re.sub(r'/\*\*\s*', '', jsdoc)
                jsdoc = re.sub(r'\s*\*/', '', jsdoc)
                # Remove leading * from each line
                jsdoc = re.sub(r'^\s*\*\s?', '', jsdoc, flags=re.MULTILINE)
                return jsdoc.strip()
        except Exception:
            pass
        return None

    def _extract_js_arrow_function(
        self,
        var_node,
        lines: list[str],
        mode: SkeletonMode
    ) -> Optional[FunctionSkeleton]:
        """Extract arrow function assigned to a variable.
        
        Args:
            var_node: Variable declaration AST node
            lines: Source code lines
            mode: Extraction mode
            
        Returns:
            FunctionSkeleton or None
        """
        try:
            arrow = var_node.find(kind="arrow_function")
            if not arrow:
                return None
            
            # Get variable name
            name_node = var_node.find(kind="identifier")
            if not name_node:
                return None
            name = name_node.text()
            
            # Get line numbers
            start_line = var_node.range().start.line + 1
            end_line = var_node.range().end.line + 1
            
            # Build signature
            if start_line <= len(lines):
                signature_line = lines[start_line - 1].rstrip()
                # Find arrow and truncate after it
                arrow_idx = signature_line.find('=>')
                if arrow_idx > 0:
                    signature_line = signature_line[:arrow_idx + 2].rstrip()
            else:
                signature_line = f"const {name} = () =>"
            
            # Check if async
            is_async = "async " in signature_line
            
            # Extract JSDoc
            docstring = None
            if mode == SkeletonMode.SKELETON:
                docstring = self._extract_js_jsdoc(var_node, lines, start_line)
            
            return FunctionSkeleton(
                name=name,
                signature=signature_line,
                docstring=docstring,
                start_line=start_line,
                end_line=end_line,
                is_async=is_async,
                is_method=False
            )
        except Exception:
            return None
    
    def _extract_js_class(
        self,
        class_node,
        lines: list[str],
        mode: SkeletonMode
    ) -> Optional[ClassSkeleton]:
        """Extract JavaScript/TypeScript class skeleton.
        
        Args:
            class_node: Class AST node
            lines: Source code lines
            mode: Extraction mode
            
        Returns:
            ClassSkeleton or None
        """
        try:
            # Get class name
            name_node = class_node.find(kind="identifier")
            if not name_node:
                return None
            name = name_node.text()
            
            # Get line numbers
            start_line = class_node.range().start.line + 1
            end_line = class_node.range().end.line + 1
            
            # Build signature
            if start_line <= len(lines):
                signature = lines[start_line - 1].rstrip()
                brace_idx = signature.find('{')
                if brace_idx > 0:
                    signature = signature[:brace_idx].rstrip()
            else:
                signature = f"class {name}"
            
            # Extract JSDoc
            docstring = None
            if mode == SkeletonMode.SKELETON:
                docstring = self._extract_js_jsdoc(class_node, lines, start_line)
            
            # Extract class properties (only in skeleton mode)
            attributes = []
            if mode == SkeletonMode.SKELETON:
                attributes = self._extract_js_class_properties(class_node, lines)
            
            # Extract methods
            methods = []
            for method_node in class_node.find_all(kind="method_definition"):
                method_skeleton = self._extract_js_method(method_node, lines, mode)
                if method_skeleton:
                    methods.append(method_skeleton)
            
            return ClassSkeleton(
                name=name,
                signature=signature,
                docstring=docstring,
                attributes=attributes,
                methods=methods,
                start_line=start_line,
                end_line=end_line
            )
        except Exception:
            return None

    def _extract_js_class_properties(
        self,
        class_node,
        lines: list[str]
    ) -> list[str]:
        """Extract JavaScript/TypeScript class properties.
        
        Args:
            class_node: Class AST node
            lines: Source code lines
            
        Returns:
            List of property definition strings
        """
        properties = []
        
        try:
            body = class_node.find(kind="class_body")
            if not body:
                return properties
            
            for child in body.children():
                # Public field definitions
                if child.kind() in ("public_field_definition", "field_definition"):
                    line_num = child.range().start.line
                    if 0 <= line_num < len(lines):
                        prop_line = lines[line_num].rstrip()
                        properties.append(prop_line)
        except Exception:
            pass
        
        return properties
    
    def _extract_js_method(
        self,
        method_node,
        lines: list[str],
        mode: SkeletonMode
    ) -> Optional[FunctionSkeleton]:
        """Extract JavaScript/TypeScript method skeleton.
        
        Args:
            method_node: Method AST node
            lines: Source code lines
            mode: Extraction mode
            
        Returns:
            FunctionSkeleton or None
        """
        try:
            # Get method name
            name_node = method_node.find(kind="property_identifier")
            if not name_node:
                return None
            name = name_node.text()
            
            # Get line numbers
            start_line = method_node.range().start.line + 1
            end_line = method_node.range().end.line + 1
            
            # Build signature
            signature = self._build_js_signature(method_node, lines, start_line)
            
            # Check if async
            is_async = "async " in signature
            
            # Extract JSDoc
            docstring = None
            if mode == SkeletonMode.SKELETON:
                docstring = self._extract_js_jsdoc(method_node, lines, start_line)
            
            return FunctionSkeleton(
                name=name,
                signature=signature,
                docstring=docstring,
                start_line=start_line,
                end_line=end_line,
                is_async=is_async,
                is_method=True
            )
        except Exception:
            return None

    def _extract_go(
        self,
        file_path: str,
        content: str,
        mode: SkeletonMode
    ) -> SkeletonContent:
        """Extract skeleton from Go file.
        
        **Validates: Requirements 2.2, 2.3, 2.4, 2.5, 2.9, 2.10, 2.11, 2.12**
        
        Args:
            file_path: Relative path to the file
            content: File content
            mode: Extraction mode
            
        Returns:
            SkeletonContent with extracted Go skeleton
        """
        skeleton = SkeletonContent(
            file_path=file_path,
            language="go"
        )
        
        try:
            root = SgRoot(content, "go")
            node = root.root()
            lines = content.split('\n')
            
            # Extract imports
            skeleton.imports = self._extract_go_imports(node, lines)
            
            # Extract global variables (only in skeleton mode)
            if mode == SkeletonMode.SKELETON:
                skeleton.global_vars = self._extract_go_globals(node, lines)
            
            # Extract structs and interfaces
            structs = []
            for type_node in node.find_all(kind="type_declaration"):
                struct_skeleton = self._extract_go_type(type_node, lines, mode)
                if struct_skeleton:
                    structs.append(struct_skeleton)
            
            # Extract functions (including receiver functions)
            functions = []
            receiver_methods: dict[str, list[FunctionSkeleton]] = {}
            
            for func_node in node.find_all(kind="function_declaration"):
                func_skeleton = self._extract_go_function(func_node, lines, mode)
                if func_skeleton:
                    functions.append(func_skeleton)
            
            for method_node in node.find_all(kind="method_declaration"):
                method_skeleton, receiver_type = self._extract_go_method(
                    method_node, lines, mode
                )
                if method_skeleton and receiver_type:
                    if receiver_type not in receiver_methods:
                        receiver_methods[receiver_type] = []
                    receiver_methods[receiver_type].append(method_skeleton)
            
            # Aggregate methods to structs
            skeleton.classes = self._aggregate_go_methods(structs, receiver_methods)
            skeleton.functions = functions
            
        except Exception as e:
            logger.warning(f"Failed to parse Go file {file_path}: {e}")
        
        return skeleton
    
    def _extract_go_imports(
        self,
        node,
        lines: list[str]
    ) -> list[str]:
        """Extract Go import statements.
        
        Args:
            node: AST root node
            lines: Source code lines
            
        Returns:
            List of import statement strings
        """
        imports = []
        
        for imp in node.find_all(kind="import_declaration"):
            start_line = imp.range().start.line
            end_line = imp.range().end.line
            
            if start_line == end_line:
                if 0 <= start_line < len(lines):
                    imports.append(lines[start_line].rstrip())
            else:
                import_lines = []
                for i in range(start_line, min(end_line + 1, len(lines))):
                    import_lines.append(lines[i].rstrip())
                imports.append('\n'.join(import_lines))
        
        return imports

    def _extract_go_globals(
        self,
        node,
        lines: list[str]
    ) -> list[str]:
        """Extract Go global variable definitions.
        
        Args:
            node: AST root node
            lines: Source code lines
            
        Returns:
            List of global variable definition strings
        """
        globals_list = []
        
        # Find var declarations
        for var_node in node.find_all(kind="var_declaration"):
            start_line = var_node.range().start.line
            end_line = var_node.range().end.line
            
            if 0 <= start_line < len(lines):
                if start_line == end_line:
                    var_def = lines[start_line].rstrip()
                else:
                    var_lines = []
                    for i in range(start_line, min(end_line + 1, len(lines))):
                        var_lines.append(lines[i].rstrip())
                    var_def = '\n'.join(var_lines)
                    if len(var_def) > 200:
                        var_def = var_def[:200] + " ..."
                
                globals_list.append(var_def)
        
        # Find const declarations
        for const_node in node.find_all(kind="const_declaration"):
            start_line = const_node.range().start.line
            end_line = const_node.range().end.line
            
            if 0 <= start_line < len(lines):
                if start_line == end_line:
                    const_def = lines[start_line].rstrip()
                else:
                    const_lines = []
                    for i in range(start_line, min(end_line + 1, len(lines))):
                        const_lines.append(lines[i].rstrip())
                    const_def = '\n'.join(const_lines)
                    if len(const_def) > 200:
                        const_def = const_def[:200] + " ..."
                
                globals_list.append(const_def)
        
        return globals_list
    
    def _extract_go_type(
        self,
        type_node,
        lines: list[str],
        mode: SkeletonMode
    ) -> Optional[ClassSkeleton]:
        """Extract Go struct or interface definition.
        
        **Validates: Requirements 2.5, 2.12** - preserve struct fields and tags.
        
        Args:
            type_node: Type declaration AST node
            lines: Source code lines
            mode: Extraction mode
            
        Returns:
            ClassSkeleton or None
        """
        try:
            # Get type name
            name_node = type_node.find(kind="type_identifier")
            if not name_node:
                return None
            name = name_node.text()
            
            # Get line numbers
            start_line = type_node.range().start.line + 1
            end_line = type_node.range().end.line + 1
            
            # Determine if struct or interface
            struct_type = type_node.find(kind="struct_type")
            interface_type = type_node.find(kind="interface_type")
            
            # Build signature and extract attributes
            attributes = []
            struct_tags = {}
            
            if struct_type:
                signature = f"type {name} struct"
                if mode == SkeletonMode.SKELETON:
                    attributes, struct_tags = self._extract_go_struct_fields(
                        struct_type, lines
                    )
            elif interface_type:
                signature = f"type {name} interface"
                if mode == SkeletonMode.SKELETON:
                    attributes = self._extract_go_interface_methods(
                        interface_type, lines
                    )
            else:
                # Type alias
                if start_line <= len(lines):
                    signature = lines[start_line - 1].rstrip()
                else:
                    signature = f"type {name}"
            
            # Extract doc comment
            docstring = None
            if mode == SkeletonMode.SKELETON:
                docstring = self._extract_go_doc_comment(type_node, lines, start_line)
            
            return ClassSkeleton(
                name=name,
                signature=signature,
                docstring=docstring,
                attributes=attributes,
                methods=[],  # Methods will be aggregated later
                start_line=start_line,
                end_line=end_line,
                struct_tags=struct_tags if struct_tags else None
            )
        except Exception:
            return None

    def _extract_go_struct_fields(
        self,
        struct_node,
        lines: list[str]
    ) -> tuple[list[str], dict[str, str]]:
        """Extract Go struct fields and tags.
        
        **Validates: Requirement 2.12** - preserve struct tags.
        
        Args:
            struct_node: Struct type AST node
            lines: Source code lines
            
        Returns:
            Tuple of (field definitions, struct tags dict)
        """
        fields = []
        tags = {}
        
        try:
            for field in struct_node.find_all(kind="field_declaration"):
                line_num = field.range().start.line
                if 0 <= line_num < len(lines):
                    field_line = lines[line_num].rstrip()
                    fields.append(field_line)
                    
                    # Extract struct tag
                    tag_node = field.find(kind="raw_string_literal")
                    if tag_node:
                        tag_text = tag_node.text()
                        # Parse tag (e.g., `json:"name"`)
                        name_node = field.find(kind="field_identifier")
                        if name_node:
                            field_name = name_node.text()
                            tags[field_name] = tag_text
        except Exception:
            pass
        
        return fields, tags
    
    def _extract_go_interface_methods(
        self,
        interface_node,
        lines: list[str]
    ) -> list[str]:
        """Extract Go interface method signatures.
        
        Args:
            interface_node: Interface type AST node
            lines: Source code lines
            
        Returns:
            List of method signature strings
        """
        methods = []
        
        try:
            for method in interface_node.find_all(kind="method_spec"):
                line_num = method.range().start.line
                if 0 <= line_num < len(lines):
                    method_line = lines[line_num].rstrip()
                    methods.append(method_line)
        except Exception:
            pass
        
        return methods
    
    def _extract_go_doc_comment(
        self,
        node,
        lines: list[str],
        start_line: int
    ) -> Optional[str]:
        """Extract Go doc comment before a declaration.
        
        Args:
            node: AST node
            lines: Source code lines
            start_line: 1-indexed declaration start line
            
        Returns:
            Doc comment text or None
        """
        try:
            doc_lines = []
            
            for i in range(start_line - 2, max(start_line - 20, -1), -1):
                if i < 0:
                    break
                line = lines[i].strip()
                
                if line.startswith('//'):
                    doc_lines.insert(0, line[2:].strip())
                elif line:
                    break
            
            if doc_lines:
                return '\n'.join(doc_lines)
        except Exception:
            pass
        return None

    def _extract_go_function(
        self,
        func_node,
        lines: list[str],
        mode: SkeletonMode
    ) -> Optional[FunctionSkeleton]:
        """Extract Go function skeleton.
        
        Args:
            func_node: Function declaration AST node
            lines: Source code lines
            mode: Extraction mode
            
        Returns:
            FunctionSkeleton or None
        """
        try:
            # Get function name
            name_node = func_node.find(kind="identifier")
            if not name_node:
                return None
            name = name_node.text()
            
            # Get line numbers
            start_line = func_node.range().start.line + 1
            end_line = func_node.range().end.line + 1
            
            # Build signature
            signature = self._build_go_signature(func_node, lines, start_line)
            
            # Extract doc comment
            docstring = None
            if mode == SkeletonMode.SKELETON:
                docstring = self._extract_go_doc_comment(func_node, lines, start_line)
            
            return FunctionSkeleton(
                name=name,
                signature=signature,
                docstring=docstring,
                start_line=start_line,
                end_line=end_line,
                is_async=False,
                is_method=False
            )
        except Exception:
            return None
    
    def _extract_go_method(
        self,
        method_node,
        lines: list[str],
        mode: SkeletonMode
    ) -> tuple[Optional[FunctionSkeleton], Optional[str]]:
        """Extract Go method (receiver function) skeleton.
        
        **Validates: Requirement 2.11** - aggregate receiver functions to structs.
        
        Args:
            method_node: Method declaration AST node
            lines: Source code lines
            mode: Extraction mode
            
        Returns:
            Tuple of (FunctionSkeleton, receiver_type) or (None, None)
        """
        try:
            # Get method name
            name_node = method_node.find(kind="field_identifier")
            if not name_node:
                return None, None
            name = name_node.text()
            
            # Get receiver type
            receiver_type = self._get_go_receiver_type(method_node)
            
            # Get line numbers
            start_line = method_node.range().start.line + 1
            end_line = method_node.range().end.line + 1
            
            # Build signature
            signature = self._build_go_signature(method_node, lines, start_line)
            
            # Extract doc comment
            docstring = None
            if mode == SkeletonMode.SKELETON:
                docstring = self._extract_go_doc_comment(method_node, lines, start_line)
            
            func_skeleton = FunctionSkeleton(
                name=name,
                signature=signature,
                docstring=docstring,
                start_line=start_line,
                end_line=end_line,
                is_async=False,
                is_method=True
            )
            
            return func_skeleton, receiver_type
        except Exception:
            return None, None

    def _get_go_receiver_type(self, method_node) -> Optional[str]:
        """Get the receiver type from a Go method declaration.
        
        Args:
            method_node: Method declaration AST node
            
        Returns:
            Receiver type name (without pointer) or None
        """
        try:
            # Find parameter list (receiver)
            params = method_node.find(kind="parameter_list")
            if not params:
                return None
            
            # Get the type identifier
            type_id = params.find(kind="type_identifier")
            if type_id:
                return type_id.text()
            
            # Handle pointer receiver (*Type)
            pointer = params.find(kind="pointer_type")
            if pointer:
                type_id = pointer.find(kind="type_identifier")
                if type_id:
                    return type_id.text()
        except Exception:
            pass
        return None
    
    def _build_go_signature(
        self,
        func_node,
        lines: list[str],
        start_line: int
    ) -> str:
        """Build Go function/method signature.
        
        Args:
            func_node: Function/method AST node
            lines: Source code lines
            start_line: 1-indexed start line
            
        Returns:
            Function signature string
        """
        if start_line <= len(lines):
            signature_line = lines[start_line - 1].rstrip()
            
            # Find the opening brace
            if '{' not in signature_line:
                sig_lines = [signature_line]
                for i in range(start_line, min(start_line + 5, len(lines))):
                    line = lines[i].rstrip()
                    sig_lines.append(line)
                    if '{' in line:
                        break
                signature_line = ' '.join(l.strip() for l in sig_lines)
            
            # Remove the body, keep only up to opening brace
            brace_idx = signature_line.find('{')
            if brace_idx > 0:
                signature_line = signature_line[:brace_idx].rstrip()
            
            return signature_line
        
        return ""
    
    def _aggregate_go_methods(
        self,
        structs: list[ClassSkeleton],
        receiver_methods: dict[str, list[FunctionSkeleton]]
    ) -> list[ClassSkeleton]:
        """Aggregate Go receiver methods to their corresponding structs.
        
        **Validates: Requirement 2.11** - aggregate receiver functions to structs.
        
        Args:
            structs: List of struct/interface skeletons
            receiver_methods: Dict mapping receiver type to methods
            
        Returns:
            List of ClassSkeleton with methods aggregated
        """
        for struct in structs:
            if struct.name in receiver_methods:
                struct.methods.extend(receiver_methods[struct.name])
        
        return structs

    def to_string(
        self,
        skeleton: SkeletonContent,
        mode: SkeletonMode = SkeletonMode.SKELETON
    ) -> str:
        """Convert skeleton content to string representation.
        
        **Validates: Requirement 2.7** - maintain code indentation and formatting.
        
        Args:
            skeleton: SkeletonContent to convert
            mode: Extraction mode for formatting
            
        Returns:
            String representation of the skeleton
        """
        # Full mode - return raw content
        if mode == SkeletonMode.FULL and skeleton.raw_content:
            return skeleton.raw_content
        
        # Build skeleton string
        parts = []
        
        # Add imports
        if skeleton.imports:
            parts.extend(skeleton.imports)
            parts.append("")  # Empty line after imports
        
        # Add global variables (only in skeleton mode)
        if mode == SkeletonMode.SKELETON and skeleton.global_vars:
            parts.extend(skeleton.global_vars)
            parts.append("")
        
        # Add classes/structs
        for cls in skeleton.classes:
            parts.append(self._class_to_string(cls, skeleton.language, mode))
            parts.append("")
        
        # Add functions
        for func in skeleton.functions:
            parts.append(self._function_to_string(func, skeleton.language, mode))
            parts.append("")
        
        return '\n'.join(parts).rstrip()
    
    def _function_to_string(
        self,
        func: FunctionSkeleton,
        language: str,
        mode: SkeletonMode
    ) -> str:
        """Convert function skeleton to string.
        
        Args:
            func: FunctionSkeleton to convert
            language: Programming language
            mode: Extraction mode
            
        Returns:
            String representation
        """
        parts = []
        
        # Add docstring (only in skeleton mode)
        if mode == SkeletonMode.SKELETON and func.docstring:
            if language == "python":
                parts.append(f'    """{func.docstring}"""' if func.is_method else f'"""{func.docstring}"""')
            elif language in ("javascript", "typescript"):
                parts.append(f"/** {func.docstring} */")
            elif language == "go":
                for line in func.docstring.split('\n'):
                    parts.append(f"// {line}")
        
        # Add signature
        parts.append(func.signature)
        
        # Add body placeholder (only in skeleton mode)
        if mode == SkeletonMode.SKELETON:
            if language == "python":
                indent = "        " if func.is_method else "    "
                if func.docstring:
                    parts.append(f"{indent}...")
                else:
                    parts.append(f"{indent}...")
            elif language in ("javascript", "typescript"):
                parts.append(" { ... }")
            elif language == "go":
                parts.append(" { ... }")
        
        return '\n'.join(parts)

    def _class_to_string(
        self,
        cls: ClassSkeleton,
        language: str,
        mode: SkeletonMode
    ) -> str:
        """Convert class skeleton to string.
        
        Args:
            cls: ClassSkeleton to convert
            language: Programming language
            mode: Extraction mode
            
        Returns:
            String representation
        """
        parts = []
        
        # Add docstring (only in skeleton mode)
        if mode == SkeletonMode.SKELETON and cls.docstring:
            if language == "python":
                parts.append(f'"""{cls.docstring}"""')
            elif language in ("javascript", "typescript"):
                parts.append(f"/** {cls.docstring} */")
            elif language == "go":
                for line in cls.docstring.split('\n'):
                    parts.append(f"// {line}")
        
        # Add signature
        parts.append(cls.signature)
        
        # Add attributes (only in skeleton mode)
        if mode == SkeletonMode.SKELETON and cls.attributes:
            if language == "python":
                # Python class docstring comes after signature
                if cls.docstring:
                    parts.append(f'    """{cls.docstring}"""')
                for attr in cls.attributes:
                    parts.append(f"    {attr.strip()}")
            elif language in ("javascript", "typescript"):
                parts.append(" {")
                for attr in cls.attributes:
                    parts.append(f"    {attr.strip()}")
            elif language == "go":
                parts.append(" {")
                for attr in cls.attributes:
                    parts.append(f"    {attr.strip()}")
                parts.append("}")
        
        # Add methods
        if cls.methods:
            if language == "python":
                for method in cls.methods:
                    method_str = self._function_to_string(method, language, mode)
                    # Indent method
                    indented = '\n'.join(
                        f"    {line}" if line.strip() else line
                        for line in method_str.split('\n')
                    )
                    parts.append(indented)
            elif language in ("javascript", "typescript"):
                if not cls.attributes:
                    parts.append(" {")
                for method in cls.methods:
                    method_str = self._function_to_string(method, language, mode)
                    parts.append(f"    {method_str}")
                parts.append("}")
            elif language == "go":
                # Go methods are shown after struct definition
                parts.append("")
                for method in cls.methods:
                    method_str = self._function_to_string(method, language, mode)
                    parts.append(method_str)
        elif language in ("javascript", "typescript") and cls.attributes:
            parts.append("}")
        
        return '\n'.join(parts)
