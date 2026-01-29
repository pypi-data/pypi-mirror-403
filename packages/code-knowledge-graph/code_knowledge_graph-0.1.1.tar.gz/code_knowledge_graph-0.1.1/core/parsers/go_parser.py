"""Go import and function parser using ast-grep."""

import logging
import re
from pathlib import Path
from ast_grep_py import SgRoot
from typing import Optional

from .base import (
    BaseParser, ImportInfo, FunctionInfo, ClassInfo, ParseResult,
    DecoratorInfo, GlobalVariableInfo, EnhancedFunctionInfo,
    EnhancedParseResult, StructInfo, InterfaceInfo, StructFieldInfo,
    InterfaceMethodInfo
)

logger = logging.getLogger("code_knowledge_graph.parser.go")


class GoParser(BaseParser):
    """Parser for Go files."""

    supported_extensions = [".go"]

    # Go built-in functions that should be filtered from call tracking
    GO_BUILTINS = frozenset([
        "append", "cap", "close", "complex", "copy", "delete",
        "imag", "len", "make", "new", "panic", "print", "println",
        "real", "recover", "string", "int", "int8", "int16", "int32",
        "int64", "uint", "uint8", "uint16", "uint32", "uint64",
        "uintptr", "float32", "float64", "complex64", "complex128",
        "bool", "byte", "rune", "error", "any",
    ])

    def parse(self, content: str, file_path: Path) -> list[ImportInfo]:
        """Parse Go source and extract imports."""
        imports: list[ImportInfo] = []

        try:
            root = SgRoot(content, "go")
            node = root.root()

            # Find import declarations
            for imp_decl in node.find_all(kind="import_declaration"):
                self._extract_imports(imp_decl, imports)

        except Exception as e:
            logger.warning(f"Failed to parse {file_path}: {type(e).__name__}: {e}")

        return imports

    def parse_full(self, content: str, file_path: Path) -> ParseResult:
        """Parse Go source and extract all information."""
        result = ParseResult()

        try:
            root = SgRoot(content, "go")
            node = root.root()

            # Extract imports
            for imp_decl in node.find_all(kind="import_declaration"):
                self._extract_imports(imp_decl, result.imports)

            # Extract functions (including methods)
            for func_node in node.find_all(kind="function_declaration"):
                func_info = self._extract_function(func_node, content)
                if func_info:
                    result.functions.append(func_info)

            # Extract method declarations (receiver functions)
            for method_node in node.find_all(kind="method_declaration"):
                method_info = self._extract_method(method_node, content)
                if method_info:
                    result.functions.append(method_info)

            logger.debug(
                f"Parsed {file_path}: {len(result.imports)} imports, "
                f"{len(result.functions)} functions"
            )

        except Exception as e:
            logger.warning(f"Failed to parse {file_path}: {type(e).__name__}: {e}")

        return result

    def parse_enhanced(self, content: str, file_path: Path) -> EnhancedParseResult:
        """Parse Go source and extract enhanced information including structs, interfaces, and package info."""
        result = EnhancedParseResult()

        try:
            root = SgRoot(content, "go")
            node = root.root()

            # Extract package name
            result.package_name = self._extract_package_name(node)

            # Extract imports
            for imp_decl in node.find_all(kind="import_declaration"):
                self._extract_imports(imp_decl, result.imports)

            # Extract global variables
            result.global_variables = self._extract_global_variables(node, content)

            # Extract structs
            result.structs = self._extract_structs(node, content)

            # Extract interfaces
            result.interfaces = self._extract_interfaces(node, content)

            # Extract functions with enhanced info (defer, go keywords)
            for func_node in node.find_all(kind="function_declaration"):
                func_info = self._extract_enhanced_function(func_node, content)
                if func_info:
                    result.functions.append(func_info)

            # Extract method declarations (receiver functions)
            for method_node in node.find_all(kind="method_declaration"):
                method_info = self._extract_enhanced_method(method_node, content)
                if method_info:
                    result.functions.append(method_info)

            logger.debug(
                f"Enhanced parse {file_path}: {len(result.imports)} imports, "
                f"{len(result.functions)} functions, {len(result.structs)} structs, "
                f"{len(result.interfaces)} interfaces, package={result.package_name}"
            )

        except Exception as e:
            logger.warning(f"Failed to parse {file_path}: {type(e).__name__}: {e}")

        return result

    def _extract_package_name(self, root_node) -> Optional[str]:
        """Extract package name from Go source."""
        try:
            package_clause = root_node.find(kind="package_clause")
            if package_clause:
                package_id = package_clause.find(kind="package_identifier")
                if package_id:
                    return package_id.text()
        except Exception:
            pass
        return None

    def _extract_imports(self, imp_decl, imports: list[ImportInfo]) -> None:
        """Extract imports from an import declaration."""
        try:
            line = imp_decl.range().start.line + 1
            
            # Find all import_spec nodes (works for both single and block imports)
            for spec in imp_decl.find_all(kind="import_spec"):
                path_node = spec.find(kind="interpreted_string_literal")
                if path_node:
                    module = path_node.text().strip('"')
                    spec_line = spec.range().start.line + 1
                    imports.append(ImportInfo(
                        module=module,
                        import_type="static",
                        line=spec_line
                    ))
        except Exception as e:
            logger.debug(f"Error extracting imports: {e}")

    def _extract_function(self, func_node, content: str) -> FunctionInfo | None:
        """Extract function information from a function_declaration node."""
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

            # Extract function calls
            calls = self._extract_calls(func_node)

            return FunctionInfo(
                name=name,
                signature=signature if signature else signature_line,
                start_line=start_line,
                end_line=end_line,
                calls=calls,
                is_method=False,
                is_async=False,
                docstring=self._extract_docstring(func_node, content)
            )
        except Exception:
            return None

    def _extract_method(self, method_node, content: str) -> FunctionInfo | None:
        """Extract method information from a method_declaration node."""
        try:
            # Get method name
            name_node = method_node.find(kind="field_identifier")
            if not name_node:
                return None
            name = name_node.text()

            # Get line numbers
            start_line = method_node.range().start.line + 1
            end_line = method_node.range().end.line + 1

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

            # Extract function calls
            calls = self._extract_calls(method_node)

            return FunctionInfo(
                name=name,
                signature=signature if signature else signature_line,
                start_line=start_line,
                end_line=end_line,
                calls=calls,
                is_method=True,
                is_async=False,
                docstring=self._extract_docstring(method_node, content)
            )
        except Exception:
            return None

    def _extract_enhanced_function(self, func_node, content: str) -> EnhancedFunctionInfo | None:
        """Extract enhanced function information including defer/go calls."""
        try:
            basic_info = self._extract_function(func_node, content)
            if not basic_info:
                return None
            
            return EnhancedFunctionInfo(
                name=basic_info.name,
                signature=basic_info.signature,
                start_line=basic_info.start_line,
                end_line=basic_info.end_line,
                calls=basic_info.calls,
                is_method=basic_info.is_method,
                is_async=basic_info.is_async,
                docstring=basic_info.docstring,
                decorators=[],
                receiver_type=None,
                receiver_name=None,
                call_type="direct"
            )
        except Exception:
            return None

    def _extract_enhanced_method(self, method_node, content: str) -> EnhancedFunctionInfo | None:
        """Extract enhanced method information including receiver info and defer/go calls.

        For Go methods like `func (t *Tenant) IsActive() bool`, this extracts:
        - name: "IsActive" (method name only)
        - receiver_type: "*Tenant" (full type with pointer)
        - receiver_name: "t" (receiver variable name)
        - container_name: "Tenant" (base type for symbol lookup)

        The container_name field is used for building function relations.
        """
        try:
            basic_info = self._extract_method(method_node, content)
            if not basic_info:
                return None

            # Extract receiver information
            receiver_type = None
            receiver_name = None
            base_receiver_type = None  # Type without pointer prefix

            param_list = method_node.find(kind="parameter_list")
            if param_list:
                # First parameter list is the receiver
                params = list(param_list.find_all(kind="parameter_declaration"))
                if params:
                    receiver_param = params[0]
                    # Get receiver name
                    name_node = receiver_param.find(kind="identifier")
                    if name_node:
                        receiver_name = name_node.text()

                    # Get receiver type (could be pointer or value type)
                    pointer_type = receiver_param.find(kind="pointer_type")
                    if pointer_type:
                        receiver_type = pointer_type.text()
                        # Extract base type from pointer type (e.g., *Tenant -> Tenant)
                        type_id = pointer_type.find(kind="type_identifier")
                        if type_id:
                            base_receiver_type = type_id.text()
                    else:
                        type_node = receiver_param.find(kind="type_identifier")
                        if type_node:
                            receiver_type = type_node.text()
                            base_receiver_type = type_node.text()

            return EnhancedFunctionInfo(
                name=basic_info.name,
                signature=basic_info.signature,
                start_line=basic_info.start_line,
                end_line=basic_info.end_line,
                calls=basic_info.calls,
                is_method=True,
                is_async=basic_info.is_async,
                docstring=basic_info.docstring,
                decorators=[],
                receiver_type=receiver_type,
                receiver_name=receiver_name,
                call_type="direct"
            )
        except Exception:
            return None

    def _extract_calls(self, node) -> list[str]:
        """Extract function calls from a function body, including defer and go calls.

        Important: Uses field("function") to get the actual function
        being called, avoiding false positives from assignment targets like:
        `tenant, err := NewTenant(...)` where tenant/err are NOT function calls.

        Filters out Go built-in functions like append, make, len, etc.
        """
        calls = []
        try:
            # Regular function calls
            for call in node.find_all(kind="call_expression"):
                # Get the function being called (not any identifier in the expression)
                func_node = call.field("function")
                if func_node:
                    if func_node.kind() == "identifier":
                        # Simple function call: NewTenant()
                        func_name = func_node.text()
                        if func_name not in self.GO_BUILTINS:
                            calls.append(func_name)
                    elif func_node.kind() == "selector_expression":
                        # Method call: obj.Method() or pkg.Func()
                        field_node = func_node.field("field")
                        if field_node:
                            calls.append(field_node.text())
                    elif func_node.kind() == "parenthesized_expression":
                        # Type assertion or function cast: (*Type)(value)
                        inner = func_node.find(kind="identifier")
                        if inner:
                            func_name = inner.text()
                            if func_name not in self.GO_BUILTINS:
                                calls.append(func_name)

            # Defer statements
            for defer_stmt in node.find_all(kind="defer_statement"):
                call = defer_stmt.find(kind="call_expression")
                if call:
                    func_node = call.field("function")
                    if func_node:
                        if func_node.kind() == "identifier":
                            func_name = func_node.text()
                            if func_name not in self.GO_BUILTINS:
                                calls.append(f"defer:{func_name}")
                        elif func_node.kind() == "selector_expression":
                            field_node = func_node.field("field")
                            if field_node:
                                calls.append(f"defer:{field_node.text()}")

            # Go statements (goroutines)
            for go_stmt in node.find_all(kind="go_statement"):
                call = go_stmt.find(kind="call_expression")
                if call:
                    func_node = call.field("function")
                    if func_node:
                        if func_node.kind() == "identifier":
                            func_name = func_node.text()
                            if func_name not in self.GO_BUILTINS:
                                calls.append(f"go:{func_name}")
                        elif func_node.kind() == "selector_expression":
                            field_node = func_node.field("field")
                            if field_node:
                                calls.append(f"go:{field_node.text()}")
        except Exception:
            pass
        return list(set(calls))  # Remove duplicates

    def _extract_docstring(self, node, content: str) -> Optional[str]:
        """Extract comment above a function/method as docstring."""
        try:
            start_line = node.range().start.line
            if start_line == 0:
                return None
            
            lines = content.split('\n')
            
            # Look for comment lines immediately above the function
            doc_lines = []
            for i in range(start_line - 1, -1, -1):
                line = lines[i].strip()
                if line.startswith("//"):
                    doc_lines.insert(0, line[2:].strip())
                elif line.startswith("/*"):
                    # Multi-line comment
                    comment_text = line[2:]
                    if "*/" in comment_text:
                        comment_text = comment_text.split("*/")[0]
                    doc_lines.insert(0, comment_text.strip())
                    break
                elif line == "":
                    continue
                else:
                    break
            
            if doc_lines:
                return '\n'.join(doc_lines)
        except Exception:
            pass
        return None

    def _extract_structs(self, root_node, content: str) -> list[StructInfo]:
        """Extract struct definitions from Go source."""
        structs = []
        try:
            lines = content.split('\n')
            
            for type_decl in root_node.find_all(kind="type_declaration"):
                for type_spec in type_decl.find_all(kind="type_spec"):
                    # Check if it's a struct type
                    struct_type = type_spec.find(kind="struct_type")
                    if not struct_type:
                        continue
                    
                    # Get struct name
                    name_node = type_spec.find(kind="type_identifier")
                    if not name_node:
                        continue
                    name = name_node.text()
                    
                    # Get line numbers
                    start_line = type_decl.range().start.line + 1
                    end_line = type_decl.range().end.line + 1
                    
                    # Extract fields
                    fields = self._extract_struct_fields(struct_type, content)
                    
                    # Extract docstring
                    docstring = self._extract_docstring(type_decl, content)
                    
                    structs.append(StructInfo(
                        name=name,
                        fields=fields,
                        start_line=start_line,
                        end_line=end_line,
                        docstring=docstring
                    ))
        except Exception as e:
            logger.debug(f"Error extracting structs: {e}")
        
        return structs

    def _extract_struct_fields(self, struct_type, content: str) -> list[StructFieldInfo]:
        """Extract fields from a struct type."""
        fields = []
        try:
            lines = content.split('\n')
            field_list = struct_type.find(kind="field_declaration_list")
            if not field_list:
                return fields
            
            for field_decl in field_list.find_all(kind="field_declaration"):
                line = field_decl.range().start.line + 1
                line_text = lines[line - 1].strip() if line <= len(lines) else ""
                
                # Get field name(s)
                name_nodes = list(field_decl.find_all(kind="field_identifier"))
                
                # Get field type
                type_text = ""
                type_node = field_decl.find(kind="type_identifier")
                if type_node:
                    type_text = type_node.text()
                else:
                    # Could be a pointer type, slice type, etc.
                    for child in field_decl.children():
                        if child.kind() in ("pointer_type", "slice_type", "array_type", 
                                           "map_type", "channel_type", "qualified_type"):
                            type_text = child.text()
                            break
                
                # Get struct tag
                tag = None
                tag_node = field_decl.find(kind="raw_string_literal")
                if tag_node:
                    tag = tag_node.text()
                else:
                    # Check for interpreted string literal
                    tag_node = field_decl.find(kind="interpreted_string_literal")
                    if tag_node:
                        tag = tag_node.text()
                
                # Create field info for each name
                for name_node in name_nodes:
                    fields.append(StructFieldInfo(
                        name=name_node.text(),
                        type_annotation=type_text,
                        tag=tag,
                        line=line
                    ))
                
                # Handle embedded fields (no name, just type)
                if not name_nodes and type_text:
                    fields.append(StructFieldInfo(
                        name=type_text,  # Embedded type name
                        type_annotation=type_text,
                        tag=tag,
                        line=line
                    ))
        except Exception as e:
            logger.debug(f"Error extracting struct fields: {e}")
        
        return fields

    def _extract_interfaces(self, root_node, content: str) -> list[InterfaceInfo]:
        """Extract interface definitions from Go source."""
        interfaces = []
        try:
            for type_decl in root_node.find_all(kind="type_declaration"):
                for type_spec in type_decl.find_all(kind="type_spec"):
                    # Check if it's an interface type
                    interface_type = type_spec.find(kind="interface_type")
                    if not interface_type:
                        continue
                    
                    # Get interface name
                    name_node = type_spec.find(kind="type_identifier")
                    if not name_node:
                        continue
                    name = name_node.text()
                    
                    # Get line numbers
                    start_line = type_decl.range().start.line + 1
                    end_line = type_decl.range().end.line + 1
                    
                    # Extract methods
                    methods = self._extract_interface_methods(interface_type, content)
                    
                    # Extract docstring
                    docstring = self._extract_docstring(type_decl, content)
                    
                    interfaces.append(InterfaceInfo(
                        name=name,
                        methods=methods,
                        start_line=start_line,
                        end_line=end_line,
                        docstring=docstring
                    ))
        except Exception as e:
            logger.debug(f"Error extracting interfaces: {e}")
        
        return interfaces

    def _extract_interface_methods(self, interface_type, content: str) -> list[InterfaceMethodInfo]:
        """Extract method signatures from an interface type."""
        methods = []
        try:
            lines = content.split('\n')
            
            for method_spec in interface_type.find_all(kind="method_spec"):
                line = method_spec.range().start.line + 1
                line_text = lines[line - 1].strip() if line <= len(lines) else ""
                
                # Get method name
                name_node = method_spec.find(kind="field_identifier")
                if not name_node:
                    continue
                name = name_node.text()
                
                # Get full signature from line text
                signature = line_text
                
                methods.append(InterfaceMethodInfo(
                    name=name,
                    signature=signature,
                    line=line
                ))
        except Exception as e:
            logger.debug(f"Error extracting interface methods: {e}")
        
        return methods

    def _extract_global_variables(self, root_node, content: str) -> list[GlobalVariableInfo]:
        """Extract global/package-level variable definitions."""
        global_vars = []
        try:
            lines = content.split('\n')
            
            # Find var declarations
            for var_decl in root_node.find_all(kind="var_declaration"):
                for var_spec in var_decl.find_all(kind="var_spec"):
                    line = var_spec.range().start.line + 1
                    line_text = lines[line - 1].strip() if line <= len(lines) else ""
                    
                    # Get variable name(s)
                    for name_node in var_spec.find_all(kind="identifier"):
                        name = name_node.text()
                        
                        # Get type annotation
                        type_annotation = None
                        type_node = var_spec.find(kind="type_identifier")
                        if type_node:
                            type_annotation = type_node.text()
                        
                        # Get value (simplified)
                        value = None
                        if "=" in line_text:
                            value = line_text.split("=", 1)[1].strip()
                            if len(value) > 100:
                                value = value[:100] + "..."
                        
                        global_vars.append(GlobalVariableInfo(
                            name=name,
                            type_annotation=type_annotation,
                            value=value,
                            line=line
                        ))
                        break  # Only first identifier is the variable name
            
            # Find const declarations
            for const_decl in root_node.find_all(kind="const_declaration"):
                for const_spec in const_decl.find_all(kind="const_spec"):
                    line = const_spec.range().start.line + 1
                    line_text = lines[line - 1].strip() if line <= len(lines) else ""
                    
                    # Get constant name
                    name_node = const_spec.find(kind="identifier")
                    if not name_node:
                        continue
                    name = name_node.text()
                    
                    # Get type annotation
                    type_annotation = None
                    type_node = const_spec.find(kind="type_identifier")
                    if type_node:
                        type_annotation = type_node.text()
                    
                    # Get value
                    value = None
                    if "=" in line_text:
                        value = line_text.split("=", 1)[1].strip()
                        if len(value) > 100:
                            value = value[:100] + "..."
                    
                    global_vars.append(GlobalVariableInfo(
                        name=name,
                        type_annotation=type_annotation,
                        value=value,
                        line=line
                    ))
        except Exception as e:
            logger.debug(f"Error extracting global variables: {e}")
        
        return global_vars

    def parse_go_mod(self, content: str) -> Optional[str]:
        """Parse go.mod file and extract module path.
        
        Args:
            content: Content of go.mod file
            
        Returns:
            Module path or None if not found
        """
        try:
            # Look for module declaration: module github.com/user/repo
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith("module "):
                    module_path = line[7:].strip()
                    # Remove any trailing comments
                    if "//" in module_path:
                        module_path = module_path.split("//")[0].strip()
                    return module_path
        except Exception as e:
            logger.debug(f"Error parsing go.mod: {e}")
        return None
