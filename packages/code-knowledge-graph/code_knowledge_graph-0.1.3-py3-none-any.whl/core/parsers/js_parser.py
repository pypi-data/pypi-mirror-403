"""JavaScript/TypeScript/TSX import and function parser using ast-grep."""

import logging
from pathlib import Path
from ast_grep_py import SgRoot
from typing import Optional

from .base import (
    BaseParser, ImportInfo, FunctionInfo, ClassInfo, ParseResult,
    DecoratorInfo, AttributeInfo, GlobalVariableInfo, EnhancedFunctionInfo,
    EnhancedClassInfo, EnhancedParseResult
)

logger = logging.getLogger("code_knowledge_graph.parser.javascript")


class JsParser(BaseParser):
    """Parser for JavaScript, TypeScript, and TSX files."""

    supported_extensions = [".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"]

    def parse(self, content: str, file_path: Path) -> list[ImportInfo]:
        """Parse JS/TS source and extract imports."""
        imports: list[ImportInfo] = []

        # Determine language based on extension
        ext = file_path.suffix.lower()
        if ext in [".ts", ".tsx"]:
            lang = "typescript"
        else:
            lang = "javascript"

        try:
            root = SgRoot(content, lang)
            node = root.root()

            # ES6 static imports: import xxx from 'path'
            for imp in node.find_all(kind="import_statement"):
                self._extract_es6_import(imp, imports)

            # require() calls
            for req in node.find_all(pattern="require($PATH)"):
                self._extract_require(req, imports)

            # Dynamic imports: import('path')
            for dyn in node.find_all(kind="call_expression"):
                self._extract_dynamic_import(dyn, imports)

            # export ... from 'path'
            for exp in node.find_all(kind="export_statement"):
                self._extract_export_from(exp, imports)

            logger.debug(f"Parsed {file_path}: found {len(imports)} imports")

        except Exception as e:
            logger.warning(f"Failed to parse {file_path}: {type(e).__name__}: {e}")

        return imports

    def parse_full(self, content: str, file_path: Path) -> ParseResult:
        """Parse JS/TS source and extract all information."""
        result = ParseResult()

        # Determine language based on extension
        ext = file_path.suffix.lower()
        if ext in [".ts", ".tsx"]:
            lang = "typescript"
        else:
            lang = "javascript"

        try:
            root = SgRoot(content, lang)
            node = root.root()

            # Extract imports
            for imp in node.find_all(kind="import_statement"):
                self._extract_es6_import(imp, result.imports)
            for req in node.find_all(pattern="require($PATH)"):
                self._extract_require(req, result.imports)
            for dyn in node.find_all(kind="call_expression"):
                self._extract_dynamic_import(dyn, result.imports)
            for exp in node.find_all(kind="export_statement"):
                self._extract_export_from(exp, result.imports)

            # Extract functions
            for func_node in node.find_all(kind="function_declaration"):
                func_info = self._extract_function(func_node, content)
                if func_info:
                    result.functions.append(func_info)

            # Arrow functions assigned to const/let/var
            for var_decl in node.find_all(kind="lexical_declaration"):
                func_info = self._extract_arrow_function(var_decl, content)
                if func_info:
                    result.functions.append(func_info)

            for var_decl in node.find_all(kind="variable_declaration"):
                func_info = self._extract_arrow_function(var_decl, content)
                if func_info:
                    result.functions.append(func_info)

            # Extract classes
            for class_node in node.find_all(kind="class_declaration"):
                class_info = self._extract_class(class_node, content)
                if class_info:
                    result.classes.append(class_info)

            logger.debug(
                f"Parsed {file_path}: {len(result.imports)} imports, "
                f"{len(result.functions)} functions, {len(result.classes)} classes"
            )

        except Exception as e:
            logger.warning(f"Failed to parse {file_path}: {type(e).__name__}: {e}")

        return result

    def _extract_es6_import(self, node, imports: list[ImportInfo]) -> None:
        """Extract path from ES6 import statement."""
        # Find the string node containing the path
        string_node = node.find(kind="string")
        if string_node:
            path = self._clean_string(string_node.text())
            imports.append(ImportInfo(
                module=path,
                import_type="static",
                line=node.range().start.line + 1
            ))

    def _extract_require(self, node, imports: list[ImportInfo]) -> None:
        """Extract path from require() call."""
        # Get the argument
        args = node.find(kind="arguments")
        if args:
            string_node = args.find(kind="string")
            if string_node:
                path = self._clean_string(string_node.text())
                imports.append(ImportInfo(
                    module=path,
                    import_type="require",
                    line=node.range().start.line + 1
                ))

    def _extract_dynamic_import(self, node, imports: list[ImportInfo]) -> None:
        """Extract path from dynamic import() call."""
        # Check if this is an import() call
        func = node.find(kind="import")
        if not func:
            return

        args = node.find(kind="arguments")
        if args:
            string_node = args.find(kind="string")
            if string_node:
                path = self._clean_string(string_node.text())
                imports.append(ImportInfo(
                    module=path,
                    import_type="dynamic",
                    line=node.range().start.line + 1
                ))

    def _extract_export_from(self, node, imports: list[ImportInfo]) -> None:
        """Extract path from 'export ... from' statement."""
        text = node.text()
        if "from" not in text:
            return

        string_node = node.find(kind="string")
        if string_node:
            path = self._clean_string(string_node.text())
            imports.append(ImportInfo(
                module=path,
                import_type="static",
                line=node.range().start.line + 1
            ))

    def _extract_function(self, node, content: str) -> FunctionInfo | None:
        """Extract function information from a function_declaration node."""
        try:
            # Get function name
            name_node = node.find(kind="identifier")
            if not name_node:
                return None
            name = name_node.text()

            # Get line numbers
            start_line = node.range().start.line + 1
            end_line = node.range().end.line + 1

            # Build signature
            lines = content.split('\n')
            signature_line = lines[start_line - 1].strip() if start_line <= len(lines) else ""

            # Extract up to the opening brace
            sig_parts = []
            for i in range(start_line - 1, min(end_line, len(lines))):
                line = lines[i]
                sig_parts.append(line.strip())
                if '{' in line:
                    # Truncate at the brace
                    last = sig_parts[-1]
                    idx = last.find('{')
                    sig_parts[-1] = last[:idx].strip()
                    break
            signature = ' '.join(sig_parts).strip()
            if signature.endswith('{'):
                signature = signature[:-1].strip()

            # Check if async
            is_async = 'async' in signature_line and 'async' in signature

            # Extract function calls
            calls = self._extract_calls(node)

            return FunctionInfo(
                name=name,
                signature=signature if signature else signature_line,
                start_line=start_line,
                end_line=end_line,
                calls=calls,
                is_method=False,
                is_async=is_async,
                docstring=None  # JS doesn't have docstrings in the same way
            )
        except Exception:
            return None

    def _extract_arrow_function(self, node, content: str) -> FunctionInfo | None:
        """Extract arrow function from variable declaration."""
        try:
            # Find the arrow function
            arrow = node.find(kind="arrow_function")
            if not arrow:
                return None

            # Find the variable name
            declarator = node.find(kind="variable_declarator")
            if not declarator:
                return None

            name_node = declarator.find(kind="identifier")
            if not name_node:
                return None
            name = name_node.text()

            # Get line numbers
            start_line = node.range().start.line + 1
            end_line = node.range().end.line + 1

            # Build signature
            lines = content.split('\n')
            signature_line = lines[start_line - 1].strip() if start_line <= len(lines) else ""

            # Extract up to the arrow
            sig_parts = []
            for i in range(start_line - 1, min(end_line, len(lines))):
                line = lines[i]
                sig_parts.append(line.strip())
                if '=>' in line:
                    # Keep up to and including the arrow
                    last = sig_parts[-1]
                    idx = last.find('=>')
                    sig_parts[-1] = last[:idx + 2].strip()
                    break
            signature = ' '.join(sig_parts).strip()

            # Check if async
            is_async = 'async' in signature

            # Extract function calls
            calls = self._extract_calls(arrow)

            return FunctionInfo(
                name=name,
                signature=signature if signature else signature_line,
                start_line=start_line,
                end_line=end_line,
                calls=calls,
                is_method=False,
                is_async=is_async,
                docstring=None
            )
        except Exception:
            return None

    def _extract_class(self, node, content: str) -> ClassInfo | None:
        """Extract class information from a class_declaration node."""
        try:
            # Get class name
            name_node = node.find(kind="identifier")
            if not name_node:
                return None
            name = name_node.text()

            # Get line numbers
            start_line = node.range().start.line + 1
            end_line = node.range().end.line + 1

            # Build signature
            lines = content.split('\n')
            signature_line = lines[start_line - 1].strip() if start_line <= len(lines) else ""

            # Extract up to the opening brace
            sig_parts = []
            for i in range(start_line - 1, min(start_line + 3, len(lines))):
                line = lines[i]
                sig_parts.append(line.strip())
                if '{' in line:
                    last = sig_parts[-1]
                    idx = last.find('{')
                    sig_parts[-1] = last[:idx].strip()
                    break
            signature = ' '.join(sig_parts).strip()

            # Extract base class
            bases = []
            heritage = node.find(kind="class_heritage")
            if heritage:
                extends = heritage.find(kind="identifier")
                if extends:
                    bases.append(extends.text())

            # Extract methods
            methods = []
            class_body = node.find(kind="class_body")
            if class_body:
                for method_node in class_body.find_all(kind="method_definition"):
                    method_info = self._extract_method(method_node, content)
                    if method_info:
                        methods.append(method_info)

            return ClassInfo(
                name=name,
                signature=signature if signature else signature_line,
                start_line=start_line,
                end_line=end_line,
                methods=methods,
                bases=bases,
                docstring=None
            )
        except Exception:
            return None

    def _extract_method(self, node, content: str) -> FunctionInfo | None:
        """Extract method information from a method_definition node."""
        try:
            # Get method name
            name_node = node.find(kind="property_identifier")
            if not name_node:
                return None
            name = name_node.text()

            # Get line numbers
            start_line = node.range().start.line + 1
            end_line = node.range().end.line + 1

            # Build signature
            lines = content.split('\n')
            signature_line = lines[start_line - 1].strip() if start_line <= len(lines) else ""

            # Extract up to the opening brace
            sig_parts = []
            for i in range(start_line - 1, min(end_line, len(lines))):
                line = lines[i]
                sig_parts.append(line.strip())
                if '{' in line:
                    last = sig_parts[-1]
                    idx = last.find('{')
                    sig_parts[-1] = last[:idx].strip()
                    break
            signature = ' '.join(sig_parts).strip()

            # Check if async
            is_async = 'async' in signature

            # Extract function calls
            calls = self._extract_calls(node)

            return FunctionInfo(
                name=name,
                signature=signature if signature else signature_line,
                start_line=start_line,
                end_line=end_line,
                calls=calls,
                is_method=True,
                is_async=is_async,
                docstring=None
            )
        except Exception:
            return None

    def _extract_calls(self, node) -> list[str]:
        """Extract function calls from a function body."""
        calls = []
        try:
            for call in node.find_all(kind="call_expression"):
                # Get the function being called
                func = call.find(kind="identifier")
                if func:
                    calls.append(func.text())
                else:
                    # Could be a member expression like obj.method()
                    member = call.find(kind="member_expression")
                    if member:
                        prop = member.find(kind="property_identifier")
                        if prop:
                            calls.append(prop.text())
        except Exception:
            pass
        return list(set(calls))  # Remove duplicates

    def _clean_string(self, s: str) -> str:
        """Remove quotes from string literal."""
        return s.strip("'\"`")

    def parse_enhanced(self, content: str, file_path: Path) -> EnhancedParseResult:
        """Parse JS/TS source and extract enhanced information including decorators, attributes, and global variables."""
        result = EnhancedParseResult()

        # Determine language based on extension
        ext = file_path.suffix.lower()
        is_typescript = ext in [".ts", ".tsx"]
        if is_typescript:
            lang = "typescript"
        else:
            lang = "javascript"

        try:
            root = SgRoot(content, lang)
            node = root.root()

            # Extract imports
            for imp in node.find_all(kind="import_statement"):
                self._extract_es6_import(imp, result.imports)
            for req in node.find_all(pattern="require($PATH)"):
                self._extract_require(req, result.imports)
            for dyn in node.find_all(kind="call_expression"):
                self._extract_dynamic_import(dyn, result.imports)
            for exp in node.find_all(kind="export_statement"):
                self._extract_export_from(exp, result.imports)

            # Extract global variables
            result.global_variables = self._extract_global_variables(node, content, is_typescript)

            # Extract classes with enhanced info
            for class_node in node.find_all(kind="class_declaration"):
                class_info = self._extract_enhanced_class(class_node, content, is_typescript)
                if class_info:
                    result.classes.append(class_info)

            # Extract functions with decorators
            for func_node in node.find_all(kind="function_declaration"):
                func_info = self._extract_function(func_node, content)
                if func_info:
                    result.functions.append(func_info)

            # Arrow functions assigned to const/let/var
            for var_decl in node.find_all(kind="lexical_declaration"):
                func_info = self._extract_arrow_function(var_decl, content)
                if func_info:
                    result.functions.append(func_info)

            for var_decl in node.find_all(kind="variable_declaration"):
                func_info = self._extract_arrow_function(var_decl, content)
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

    def _extract_decorators(self, node) -> list[DecoratorInfo]:
        """Extract decorators from a class or method (TypeScript/NestJS style)."""
        decorators = []
        try:
            # In TypeScript, decorators are represented as "decorator" nodes
            for decorator in node.find_all(kind="decorator"):
                line = decorator.range().start.line + 1
                
                # Get decorator text
                dec_text = decorator.text()
                
                # Remove the @ symbol
                if dec_text.startswith("@"):
                    dec_text = dec_text[1:].strip()
                
                # Check if it's a call (has arguments)
                call_node = decorator.find(kind="call_expression")
                if call_node:
                    # Get the function being called
                    func_part = call_node.find(kind="identifier")
                    member_part = call_node.find(kind="member_expression")
                    
                    if member_part:
                        name = member_part.text().split("(")[0]
                    elif func_part:
                        name = func_part.text()
                    else:
                        name = dec_text.split("(")[0]
                    
                    # Extract arguments
                    args = []
                    arg_list = call_node.find(kind="arguments")
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
                    
                    if identifier:
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

    def _extract_class_attributes(self, class_node, content: str, is_typescript: bool = False) -> list[AttributeInfo]:
        """Extract class attributes and type annotations from a class."""
        attributes = []
        try:
            lines = content.split('\n')
            class_body = class_node.find(kind="class_body")
            if not class_body:
                return attributes
            
            # Look for public_field_definition (TypeScript class fields)
            for field in class_body.find_all(kind="public_field_definition"):
                name_node = field.find(kind="property_identifier")
                if not name_node:
                    continue
                
                name = name_node.text()
                line = field.range().start.line + 1
                line_text = lines[line - 1].strip() if line <= len(lines) else ""
                
                type_annotation = None
                default_value = None
                
                # Check for type annotation (TypeScript only)
                if is_typescript:
                    try:
                        type_node = field.find(kind="type_annotation")
                        if type_node:
                            type_annotation = type_node.text()
                            if type_annotation.startswith(":"):
                                type_annotation = type_annotation[1:].strip()
                    except Exception:
                        pass
                
                # Check for default value
                if "=" in line_text:
                    default_value = line_text.split("=", 1)[1].strip().rstrip(";")
                
                attributes.append(AttributeInfo(
                    name=name,
                    type_annotation=type_annotation,
                    default_value=default_value,
                    line=line,
                    is_class_var=False
                ))
            
            # Also look for field_definition (JavaScript class fields)
            for field in class_body.find_all(kind="field_definition"):
                name_node = field.find(kind="property_identifier")
                if not name_node:
                    continue
                
                name = name_node.text()
                line = field.range().start.line + 1
                line_text = lines[line - 1].strip() if line <= len(lines) else ""
                
                type_annotation = None
                default_value = None
                
                # Check for type annotation (TypeScript only)
                if is_typescript:
                    try:
                        type_node = field.find(kind="type_annotation")
                        if type_node:
                            type_annotation = type_node.text()
                            if type_annotation.startswith(":"):
                                type_annotation = type_annotation[1:].strip()
                    except Exception:
                        pass
                
                # Check for default value
                if "=" in line_text:
                    default_value = line_text.split("=", 1)[1].strip().rstrip(";")
                
                # Avoid duplicates
                if not any(a.name == name and a.line == line for a in attributes):
                    attributes.append(AttributeInfo(
                        name=name,
                        type_annotation=type_annotation,
                        default_value=default_value,
                        line=line,
                        is_class_var=False
                    ))
        except Exception as e:
            logger.debug(f"Error extracting class attributes: {e}")
        
        return attributes

    def _extract_enhanced_class(self, class_node, content: str, is_typescript: bool = False) -> EnhancedClassInfo | None:
        """Extract enhanced class information including decorators and attributes."""
        try:
            # Get basic class info
            basic_info = self._extract_class(class_node, content)
            if not basic_info:
                return None
            
            # Extract decorators (check parent for decorated class)
            decorators = self._extract_decorators(class_node)
            
            # Also check if there's a parent export_statement with decorators
            parent = class_node.parent()
            if parent and parent.kind() == "export_statement":
                decorators.extend(self._extract_decorators(parent))
            
            # Extract class attributes
            attributes = self._extract_class_attributes(class_node, content, is_typescript)
            
            # Adjust start line if there are decorators
            start_line = basic_info.start_line
            if decorators:
                start_line = min(d.line for d in decorators)
            
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

    def _extract_global_variables(self, root_node, content: str, is_typescript: bool = False) -> list[GlobalVariableInfo]:
        """Extract global/module-level variable definitions."""
        global_vars = []
        lines = content.split('\n')
        
        # Find lexical declarations (const, let) at module level
        for decl in root_node.find_all(kind="lexical_declaration"):
            # Skip if it's an arrow function (already handled)
            if decl.find(kind="arrow_function"):
                continue
            
            # Check if it's at module level
            parent = decl.parent()
            if parent and parent.kind() not in ("program", "export_statement"):
                continue
            
            for declarator in decl.find_all(kind="variable_declarator"):
                name_node = declarator.find(kind="identifier")
                if not name_node:
                    continue
                
                name = name_node.text()
                line = decl.range().start.line + 1
                line_text = lines[line - 1].strip() if line <= len(lines) else ""
                
                type_annotation = None
                value = None
                
                # Check for type annotation (TypeScript only)
                if is_typescript:
                    try:
                        type_node = declarator.find(kind="type_annotation")
                        if type_node:
                            type_annotation = type_node.text()
                            if type_annotation.startswith(":"):
                                type_annotation = type_annotation[1:].strip()
                    except Exception:
                        pass
                
                # Get value
                if "=" in line_text:
                    value = line_text.split("=", 1)[1].strip().rstrip(";")
                    # Truncate long values
                    if len(value) > 100:
                        value = value[:100] + "..."
                
                global_vars.append(GlobalVariableInfo(
                    name=name,
                    type_annotation=type_annotation,
                    value=value,
                    line=line
                ))
        
        # Find variable declarations (var) at module level
        for decl in root_node.find_all(kind="variable_declaration"):
            # Skip if it's an arrow function
            if decl.find(kind="arrow_function"):
                continue
            
            # Check if it's at module level
            parent = decl.parent()
            if parent and parent.kind() not in ("program", "export_statement"):
                continue
            
            for declarator in decl.find_all(kind="variable_declarator"):
                name_node = declarator.find(kind="identifier")
                if not name_node:
                    continue
                
                name = name_node.text()
                line = decl.range().start.line + 1
                line_text = lines[line - 1].strip() if line <= len(lines) else ""
                
                type_annotation = None
                value = None
                
                # Get value
                if "=" in line_text:
                    value = line_text.split("=", 1)[1].strip().rstrip(";")
                    if len(value) > 100:
                        value = value[:100] + "..."
                
                # Avoid duplicates
                if not any(v.name == name and v.line == line for v in global_vars):
                    global_vars.append(GlobalVariableInfo(
                        name=name,
                        type_annotation=type_annotation,
                        value=value,
                        line=line
                    ))
        
        return global_vars
