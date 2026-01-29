"""Python import and function parser using ast-grep."""

import logging
from pathlib import Path
from ast_grep_py import SgRoot
from typing import Optional

from .base import (
    BaseParser, ImportInfo, FunctionInfo, ClassInfo, ParseResult, ParseError,
    DecoratorInfo, AttributeInfo, GlobalVariableInfo, EnhancedFunctionInfo,
    EnhancedClassInfo, EnhancedParseResult
)

logger = logging.getLogger("code_knowledge_graph.parser.python")


class PythonParser(BaseParser):
    """Parser for Python files."""

    supported_extensions = [".py", ".pyw"]

    def parse(self, content: str, file_path: Path) -> list[ImportInfo]:
        """Parse Python source and extract imports."""
        imports: list[ImportInfo] = []

        try:
            root = SgRoot(content, "python")
            node = root.root()

            # Find 'import xxx' statements
            for imp in node.find_all(kind="import_statement"):
                self._extract_import_statement(imp, imports)

            # Find 'from xxx import yyy' statements
            for imp in node.find_all(kind="import_from_statement"):
                self._extract_from_import(imp, imports)

            logger.debug(f"Parsed {file_path}: found {len(imports)} imports")

        except Exception as e:
            logger.warning(f"Failed to parse {file_path}: {type(e).__name__}: {e}")

        return imports

    def parse_full(self, content: str, file_path: Path) -> ParseResult:
        """Parse Python source and extract all information."""
        result = ParseResult()

        try:
            root = SgRoot(content, "python")
            node = root.root()

            # Extract imports
            for imp in node.find_all(kind="import_statement"):
                self._extract_import_statement(imp, result.imports)
            for imp in node.find_all(kind="import_from_statement"):
                self._extract_from_import(imp, result.imports)

            # Extract classes
            for class_node in node.find_all(kind="class_definition"):
                class_info = self._extract_class(class_node, content)
                if class_info:
                    result.classes.append(class_info)

            # Extract top-level functions (not methods)
            for func_node in node.find_all(kind="function_definition"):
                # Check if this is a top-level function (not inside a class)
                parent = func_node.parent()
                if parent and parent.kind() not in ("class_definition", "block"):
                    func_info = self._extract_function(func_node, content)
                    if func_info:
                        result.functions.append(func_info)
                elif parent and parent.kind() == "block":
                    # Check if the block's parent is module (top-level)
                    grandparent = parent.parent()
                    if grandparent and grandparent.kind() == "module":
                        func_info = self._extract_function(func_node, content)
                        if func_info:
                            result.functions.append(func_info)

            logger.debug(
                f"Parsed {file_path}: {len(result.imports)} imports, "
                f"{len(result.functions)} functions, {len(result.classes)} classes"
            )

        except Exception as e:
            logger.warning(f"Failed to parse {file_path}: {type(e).__name__}: {e}")

        return result

    def parse_enhanced(self, content: str, file_path: Path) -> EnhancedParseResult:
        """Parse Python source and extract enhanced information including decorators, attributes, and global variables."""
        result = EnhancedParseResult()

        try:
            root = SgRoot(content, "python")
            node = root.root()

            # Extract imports
            for imp in node.find_all(kind="import_statement"):
                self._extract_import_statement(imp, result.imports)
            for imp in node.find_all(kind="import_from_statement"):
                self._extract_from_import(imp, result.imports)

            # Extract global variables (module-level assignments)
            result.global_variables = self._extract_global_variables(node, content)

            # Extract classes with enhanced info (decorators and attributes)
            for class_node in node.find_all(kind="class_definition"):
                class_info = self._extract_enhanced_class(class_node, content)
                if class_info:
                    result.classes.append(class_info)

            # Extract top-level functions with decorators
            # First, find decorated definitions
            decorated_funcs = set()
            for decorated_node in node.find_all(kind="decorated_definition"):
                func_node = decorated_node.find(kind="function_definition")
                if func_node:
                    func_info = self._extract_enhanced_function(decorated_node, func_node, content)
                    if func_info:
                        result.functions.append(func_info)
                        decorated_funcs.add(func_node.range().start.line)

            # Then find non-decorated top-level functions
            for func_node in node.find_all(kind="function_definition"):
                # Skip if already processed as decorated
                if func_node.range().start.line in decorated_funcs:
                    continue
                # Check if this is a top-level function (not inside a class)
                parent = func_node.parent()
                if parent and parent.kind() not in ("class_definition", "block"):
                    func_info = self._extract_function(func_node, content)
                    if func_info:
                        result.functions.append(func_info)
                elif parent and parent.kind() == "block":
                    # Check if the block's parent is module (top-level)
                    grandparent = parent.parent()
                    if grandparent and grandparent.kind() == "module":
                        func_info = self._extract_function(func_node, content)
                        if func_info:
                            result.functions.append(func_info)

            logger.debug(
                f"Enhanced parse {file_path}: {len(result.imports)} imports, "
                f"{len(result.functions)} functions, {len(result.classes)} classes, "
                f"{len(result.global_variables)} global variables"
            )

        except Exception as e:
            logger.warning(f"Failed to parse {file_path}: {type(e).__name__}: {e}")

        return result

    def _extract_decorators(self, decorated_node) -> list[DecoratorInfo]:
        """Extract decorators from a decorated_definition node."""
        decorators = []
        try:
            for decorator in decorated_node.find_all(kind="decorator"):
                line = decorator.range().start.line + 1
                
                # Get decorator text and parse it
                dec_text = decorator.text()
                
                # Remove the @ symbol
                if dec_text.startswith("@"):
                    dec_text = dec_text[1:].strip()
                
                # Check if it's a call (has arguments)
                call_node = decorator.find(kind="call")
                if call_node:
                    # Get the function being called
                    func_part = call_node.find(kind="identifier")
                    attr_part = call_node.find(kind="attribute")
                    
                    if attr_part:
                        name = attr_part.text()
                    elif func_part:
                        name = func_part.text()
                    else:
                        name = dec_text.split("(")[0]
                    
                    # Extract arguments
                    args = []
                    arg_list = call_node.find(kind="argument_list")
                    if arg_list:
                        for child in arg_list.children():
                            if child.kind() not in ("(", ")", ","):
                                args.append(child.text())
                    
                    decorators.append(DecoratorInfo(
                        name=name,
                        arguments=args,
                        line=line
                    ))
                else:
                    # Simple decorator without arguments
                    identifier = decorator.find(kind="identifier")
                    attr = decorator.find(kind="attribute")
                    
                    if attr:
                        name = attr.text()
                    elif identifier:
                        name = identifier.text()
                    else:
                        name = dec_text
                    
                    decorators.append(DecoratorInfo(
                        name=name,
                        arguments=[],
                        line=line
                    ))
        except Exception as e:
            logger.debug(f"Error extracting decorators: {e}")
        
        return decorators

    def _extract_enhanced_function(self, decorated_node, func_node, content: str) -> EnhancedFunctionInfo | None:
        """Extract enhanced function information including decorators."""
        try:
            # Get basic function info
            basic_info = self._extract_function(func_node, content)
            if not basic_info:
                return None
            
            # Extract decorators
            decorators = self._extract_decorators(decorated_node)
            
            return EnhancedFunctionInfo(
                name=basic_info.name,
                signature=basic_info.signature,
                start_line=decorated_node.range().start.line + 1,  # Include decorator lines
                end_line=basic_info.end_line,
                calls=basic_info.calls,
                is_method=basic_info.is_method,
                is_async=basic_info.is_async,
                docstring=basic_info.docstring,
                decorators=decorators
            )
        except Exception:
            return None

    def _extract_class_attributes(self, class_node, content: str) -> list[AttributeInfo]:
        """Extract class attributes and type annotations from a class."""
        attributes = []
        try:
            # Find the class body block
            block = class_node.find(kind="block")
            if not block:
                return attributes
            
            lines = content.split('\n')
            
            # Look for typed assignments (class-level type annotations)
            # e.g., name: str = "default" or name: str
            for typed_node in block.find_all(kind="expression_statement"):
                # Check for type annotation
                assignment = typed_node.find(kind="assignment")
                if assignment:
                    # Check if it's a class-level assignment (not inside a method)
                    parent = typed_node.parent()
                    if parent and parent.kind() == "block":
                        grandparent = parent.parent()
                        if grandparent and grandparent.kind() == "class_definition":
                            # This is a class-level assignment
                            left = assignment.find(kind="identifier")
                            if left:
                                name = left.text()
                                line = typed_node.range().start.line + 1
                                
                                # Get the full line for type annotation
                                line_text = lines[line - 1].strip() if line <= len(lines) else ""
                                
                                # Parse type annotation if present
                                type_annotation = None
                                default_value = None
                                
                                if ":" in line_text:
                                    # Has type annotation
                                    parts = line_text.split(":", 1)
                                    if len(parts) > 1:
                                        type_part = parts[1].strip()
                                        if "=" in type_part:
                                            type_annotation = type_part.split("=")[0].strip()
                                            default_value = type_part.split("=", 1)[1].strip()
                                        else:
                                            type_annotation = type_part
                                elif "=" in line_text:
                                    # No type annotation, just assignment
                                    default_value = line_text.split("=", 1)[1].strip()
                                
                                # Check if it's a ClassVar
                                is_class_var = type_annotation and "ClassVar" in type_annotation
                                
                                attributes.append(AttributeInfo(
                                    name=name,
                                    type_annotation=type_annotation,
                                    default_value=default_value,
                                    line=line,
                                    is_class_var=is_class_var
                                ))
            
            # Also look for annotated assignments (type: annotation = value)
            for typed_node in block.find_all(kind="type"):
                parent = typed_node.parent()
                if parent and parent.kind() == "expression_statement":
                    # Check if it's class-level
                    gparent = parent.parent()
                    if gparent and gparent.kind() == "block":
                        ggparent = gparent.parent()
                        if ggparent and ggparent.kind() == "class_definition":
                            line = typed_node.range().start.line + 1
                            line_text = lines[line - 1].strip() if line <= len(lines) else ""
                            
                            # Parse the annotation
                            if ":" in line_text:
                                name = line_text.split(":")[0].strip()
                                type_part = line_text.split(":", 1)[1].strip()
                                
                                type_annotation = None
                                default_value = None
                                
                                if "=" in type_part:
                                    type_annotation = type_part.split("=")[0].strip()
                                    default_value = type_part.split("=", 1)[1].strip()
                                else:
                                    type_annotation = type_part
                                
                                # Avoid duplicates
                                if not any(a.name == name and a.line == line for a in attributes):
                                    is_class_var = type_annotation and "ClassVar" in type_annotation
                                    attributes.append(AttributeInfo(
                                        name=name,
                                        type_annotation=type_annotation,
                                        default_value=default_value,
                                        line=line,
                                        is_class_var=is_class_var
                                    ))
        except Exception as e:
            logger.debug(f"Error extracting class attributes: {e}")
        
        return attributes

    def _extract_enhanced_class(self, class_node, content: str) -> EnhancedClassInfo | None:
        """Extract enhanced class information including decorators and attributes."""
        try:
            # Check if this class is decorated
            parent = class_node.parent()
            decorators = []
            start_line = class_node.range().start.line + 1
            
            if parent and parent.kind() == "decorated_definition":
                decorators = self._extract_decorators(parent)
                start_line = parent.range().start.line + 1
            
            # Get basic class info
            basic_info = self._extract_class(class_node, content)
            if not basic_info:
                return None
            
            # Extract class attributes
            attributes = self._extract_class_attributes(class_node, content)
            
            return EnhancedClassInfo(
                name=basic_info.name,
                signature=basic_info.signature,
                start_line=start_line,
                end_line=basic_info.end_line,
                methods=basic_info.methods,
                bases=basic_info.bases,
                docstring=basic_info.docstring,
                decorators=decorators,
                attributes=attributes
            )
        except Exception:
            return None

    def _extract_global_variables(self, root_node, content: str) -> list[GlobalVariableInfo]:
        """Extract global/module-level variable definitions."""
        global_vars = []
        try:
            lines = content.split('\n')
            
            # Find all expression statements at module level
            for child in root_node.children():
                if child.kind() == "expression_statement":
                    # Check for assignment
                    assignment = child.find(kind="assignment")
                    if assignment:
                        # Get the left side (variable name)
                        left = assignment.find(kind="identifier")
                        if left:
                            name = left.text()
                            line = child.range().start.line + 1
                            line_text = lines[line - 1].strip() if line <= len(lines) else ""
                            
                            type_annotation = None
                            value = None
                            
                            # Check for type annotation
                            if ":" in line_text.split("=")[0]:
                                parts = line_text.split(":", 1)
                                if len(parts) > 1:
                                    type_part = parts[1].strip()
                                    if "=" in type_part:
                                        type_annotation = type_part.split("=")[0].strip()
                                        value = type_part.split("=", 1)[1].strip()
                                    else:
                                        type_annotation = type_part
                            elif "=" in line_text:
                                value = line_text.split("=", 1)[1].strip()
                            
                            # Truncate long values
                            if value and len(value) > 100:
                                value = value[:100] + "..."
                            
                            global_vars.append(GlobalVariableInfo(
                                name=name,
                                type_annotation=type_annotation,
                                value=value,
                                line=line
                            ))
                    
                    # Also check for annotated assignments without value
                    # e.g., MY_VAR: int
                    elif ":" in child.text() and "=" not in child.text():
                        line = child.range().start.line + 1
                        line_text = lines[line - 1].strip() if line <= len(lines) else ""
                        
                        if ":" in line_text:
                            name = line_text.split(":")[0].strip()
                            type_annotation = line_text.split(":", 1)[1].strip()
                            
                            global_vars.append(GlobalVariableInfo(
                                name=name,
                                type_annotation=type_annotation,
                                value=None,
                                line=line
                            ))
        except Exception as e:
            logger.debug(f"Error extracting global variables: {e}")
        
        return global_vars

    def _extract_import_statement(self, node, imports: list[ImportInfo]) -> None:
        """Extract module names from 'import xxx' statement."""
        # Find dotted_name or aliased_import children
        for child in node.children():
            if child.kind() == "dotted_name":
                module = child.text()
                imports.append(ImportInfo(
                    module=module,
                    import_type="static",
                    line=child.range().start.line + 1
                ))
            elif child.kind() == "aliased_import":
                # import xxx as yyy
                dotted = child.find(kind="dotted_name")
                if dotted:
                    imports.append(ImportInfo(
                        module=dotted.text(),
                        import_type="static",
                        line=child.range().start.line + 1
                    ))

    def _extract_from_import(self, node, imports: list[ImportInfo]) -> None:
        """Extract module name from 'from xxx import yyy' statement."""
        # The module name is in dotted_name or relative_import
        text = node.text()
        line = node.range().start.line + 1

        # Handle relative imports: from . import xxx or from .foo import xxx
        if "from ." in text:
            # Extract the relative module path
            # from . import x -> "."
            # from .foo import x -> ".foo"
            # from ..bar import x -> "..bar"
            parts = text.split("import")[0].strip()
            module = parts.replace("from", "").strip()
            imports.append(ImportInfo(
                module=module,
                import_type="static",
                line=line
            ))
        else:
            # Absolute import: from xxx import yyy
            dotted = node.find(kind="dotted_name")
            if dotted:
                imports.append(ImportInfo(
                    module=dotted.text(),
                    import_type="static",
                    line=line
                ))

    def _extract_function(self, node, content: str) -> FunctionInfo | None:
        """Extract function information from a function_definition node."""
        try:
            # Get function name
            name_node = node.find(kind="identifier")
            if not name_node:
                return None
            name = name_node.text()

            # Get line numbers
            start_line = node.range().start.line + 1
            end_line = node.range().end.line + 1

            # Build signature (first line of function)
            lines = content.split('\n')
            signature_line = lines[start_line - 1].strip() if start_line <= len(lines) else ""

            # Remove the body, keep only the def line
            if signature_line.endswith(':'):
                signature = signature_line
            else:
                # Multi-line signature, find the colon
                sig_lines = []
                for i in range(start_line - 1, min(start_line + 5, len(lines))):
                    sig_lines.append(lines[i].strip())
                    if ':' in lines[i]:
                        break
                signature = ' '.join(sig_lines)

            # Check if async
            is_async = signature.strip().startswith('async ')

            # Extract function calls
            calls = self._extract_calls(node)

            # Extract docstring
            docstring = self._extract_docstring(node)

            return FunctionInfo(
                name=name,
                signature=signature,
                start_line=start_line,
                end_line=end_line,
                calls=calls,
                is_method=False,
                is_async=is_async,
                docstring=docstring
            )
        except Exception:
            return None

    def _extract_class(self, node, content: str) -> ClassInfo | None:
        """Extract class information from a class_definition node."""
        try:
            # Get class name
            name_node = node.find(kind="identifier")
            if not name_node:
                return None
            name = name_node.text()

            # Get line numbers
            start_line = node.range().start.line + 1
            end_line = node.range().end.line + 1

            # Build signature (first line of class)
            lines = content.split('\n')
            signature = lines[start_line - 1].strip() if start_line <= len(lines) else ""

            # Extract base classes
            bases = []
            arg_list = node.find(kind="argument_list")
            if arg_list:
                for child in arg_list.children():
                    if child.kind() == "identifier":
                        bases.append(child.text())
                    elif child.kind() == "attribute":
                        bases.append(child.text())

            # Extract methods
            methods = []
            for func_node in node.find_all(kind="function_definition"):
                # Only direct children (not nested functions)
                func_info = self._extract_function(func_node, content)
                if func_info:
                    func_info.is_method = True
                    methods.append(func_info)

            # Extract docstring
            docstring = self._extract_docstring(node)

            return ClassInfo(
                name=name,
                signature=signature,
                start_line=start_line,
                end_line=end_line,
                methods=methods,
                bases=bases,
                docstring=docstring
            )
        except Exception:
            return None

    def _extract_calls(self, node) -> list[str]:
        """Extract function calls from a function body."""
        calls = []
        try:
            for call in node.find_all(kind="call"):
                # Get the function being called
                func = call.find(kind="identifier")
                if func:
                    calls.append(func.text())
                else:
                    # Could be an attribute call like obj.method()
                    attr = call.find(kind="attribute")
                    if attr:
                        # Get the last identifier (method name)
                        ids = list(attr.find_all(kind="identifier"))
                        if ids:
                            calls.append(ids[-1].text())
        except Exception:
            pass
        return list(set(calls))  # Remove duplicates

    def _extract_docstring(self, node) -> str | None:
        """Extract docstring from a function or class."""
        try:
            # Find the block containing the body
            block = node.find(kind="block")
            if not block:
                return None

            # First statement in the block
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
