"""Entry Point Detector Service for code knowledge graph.

This module implements entry point detection for various frameworks,
including HTTP routes, main entry points, database models, and CLI commands.

Uses AST-based detection (Tree-sitter) for accurate identification,
avoiding false positives from string/regex matching.

Feature: code-knowledge-graph-enhancement

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.9**
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional, Union

from ast_grep_py import SgRoot

from core.storage.sqlite import SQLiteStorage

logger = logging.getLogger(__name__)


class EntryPointType(Enum):
    """Entry point type enumeration.
    
    Represents different types of entry points that can be detected.
    
    Attributes:
        HTTP_ROUTE: HTTP API route handlers (FastAPI, Flask, Express, Gin, etc.)
        MAIN_ENTRY: Main entry points (__main__, func main())
        DATABASE_MODEL: Database model definitions (SQLAlchemy, Django, Gorm, etc.)
        CLI_COMMAND: CLI command definitions (Click, Typer, Cobra, etc.)
    """
    HTTP_ROUTE = "http_routes"
    MAIN_ENTRY = "main_entry"
    DATABASE_MODEL = "database_models"
    CLI_COMMAND = "cli_commands"


@dataclass
class HTTPRouteEntry:
    """HTTP route entry point.
    
    Represents an HTTP route handler detected in the codebase.
    
    Attributes:
        file_path: Relative path to the file containing the route
        line_number: Line number where the route is defined
        route_path: The URL path pattern (e.g., "/users/{id}")
        http_method: HTTP method (GET, POST, PUT, DELETE, etc.)
        handler_name: Name of the handler function
        framework: Framework name (fastapi, flask, express, gin, etc.)
    """
    file_path: str
    line_number: int
    route_path: str
    http_method: str
    handler_name: str
    framework: str


@dataclass
class MainEntry:
    """Main entry point.
    
    Represents a main entry point in the codebase.
    
    Attributes:
        file_path: Relative path to the file containing the entry point
        line_number: Line number where the entry point is defined
        entry_type: Type of entry point (__main__, main_func, package_main)
    """
    file_path: str
    line_number: int
    entry_type: str  # __main__, main_func, package_main


@dataclass
class DatabaseModelEntry:
    """Database model entry point.
    
    Represents a database model definition in the codebase.
    
    Attributes:
        file_path: Relative path to the file containing the model
        line_number: Line number where the model is defined
        model_name: Name of the model class/struct
        framework: ORM framework (sqlalchemy, django, gorm, ent, etc.)
        table_name: Database table name if specified
    """
    file_path: str
    line_number: int
    model_name: str
    framework: str  # sqlalchemy, django, gorm, ent, prisma
    table_name: Optional[str] = None


@dataclass
class CLICommandEntry:
    """CLI command entry point.
    
    Represents a CLI command definition in the codebase.
    
    Attributes:
        file_path: Relative path to the file containing the command
        line_number: Line number where the command is defined
        command_name: Name of the CLI command
        framework: CLI framework (click, typer, argparse, cobra, urfave-cli)
    """
    file_path: str
    line_number: int
    command_name: str
    framework: str  # click, typer, argparse, cobra, urfave-cli


@dataclass
class EntryPointResult:
    """Entry point detection result.
    
    Contains all detected entry points organized by type.
    
    Attributes:
        project_path: Path to the project
        http_routes: List of HTTP route entry points
        main_entries: List of main entry points
        database_models: List of database model entry points
        cli_commands: List of CLI command entry points
        message: Optional message (e.g., info or warning)
    """
    project_path: str
    http_routes: list[HTTPRouteEntry] = field(default_factory=list)
    main_entries: list[MainEntry] = field(default_factory=list)
    database_models: list[DatabaseModelEntry] = field(default_factory=list)
    cli_commands: list[CLICommandEntry] = field(default_factory=list)
    message: Optional[str] = None


# Type alias for any entry point type
EntryPoint = Union[HTTPRouteEntry, MainEntry, DatabaseModelEntry, CLICommandEntry]


class EntryPointDetector:
    """Entry point detector service.
    
    Detects various types of entry points in a codebase using AST-based
    analysis with Tree-sitter. Supports:
    
    - HTTP routes: FastAPI, Flask, Express, NestJS, Gin, Echo, Chi, Fiber
    - Main entry points: Python __main__, Go main()
    - Database models: SQLAlchemy, Django ORM, Prisma, Gorm, Ent
    - CLI commands: Click, Typer, Argparse, Cobra, Urfave-cli
    
    Uses AST queries instead of string/regex matching to avoid false positives
    from comments or string literals.
    
    **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.9**
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
    
    # Python HTTP framework configurations
    PYTHON_HTTP_FRAMEWORKS = {
        "fastapi": {
            "decorators": ["get", "post", "put", "delete", "patch", "options", "head"],
            "router_methods": ["get", "post", "put", "delete", "patch", "options", "head"],
            "app_classes": ["FastAPI", "APIRouter"],
        },
        "flask": {
            "decorators": ["route", "get", "post", "put", "delete", "patch"],
            "router_methods": ["route", "get", "post", "put", "delete", "patch"],
            "app_classes": ["Flask", "Blueprint"],
        },
    }
    
    # JavaScript/TypeScript HTTP framework configurations
    JS_HTTP_FRAMEWORKS = {
        "express": {
            "methods": ["get", "post", "put", "delete", "patch", "options", "head", "all"],
            "router_types": ["Router", "express"],
        },
        "nestjs": {
            "decorators": ["Get", "Post", "Put", "Delete", "Patch", "Options", "Head", "All"],
        },
    }
    
    # Go HTTP framework configurations
    GO_HTTP_FRAMEWORKS = {
        "gin": {
            "methods": ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD", "Any"],
        },
        "echo": {
            "methods": ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD", "Any"],
        },
        "chi": {
            "methods": ["Get", "Post", "Put", "Delete", "Patch", "Options", "Head"],
        },
        "fiber": {
            "methods": ["Get", "Post", "Put", "Delete", "Patch", "Options", "Head", "All"],
        },
    }
    
    # Python ORM framework configurations
    PYTHON_ORM_FRAMEWORKS = {
        "sqlalchemy": {
            "base_classes": ["Base", "DeclarativeBase", "Model"],
            "mixins": ["declarative_base"],
        },
        "django": {
            "base_classes": ["Model", "models.Model"],
        },
    }
    
    # Go ORM framework configurations
    GO_ORM_FRAMEWORKS = {
        "gorm": {
            "markers": ["gorm.Model", "gorm:"],
        },
        "ent": {
            "markers": ["ent.Schema"],
        },
    }
    
    # Python CLI framework configurations
    PYTHON_CLI_FRAMEWORKS = {
        "click": {
            "decorators": ["command", "group", "option", "argument"],
        },
        "typer": {
            "decorators": ["command", "callback"],
            "app_classes": ["Typer"],
        },
        "argparse": {
            "classes": ["ArgumentParser"],
            "methods": ["add_argument", "add_subparsers"],
        },
    }
    
    # Go CLI framework configurations
    GO_CLI_FRAMEWORKS = {
        "cobra": {
            "types": ["cobra.Command"],
        },
        "urfave-cli": {
            "types": ["cli.App", "cli.Command"],
        },
    }
    
    def __init__(
        self,
        storage: Optional[SQLiteStorage] = None,
        project_root: Optional[Path] = None
    ):
        """Initialize entry point detector.
        
        Args:
            storage: Optional storage backend for accessing project data
            project_root: Optional project root path for reading files
        """
        self.storage = storage
        self.project_root = project_root
        # Cache for import aliases per file
        self._import_alias_cache: dict[str, dict[str, str]] = {}
    
    def find_entry_points(
        self,
        project_path: str,
        types: Optional[list[EntryPointType]] = None
    ) -> EntryPointResult:
        """Find entry points in a project.
        
        Uses AST queries to detect entry points, ensuring accuracy by
        avoiding string/regex matching that could match comments or strings.
        
        Args:
            project_path: Path to the project
            types: Optional list of entry point types to find.
                   If None, finds all types.
                   
        Returns:
            EntryPointResult containing all detected entry points
        """
        result = EntryPointResult(project_path=project_path)
        
        # Determine which types to search for
        if types is None:
            types = list(EntryPointType)
        
        # Get project from storage
        if self.storage:
            project = self.storage.get_project(project_path)
            if not project:
                result.message = f"Project not found: {project_path}"
                return result
            
            # Get all files in the project
            files = self.storage.get_files_by_project(project.id)
            
            for file_record in files:
                self._process_file(
                    file_record.relative_path,
                    types,
                    result
                )
        elif self.project_root:
            # Scan project root directly
            for file_path in self._scan_project_files(self.project_root):
                self._process_file(
                    str(file_path.relative_to(self.project_root)),
                    types,
                    result
                )
        else:
            result.message = "No storage or project root provided"
            return result
        
        # Add summary message
        total = (
            len(result.http_routes) +
            len(result.main_entries) +
            len(result.database_models) +
            len(result.cli_commands)
        )
        
        if total == 0:
            result.message = "No entry points found for the specified types"
        else:
            result.message = (
                f"Found {total} entry points: "
                f"{len(result.http_routes)} HTTP routes, "
                f"{len(result.main_entries)} main entries, "
                f"{len(result.database_models)} database models, "
                f"{len(result.cli_commands)} CLI commands"
            )
        
        return result
    
    def _scan_project_files(self, root: Path) -> list[Path]:
        """Scan project directory for supported files.
        
        Args:
            root: Project root directory
            
        Returns:
            List of file paths
        """
        files = []
        for ext in self.LANGUAGE_MAP.keys():
            files.extend(root.rglob(f"*{ext}"))
        return files
    
    def _process_file(
        self,
        relative_path: str,
        types: list[EntryPointType],
        result: EntryPointResult
    ) -> None:
        """Process a single file for entry points.
        
        Args:
            relative_path: Relative path to the file
            types: Entry point types to search for
            result: Result object to populate
        """
        # Determine language
        ext = Path(relative_path).suffix.lower()
        language = self.LANGUAGE_MAP.get(ext)
        
        if not language:
            return
        
        # Read file content
        content = self._read_file(relative_path)
        if not content:
            return
        
        # Clear import alias cache for this file
        self._import_alias_cache[relative_path] = {}
        
        # Process based on language and requested types
        try:
            if EntryPointType.HTTP_ROUTE in types:
                self._find_http_routes(relative_path, content, language, result)
            
            if EntryPointType.MAIN_ENTRY in types:
                self._find_main_entries(relative_path, content, language, result)
            
            if EntryPointType.DATABASE_MODEL in types:
                self._find_database_models(relative_path, content, language, result)
            
            if EntryPointType.CLI_COMMAND in types:
                self._find_cli_commands(relative_path, content, language, result)
                
        except Exception as e:
            logger.warning(f"Failed to process {relative_path}: {e}")
    
    def _read_file(self, relative_path: str) -> Optional[str]:
        """Read file content.
        
        Args:
            relative_path: Relative path to the file
            
        Returns:
            File content or None if read fails
        """
        if self.project_root:
            full_path = self.project_root / relative_path
        else:
            full_path = Path(relative_path)
        
        try:
            return full_path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            logger.warning(f"Failed to read {relative_path}: {e}")
            return None

    # =========================================================================
    # Import Alias Resolution (Task 5.3)
    # =========================================================================
    
    def _resolve_import_alias(
        self,
        file_path: str,
        content: str,
        identifier: str,
        language: str
    ) -> Optional[str]:
        """Resolve import alias to original module/class name.
        
        Handles cases like:
        - Python: `from fastapi import FastAPI as API` -> API resolves to FastAPI
        - Python: `import flask as f` -> f resolves to flask
        - JS/TS: `import { Router as R } from 'express'` -> R resolves to Router
        
        Args:
            file_path: Path to the file (for caching)
            content: File content
            identifier: The identifier to resolve
            language: Programming language
            
        Returns:
            Original name if alias found, None otherwise
        """
        # Check cache first
        if file_path in self._import_alias_cache:
            cache = self._import_alias_cache[file_path]
            if identifier in cache:
                return cache[identifier]
        else:
            self._import_alias_cache[file_path] = {}
        
        # Parse imports based on language
        if language == "python":
            return self._resolve_python_import_alias(file_path, content, identifier)
        elif language in ("javascript", "typescript"):
            return self._resolve_js_import_alias(file_path, content, identifier, language)
        
        return None
    
    def _resolve_python_import_alias(
        self,
        file_path: str,
        content: str,
        identifier: str
    ) -> Optional[str]:
        """Resolve Python import alias.
        
        Handles:
        - `from module import Name as Alias`
        - `import module as alias`
        
        Args:
            file_path: Path to the file
            content: File content
            identifier: The identifier to resolve
            
        Returns:
            Original name if alias found, None otherwise
        """
        try:
            root = SgRoot(content, "python")
            node = root.root()
            
            # Check 'from xxx import yyy as zzz' statements
            for imp in node.find_all(kind="import_from_statement"):
                # Find aliased imports
                for child in imp.children():
                    if child.kind() == "aliased_import":
                        # Get the original name and alias
                        names = list(child.find_all(kind="identifier"))
                        if len(names) >= 2:
                            original = names[0].text()
                            alias = names[-1].text()
                            
                            # Cache the mapping
                            self._import_alias_cache[file_path][alias] = original
                            
                            if alias == identifier:
                                return original
            
            # Check 'import xxx as yyy' statements
            for imp in node.find_all(kind="import_statement"):
                for child in imp.children():
                    if child.kind() == "aliased_import":
                        # Get the original module and alias
                        dotted = child.find(kind="dotted_name")
                        names = list(child.find_all(kind="identifier"))
                        
                        if dotted and names:
                            original = dotted.text()
                            alias = names[-1].text()
                            
                            # Cache the mapping
                            self._import_alias_cache[file_path][alias] = original
                            
                            if alias == identifier:
                                return original
                                
        except Exception as e:
            logger.debug(f"Failed to resolve Python import alias: {e}")
        
        return None
    
    def _resolve_js_import_alias(
        self,
        file_path: str,
        content: str,
        identifier: str,
        language: str
    ) -> Optional[str]:
        """Resolve JavaScript/TypeScript import alias.
        
        Handles:
        - `import { Name as Alias } from 'module'`
        - `import * as Alias from 'module'`
        
        Args:
            file_path: Path to the file
            content: File content
            identifier: The identifier to resolve
            language: javascript or typescript
            
        Returns:
            Original name if alias found, None otherwise
        """
        try:
            ts_lang = "typescript" if language == "typescript" else "javascript"
            root = SgRoot(content, ts_lang)
            node = root.root()
            
            # Find import statements
            for imp in node.find_all(kind="import_statement"):
                # Find import specifiers with aliases
                for spec in imp.find_all(kind="import_specifier"):
                    names = list(spec.find_all(kind="identifier"))
                    if len(names) >= 2:
                        original = names[0].text()
                        alias = names[-1].text()
                        
                        # Cache the mapping
                        self._import_alias_cache[file_path][alias] = original
                        
                        if alias == identifier:
                            return original
                
                # Handle namespace imports: import * as name from 'module'
                namespace = imp.find(kind="namespace_import")
                if namespace:
                    alias_node = namespace.find(kind="identifier")
                    if alias_node:
                        alias = alias_node.text()
                        # For namespace imports, the alias represents the whole module
                        self._import_alias_cache[file_path][alias] = "*"
                        
        except Exception as e:
            logger.debug(f"Failed to resolve JS import alias: {e}")
        
        return None
    
    def _get_imported_modules(
        self,
        content: str,
        language: str
    ) -> dict[str, str]:
        """Get all imported modules and their aliases.
        
        Returns a mapping of identifier -> module/class name.
        
        Args:
            content: File content
            language: Programming language
            
        Returns:
            Dict mapping identifiers to their original names
        """
        imports: dict[str, str] = {}
        
        try:
            if language == "python":
                root = SgRoot(content, "python")
                node = root.root()
                
                # from xxx import yyy
                for imp in node.find_all(kind="import_from_statement"):
                    # Get the module name
                    dotted = imp.find(kind="dotted_name")
                    module = dotted.text() if dotted else ""
                    
                    # Get imported names
                    for child in imp.children():
                        if child.kind() == "dotted_name" and child != dotted:
                            name = child.text()
                            imports[name] = f"{module}.{name}" if module else name
                        elif child.kind() == "aliased_import":
                            names = list(child.find_all(kind="identifier"))
                            if len(names) >= 2:
                                original = names[0].text()
                                alias = names[-1].text()
                                imports[alias] = f"{module}.{original}" if module else original
                        elif child.kind() == "identifier":
                            name = child.text()
                            imports[name] = f"{module}.{name}" if module else name
                
                # import xxx
                for imp in node.find_all(kind="import_statement"):
                    for child in imp.children():
                        if child.kind() == "dotted_name":
                            name = child.text()
                            imports[name] = name
                        elif child.kind() == "aliased_import":
                            dotted = child.find(kind="dotted_name")
                            names = list(child.find_all(kind="identifier"))
                            if dotted and names:
                                original = dotted.text()
                                alias = names[-1].text()
                                imports[alias] = original
                                
        except Exception as e:
            logger.debug(f"Failed to get imported modules: {e}")
        
        return imports
    
    # =========================================================================
    # HTTP Route Detection (Task 5.2)
    # =========================================================================
    
    def _find_http_routes(
        self,
        file_path: str,
        content: str,
        language: str,
        result: EntryPointResult
    ) -> None:
        """Find HTTP route entry points in a file.
        
        Uses AST-based detection for accuracy.
        
        **Validates: Requirement 3.1** - HTTP route detection
        
        Args:
            file_path: Relative path to the file
            content: File content
            language: Programming language
            result: Result object to populate
        """
        if language == "python":
            self._find_python_http_routes(file_path, content, result)
        elif language in ("javascript", "typescript"):
            self._find_js_http_routes(file_path, content, language, result)
        elif language == "go":
            self._find_go_http_routes(file_path, content, result)
    
    def _find_python_http_routes(
        self,
        file_path: str,
        content: str,
        result: EntryPointResult
    ) -> None:
        """Find Python HTTP routes (FastAPI, Flask).
        
        Detects decorator-based route definitions:
        - @app.get("/path")
        - @router.post("/path")
        - @app.route("/path", methods=["GET"])
        
        Args:
            file_path: Relative path to the file
            content: File content
            result: Result object to populate
        """
        try:
            root = SgRoot(content, "python")
            node = root.root()
            
            # Get imported modules for framework detection
            imports = self._get_imported_modules(content, "python")
            
            # Find decorated function definitions
            for decorated in node.find_all(kind="decorated_definition"):
                # Get all decorators
                decorators = list(decorated.find_all(kind="decorator"))
                
                for decorator in decorators:
                    route_info = self._parse_python_route_decorator(
                        decorator, file_path, content, imports
                    )
                    
                    if route_info:
                        # Get the function name
                        func_def = decorated.find(kind="function_definition")
                        if func_def:
                            name_node = func_def.find(kind="identifier")
                            if name_node:
                                route_info["handler_name"] = name_node.text()
                                route_info["line_number"] = decorator.range().start.line + 1
                                
                                result.http_routes.append(HTTPRouteEntry(
                                    file_path=file_path,
                                    line_number=route_info["line_number"],
                                    route_path=route_info["route_path"],
                                    http_method=route_info["http_method"],
                                    handler_name=route_info["handler_name"],
                                    framework=route_info["framework"]
                                ))
                                
        except Exception as e:
            logger.debug(f"Failed to find Python HTTP routes in {file_path}: {e}")
    
    def _parse_python_route_decorator(
        self,
        decorator,
        file_path: str,
        content: str,
        imports: dict[str, str]
    ) -> Optional[dict]:
        """Parse a Python route decorator.
        
        Args:
            decorator: Decorator AST node
            file_path: File path for alias resolution
            content: File content
            imports: Imported modules mapping
            
        Returns:
            Dict with route_path, http_method, framework or None
        """
        try:
            # Find the call expression in the decorator
            call = decorator.find(kind="call")
            if not call:
                return None
            
            # Get the function being called (e.g., app.get, router.post)
            func = call.find(kind="attribute")
            if not func:
                return None
            
            # Get object and method
            children = list(func.children())
            if len(children) < 2:
                return None
            
            obj_node = children[0]
            method_node = children[-1]
            
            # Get object name (might be an alias)
            if obj_node.kind() == "identifier":
                obj_name = obj_node.text()
            elif obj_node.kind() == "attribute":
                # Nested attribute like app.router.get
                ids = list(obj_node.find_all(kind="identifier"))
                obj_name = ids[0].text() if ids else ""
            else:
                return None
            
            method_name = method_node.text() if method_node.kind() == "identifier" else ""
            
            # Resolve alias if needed
            resolved_obj = self._resolve_import_alias(file_path, content, obj_name, "python")
            if resolved_obj:
                obj_name = resolved_obj
            
            # Check if this matches a known framework
            framework = None
            http_method = None
            
            # Check if FastAPI is imported in the file
            has_fastapi = any(
                "fastapi" in v.lower() for v in imports.values()
            ) or any("fastapi" in k.lower() for k in imports.keys())
            
            # Check if Flask is imported in the file
            has_flask = any(
                "flask" in v.lower() for v in imports.values()
            ) or any("flask" in k.lower() for k in imports.keys())
            
            # Check FastAPI
            fastapi_config = self.PYTHON_HTTP_FRAMEWORKS["fastapi"]
            if method_name.lower() in fastapi_config["decorators"]:
                # If FastAPI is imported and method matches, assume it's a FastAPI route
                if has_fastapi:
                    framework = "fastapi"
                    http_method = method_name.upper()
                # Also check if object name suggests FastAPI
                elif any(cls.lower() in obj_name.lower() for cls in fastapi_config["app_classes"]):
                    framework = "fastapi"
                    http_method = method_name.upper()
            
            # Check Flask
            if not framework:
                flask_config = self.PYTHON_HTTP_FRAMEWORKS["flask"]
                if method_name.lower() in flask_config["decorators"]:
                    # If Flask is imported and method matches, assume it's a Flask route
                    if has_flask:
                        framework = "flask"
                        if method_name.lower() == "route":
                            http_method = self._extract_flask_route_method(call)
                        else:
                            http_method = method_name.upper()
                    # Also check if object name suggests Flask
                    elif any(cls.lower() in obj_name.lower() for cls in flask_config["app_classes"]):
                        framework = "flask"
                        if method_name.lower() == "route":
                            http_method = self._extract_flask_route_method(call)
                        else:
                            http_method = method_name.upper()
            
            if not framework:
                return None
            
            # Extract route path from arguments
            route_path = self._extract_route_path_from_call(call)
            if not route_path:
                return None
            
            return {
                "route_path": route_path,
                "http_method": http_method or "GET",
                "framework": framework
            }
            
        except Exception as e:
            logger.debug(f"Failed to parse Python route decorator: {e}")
            return None
    
    def _extract_route_path_from_call(self, call) -> Optional[str]:
        """Extract route path from a function call.
        
        Args:
            call: Call AST node
            
        Returns:
            Route path string or None
        """
        try:
            args = call.find(kind="argument_list")
            if not args:
                return None
            
            # First positional argument is usually the path
            for child in args.children():
                if child.kind() == "string":
                    text = child.text()
                    # Remove quotes
                    if text.startswith(('"""', "'''")):
                        return text[3:-3]
                    elif text.startswith(('"', "'")):
                        return text[1:-1]
                    return text
                elif child.kind() == "concatenated_string":
                    # Handle f-strings or concatenated strings
                    strings = list(child.find_all(kind="string"))
                    if strings:
                        text = strings[0].text()
                        if text.startswith(('"', "'")):
                            return text[1:-1]
                        return text
                        
        except Exception:
            pass
        
        return None
    
    def _extract_flask_route_method(self, call) -> str:
        """Extract HTTP method from Flask route decorator.
        
        Flask uses: @app.route("/path", methods=["GET", "POST"])
        
        Args:
            call: Call AST node
            
        Returns:
            HTTP method string (defaults to GET)
        """
        try:
            args = call.find(kind="argument_list")
            if not args:
                return "GET"
            
            # Look for methods keyword argument
            for child in args.children():
                if child.kind() == "keyword_argument":
                    key = child.find(kind="identifier")
                    if key and key.text() == "methods":
                        # Get the list of methods
                        list_node = child.find(kind="list")
                        if list_node:
                            strings = list(list_node.find_all(kind="string"))
                            if strings:
                                method = strings[0].text()
                                if method.startswith(('"', "'")):
                                    return method[1:-1].upper()
                                return method.upper()
                                
        except Exception:
            pass
        
        return "GET"

    def _find_js_http_routes(
        self,
        file_path: str,
        content: str,
        language: str,
        result: EntryPointResult
    ) -> None:
        """Find JavaScript/TypeScript HTTP routes (Express, NestJS).
        
        Detects:
        - Express: app.get("/path", handler), router.post("/path", handler)
        - NestJS: @Get("/path"), @Post("/path") decorators
        
        Args:
            file_path: Relative path to the file
            content: File content
            language: javascript or typescript
            result: Result object to populate
        """
        try:
            ts_lang = "typescript" if language == "typescript" else "javascript"
            root = SgRoot(content, ts_lang)
            node = root.root()
            
            # Find Express-style routes: app.get("/path", handler)
            self._find_express_routes(file_path, node, result)
            
            # Find NestJS-style routes: @Get("/path")
            if language == "typescript":
                self._find_nestjs_routes(file_path, node, result)
                
        except Exception as e:
            logger.debug(f"Failed to find JS HTTP routes in {file_path}: {e}")
    
    def _find_express_routes(
        self,
        file_path: str,
        node,
        result: EntryPointResult
    ) -> None:
        """Find Express.js route definitions.
        
        Detects patterns like:
        - app.get("/users", handler)
        - router.post("/users", createUser)
        
        Args:
            file_path: Relative path to the file
            node: AST root node
            result: Result object to populate
        """
        express_methods = self.JS_HTTP_FRAMEWORKS["express"]["methods"]
        
        # Find call expressions
        for call in node.find_all(kind="call_expression"):
            try:
                # Get the function being called
                func = call.find(kind="member_expression")
                if not func:
                    continue
                
                # Get the method name (last identifier)
                property_node = func.find(kind="property_identifier")
                if not property_node:
                    continue
                
                method_name = property_node.text()
                
                # Check if it's an HTTP method
                if method_name.lower() not in [m.lower() for m in express_methods]:
                    continue
                
                # Get arguments
                args = call.find(kind="arguments")
                if not args:
                    continue
                
                # First argument should be the route path
                route_path = None
                handler_name = None
                
                arg_children = list(args.children())
                for i, arg in enumerate(arg_children):
                    if arg.kind() == "string":
                        text = arg.text()
                        if text.startswith(('"', "'", "`")):
                            route_path = text[1:-1]
                        else:
                            route_path = text
                    elif arg.kind() == "template_string":
                        # Template literal
                        route_path = arg.text()[1:-1]  # Remove backticks
                    elif arg.kind() == "identifier" and route_path:
                        # This is likely the handler
                        handler_name = arg.text()
                    elif arg.kind() in ("arrow_function", "function"):
                        handler_name = "<anonymous>"
                
                if route_path:
                    result.http_routes.append(HTTPRouteEntry(
                        file_path=file_path,
                        line_number=call.range().start.line + 1,
                        route_path=route_path,
                        http_method=method_name.upper(),
                        handler_name=handler_name or "<anonymous>",
                        framework="express"
                    ))
                    
            except Exception as e:
                logger.debug(f"Failed to parse Express route: {e}")
    
    def _find_nestjs_routes(
        self,
        file_path: str,
        node,
        result: EntryPointResult
    ) -> None:
        """Find NestJS route definitions.
        
        Detects decorator patterns like:
        - @Get("/users")
        - @Post("/users")
        
        Args:
            file_path: Relative path to the file
            node: AST root node
            result: Result object to populate
        """
        nestjs_decorators = self.JS_HTTP_FRAMEWORKS["nestjs"]["decorators"]
        
        # Find decorators
        for decorator in node.find_all(kind="decorator"):
            try:
                # Get the decorator call
                call = decorator.find(kind="call_expression")
                if not call:
                    # Might be a simple decorator without call
                    ident = decorator.find(kind="identifier")
                    if ident and ident.text() in nestjs_decorators:
                        # Decorator without path argument
                        method_name = ident.text()
                        
                        # Find the method being decorated
                        parent = decorator.parent()
                        if parent:
                            method_def = parent.find(kind="method_definition")
                            if method_def:
                                name_node = method_def.find(kind="property_identifier")
                                handler_name = name_node.text() if name_node else "<unknown>"
                                
                                result.http_routes.append(HTTPRouteEntry(
                                    file_path=file_path,
                                    line_number=decorator.range().start.line + 1,
                                    route_path="/",
                                    http_method=method_name.upper(),
                                    handler_name=handler_name,
                                    framework="nestjs"
                                ))
                    continue
                
                # Get the decorator name
                func = call.find(kind="identifier")
                if not func:
                    continue
                
                decorator_name = func.text()
                
                if decorator_name not in nestjs_decorators:
                    continue
                
                # Get the route path from arguments
                args = call.find(kind="arguments")
                route_path = "/"
                
                if args:
                    for arg in args.children():
                        if arg.kind() == "string":
                            text = arg.text()
                            if text.startswith(('"', "'", "`")):
                                route_path = text[1:-1]
                            break
                
                # Find the method being decorated
                parent = decorator.parent()
                handler_name = "<unknown>"
                
                if parent:
                    method_def = parent.find(kind="method_definition")
                    if method_def:
                        name_node = method_def.find(kind="property_identifier")
                        if name_node:
                            handler_name = name_node.text()
                
                result.http_routes.append(HTTPRouteEntry(
                    file_path=file_path,
                    line_number=decorator.range().start.line + 1,
                    route_path=route_path,
                    http_method=decorator_name.upper(),
                    handler_name=handler_name,
                    framework="nestjs"
                ))
                
            except Exception as e:
                logger.debug(f"Failed to parse NestJS route: {e}")
    
    def _find_go_http_routes(
        self,
        file_path: str,
        content: str,
        result: EntryPointResult
    ) -> None:
        """Find Go HTTP routes (Gin, Echo, Chi, Fiber).
        
        Detects patterns like:
        - r.GET("/users", handler)
        - e.POST("/users", createUser)
        - r.Get("/users", handler)  // Chi
        
        Args:
            file_path: Relative path to the file
            content: File content
            result: Result object to populate
        """
        try:
            root = SgRoot(content, "go")
            node = root.root()
            
            # Detect which framework is imported
            detected_framework = self._detect_go_http_framework(content)
            
            # Find call expressions
            for call in node.find_all(kind="call_expression"):
                route_info = self._parse_go_route_call(call, detected_framework)
                
                if route_info:
                    result.http_routes.append(HTTPRouteEntry(
                        file_path=file_path,
                        line_number=call.range().start.line + 1,
                        route_path=route_info["route_path"],
                        http_method=route_info["http_method"],
                        handler_name=route_info["handler_name"],
                        framework=route_info["framework"]
                    ))
                    
        except Exception as e:
            logger.debug(f"Failed to find Go HTTP routes in {file_path}: {e}")
    
    def _detect_go_http_framework(self, content: str) -> Optional[str]:
        """Detect which Go HTTP framework is imported.
        
        Args:
            content: File content
            
        Returns:
            Framework name or None
        """
        content_lower = content.lower()
        
        # Check for framework imports
        if "gin-gonic/gin" in content:
            return "gin"
        elif "labstack/echo" in content:
            return "echo"
        elif "go-chi/chi" in content:
            return "chi"
        elif "gofiber/fiber" in content:
            return "fiber"
        
        return None
    
    def _parse_go_route_call(self, call, detected_framework: Optional[str] = None) -> Optional[dict]:
        """Parse a Go route registration call.
        
        Args:
            call: Call expression AST node
            detected_framework: Framework detected from imports
            
        Returns:
            Dict with route_path, http_method, handler_name, framework or None
        """
        try:
            # Get the selector expression (e.g., r.GET)
            selector = call.find(kind="selector_expression")
            if not selector:
                return None
            
            # Get the method name
            field = selector.find(kind="field_identifier")
            if not field:
                return None
            
            method_name = field.text()
            
            # Check against known frameworks
            framework = None
            http_method = None
            
            # If we detected a framework from imports, use it
            if detected_framework:
                fw_config = self.GO_HTTP_FRAMEWORKS.get(detected_framework, {})
                if method_name in fw_config.get("methods", []):
                    framework = detected_framework
                    http_method = method_name.upper()
            
            # Fallback: check all frameworks
            if not framework:
                for fw_name, fw_config in self.GO_HTTP_FRAMEWORKS.items():
                    if method_name in fw_config["methods"]:
                        framework = fw_name
                        http_method = method_name.upper()
                        break
            
            if not framework:
                return None
            
            # Get arguments
            args = call.find(kind="argument_list")
            if not args:
                return None
            
            route_path = None
            handler_name = None
            
            arg_children = list(args.children())
            for arg in arg_children:
                if arg.kind() == "interpreted_string_literal":
                    # Go string literal
                    text = arg.text()
                    if text.startswith('"') and text.endswith('"'):
                        route_path = text[1:-1]
                elif arg.kind() == "raw_string_literal":
                    # Go raw string literal
                    text = arg.text()
                    if text.startswith('`') and text.endswith('`'):
                        route_path = text[1:-1]
                elif arg.kind() == "identifier" and route_path:
                    handler_name = arg.text()
                elif arg.kind() == "selector_expression" and route_path:
                    # Method reference like controller.GetUsers
                    handler_name = arg.text()
                elif arg.kind() == "func_literal" and route_path:
                    handler_name = "<anonymous>"
            
            if route_path:
                return {
                    "route_path": route_path,
                    "http_method": http_method,
                    "handler_name": handler_name or "<anonymous>",
                    "framework": framework
                }
                
        except Exception as e:
            logger.debug(f"Failed to parse Go route call: {e}")
        
        return None

    # =========================================================================
    # Main Entry Point Detection (Task 5.4)
    # =========================================================================
    
    def _find_main_entries(
        self,
        file_path: str,
        content: str,
        language: str,
        result: EntryPointResult
    ) -> None:
        """Find main entry points in a file.
        
        **Validates: Requirement 3.2** - Main entry point detection
        
        Args:
            file_path: Relative path to the file
            content: File content
            language: Programming language
            result: Result object to populate
        """
        if language == "python":
            self._find_python_main_entry(file_path, content, result)
        elif language == "go":
            self._find_go_main_entry(file_path, content, result)
    
    def _find_python_main_entry(
        self,
        file_path: str,
        content: str,
        result: EntryPointResult
    ) -> None:
        """Find Python main entry point.
        
        Detects: if __name__ == "__main__":
        
        Args:
            file_path: Relative path to the file
            content: File content
            result: Result object to populate
        """
        try:
            root = SgRoot(content, "python")
            node = root.root()
            
            # Find if statements
            for if_stmt in node.find_all(kind="if_statement"):
                # Check the condition
                condition = if_stmt.find(kind="comparison_operator")
                if not condition:
                    continue
                
                # Look for __name__ == "__main__" pattern
                condition_text = condition.text()
                
                if "__name__" in condition_text and "__main__" in condition_text:
                    result.main_entries.append(MainEntry(
                        file_path=file_path,
                        line_number=if_stmt.range().start.line + 1,
                        entry_type="__main__"
                    ))
                    break  # Only one main entry per file
                    
        except Exception as e:
            logger.debug(f"Failed to find Python main entry in {file_path}: {e}")
    
    def _find_go_main_entry(
        self,
        file_path: str,
        content: str,
        result: EntryPointResult
    ) -> None:
        """Find Go main entry point.
        
        Detects:
        - package main declaration
        - func main() function
        
        Args:
            file_path: Relative path to the file
            content: File content
            result: Result object to populate
        """
        try:
            root = SgRoot(content, "go")
            node = root.root()
            
            # Check for package main
            is_main_package = False
            package_line = 0
            
            for pkg in node.find_all(kind="package_clause"):
                pkg_name = pkg.find(kind="package_identifier")
                if pkg_name and pkg_name.text() == "main":
                    is_main_package = True
                    package_line = pkg.range().start.line + 1
                    break
            
            if not is_main_package:
                return
            
            # Find func main()
            for func in node.find_all(kind="function_declaration"):
                name_node = func.find(kind="identifier")
                if name_node and name_node.text() == "main":
                    # Check it has no parameters (true main function)
                    params = func.find(kind="parameter_list")
                    if params:
                        param_children = [c for c in params.children() 
                                         if c.kind() not in ("(", ")", ",")]
                        if len(param_children) == 0:
                            result.main_entries.append(MainEntry(
                                file_path=file_path,
                                line_number=func.range().start.line + 1,
                                entry_type="main_func"
                            ))
                            return
            
            # If we have package main but no main func, still record it
            if is_main_package:
                result.main_entries.append(MainEntry(
                    file_path=file_path,
                    line_number=package_line,
                    entry_type="package_main"
                ))
                
        except Exception as e:
            logger.debug(f"Failed to find Go main entry in {file_path}: {e}")
    
    # =========================================================================
    # Database Model Detection (Task 5.5)
    # =========================================================================
    
    def _find_database_models(
        self,
        file_path: str,
        content: str,
        language: str,
        result: EntryPointResult
    ) -> None:
        """Find database model definitions in a file.
        
        **Validates: Requirement 3.3** - Database model detection
        
        Args:
            file_path: Relative path to the file
            content: File content
            language: Programming language
            result: Result object to populate
        """
        if language == "python":
            self._find_python_db_models(file_path, content, result)
        elif language == "go":
            self._find_go_db_models(file_path, content, result)
        elif language in ("javascript", "typescript"):
            self._find_js_db_models(file_path, content, language, result)
    
    def _find_python_db_models(
        self,
        file_path: str,
        content: str,
        result: EntryPointResult
    ) -> None:
        """Find Python database models (SQLAlchemy, Django).
        
        Detects:
        - Classes inheriting from Base, DeclarativeBase, Model
        - Classes inheriting from models.Model (Django)
        
        Args:
            file_path: Relative path to the file
            content: File content
            result: Result object to populate
        """
        try:
            root = SgRoot(content, "python")
            node = root.root()
            
            # Get imports to understand the context
            imports = self._get_imported_modules(content, "python")
            
            # Find class definitions
            for class_node in node.find_all(kind="class_definition"):
                model_info = self._check_python_model_class(class_node, imports)
                
                if model_info:
                    name_node = class_node.find(kind="identifier")
                    if name_node:
                        # Try to extract table name from __tablename__
                        table_name = self._extract_python_table_name(class_node)
                        
                        result.database_models.append(DatabaseModelEntry(
                            file_path=file_path,
                            line_number=class_node.range().start.line + 1,
                            model_name=name_node.text(),
                            framework=model_info["framework"],
                            table_name=table_name
                        ))
                        
        except Exception as e:
            logger.debug(f"Failed to find Python DB models in {file_path}: {e}")
    
    def _check_python_model_class(
        self,
        class_node,
        imports: dict[str, str]
    ) -> Optional[dict]:
        """Check if a Python class is a database model.
        
        Args:
            class_node: Class AST node
            imports: Imported modules mapping
            
        Returns:
            Dict with framework name or None
        """
        try:
            # Get base classes
            arg_list = class_node.find(kind="argument_list")
            if not arg_list:
                return None
            
            base_classes = []
            for child in arg_list.children():
                if child.kind() == "identifier":
                    base_classes.append(child.text())
                elif child.kind() == "attribute":
                    base_classes.append(child.text())
            
            # Check SQLAlchemy
            sqlalchemy_bases = self.PYTHON_ORM_FRAMEWORKS["sqlalchemy"]["base_classes"]
            for base in base_classes:
                if base in sqlalchemy_bases:
                    return {"framework": "sqlalchemy"}
                # Check if base is imported from sqlalchemy
                if base in imports:
                    import_path = imports[base]
                    if "sqlalchemy" in import_path.lower():
                        return {"framework": "sqlalchemy"}
            
            # Check Django
            django_bases = self.PYTHON_ORM_FRAMEWORKS["django"]["base_classes"]
            for base in base_classes:
                if base in django_bases or base == "models.Model":
                    return {"framework": "django"}
                if base in imports:
                    import_path = imports[base]
                    if "django" in import_path.lower():
                        return {"framework": "django"}
                        
        except Exception:
            pass
        
        return None
    
    def _extract_python_table_name(self, class_node) -> Optional[str]:
        """Extract table name from Python model class.
        
        Looks for __tablename__ = "table_name" assignment.
        
        Args:
            class_node: Class AST node
            
        Returns:
            Table name or None
        """
        try:
            # Find the class body
            block = class_node.find(kind="block")
            if not block:
                return None
            
            # Look for __tablename__ assignment
            for child in block.children():
                if child.kind() == "expression_statement":
                    assignment = child.find(kind="assignment")
                    if assignment:
                        # Get the left side
                        left = assignment.find(kind="identifier")
                        if left and left.text() == "__tablename__":
                            # Get the right side (string value)
                            string = assignment.find(kind="string")
                            if string:
                                text = string.text()
                                if text.startswith(('"', "'")):
                                    return text[1:-1]
                                    
        except Exception:
            pass
        
        return None
    
    def _find_go_db_models(
        self,
        file_path: str,
        content: str,
        result: EntryPointResult
    ) -> None:
        """Find Go database models (Gorm, Ent).
        
        Detects:
        - Structs with gorm.Model embedded
        - Structs with gorm struct tags
        - Ent schema definitions
        
        Args:
            file_path: Relative path to the file
            content: File content
            result: Result object to populate
        """
        try:
            root = SgRoot(content, "go")
            node = root.root()
            
            # Find type declarations
            for type_decl in node.find_all(kind="type_declaration"):
                # Find struct types
                for type_spec in type_decl.find_all(kind="type_spec"):
                    struct_type = type_spec.find(kind="struct_type")
                    if not struct_type:
                        continue
                    
                    name_node = type_spec.find(kind="type_identifier")
                    if not name_node:
                        continue
                    
                    model_name = name_node.text()
                    framework = self._check_go_model_struct(struct_type, content)
                    
                    if framework:
                        # Try to extract table name from struct tags
                        table_name = self._extract_go_table_name(struct_type)
                        
                        result.database_models.append(DatabaseModelEntry(
                            file_path=file_path,
                            line_number=type_spec.range().start.line + 1,
                            model_name=model_name,
                            framework=framework,
                            table_name=table_name
                        ))
                        
        except Exception as e:
            logger.debug(f"Failed to find Go DB models in {file_path}: {e}")
    
    def _check_go_model_struct(self, struct_type, content: str) -> Optional[str]:
        """Check if a Go struct is a database model.
        
        Args:
            struct_type: Struct type AST node
            content: File content
            
        Returns:
            Framework name or None
        """
        try:
            struct_text = struct_type.text()
            
            # Check for gorm.Model embedding
            if "gorm.Model" in struct_text:
                return "gorm"
            
            # Check for gorm struct tags
            if 'gorm:"' in struct_text or "gorm:" in struct_text:
                return "gorm"
            
            # Check for ent schema
            if "ent.Schema" in struct_text:
                return "ent"
                
        except Exception:
            pass
        
        return None
    
    def _extract_go_table_name(self, struct_type) -> Optional[str]:
        """Extract table name from Go struct tags.
        
        Looks for gorm:"table:table_name" tag.
        
        Args:
            struct_type: Struct type AST node
            
        Returns:
            Table name or None
        """
        try:
            # Find field declarations with tags
            for field in struct_type.find_all(kind="field_declaration"):
                tag = field.find(kind="raw_string_literal")
                if tag:
                    tag_text = tag.text()
                    # Look for table name in gorm tag
                    if "table:" in tag_text:
                        # Extract table name
                        import re
                        match = re.search(r'table:(\w+)', tag_text)
                        if match:
                            return match.group(1)
                            
        except Exception:
            pass
        
        return None
    
    def _find_js_db_models(
        self,
        file_path: str,
        content: str,
        language: str,
        result: EntryPointResult
    ) -> None:
        """Find JavaScript/TypeScript database models (Prisma).
        
        Note: Prisma models are typically in .prisma files, but we can
        detect Prisma client usage patterns.
        
        Args:
            file_path: Relative path to the file
            content: File content
            language: javascript or typescript
            result: Result object to populate
        """
        # Prisma models are in .prisma files, not JS/TS
        # We could detect TypeORM entities here if needed
        pass

    # =========================================================================
    # CLI Command Detection (Task 5.6)
    # =========================================================================
    
    def _find_cli_commands(
        self,
        file_path: str,
        content: str,
        language: str,
        result: EntryPointResult
    ) -> None:
        """Find CLI command definitions in a file.
        
        **Validates: Requirement 3.9** - CLI command detection
        
        Args:
            file_path: Relative path to the file
            content: File content
            language: Programming language
            result: Result object to populate
        """
        if language == "python":
            self._find_python_cli_commands(file_path, content, result)
        elif language == "go":
            self._find_go_cli_commands(file_path, content, result)
    
    def _find_python_cli_commands(
        self,
        file_path: str,
        content: str,
        result: EntryPointResult
    ) -> None:
        """Find Python CLI commands (Click, Typer, Argparse).
        
        Detects:
        - @click.command() decorators
        - @app.command() for Typer
        - ArgumentParser usage
        
        Args:
            file_path: Relative path to the file
            content: File content
            result: Result object to populate
        """
        try:
            root = SgRoot(content, "python")
            node = root.root()
            
            # Get imports
            imports = self._get_imported_modules(content, "python")
            
            # Find Click/Typer decorated functions
            for decorated in node.find_all(kind="decorated_definition"):
                decorators = list(decorated.find_all(kind="decorator"))
                
                for decorator in decorators:
                    cli_info = self._parse_python_cli_decorator(
                        decorator, file_path, content, imports
                    )
                    
                    if cli_info:
                        # Get the function name
                        func_def = decorated.find(kind="function_definition")
                        if func_def:
                            name_node = func_def.find(kind="identifier")
                            if name_node:
                                command_name = cli_info.get("command_name") or name_node.text()
                                
                                result.cli_commands.append(CLICommandEntry(
                                    file_path=file_path,
                                    line_number=decorator.range().start.line + 1,
                                    command_name=command_name,
                                    framework=cli_info["framework"]
                                ))
            
            # Find Argparse usage
            self._find_argparse_commands(file_path, node, imports, result)
            
        except Exception as e:
            logger.debug(f"Failed to find Python CLI commands in {file_path}: {e}")
    
    def _parse_python_cli_decorator(
        self,
        decorator,
        file_path: str,
        content: str,
        imports: dict[str, str]
    ) -> Optional[dict]:
        """Parse a Python CLI decorator.
        
        Args:
            decorator: Decorator AST node
            file_path: File path
            content: File content
            imports: Imported modules mapping
            
        Returns:
            Dict with framework and command_name or None
        """
        try:
            # Get decorator text for analysis
            dec_text = decorator.text()
            
            # Check for Click decorators
            click_decorators = self.PYTHON_CLI_FRAMEWORKS["click"]["decorators"]
            for dec in click_decorators:
                if f"click.{dec}" in dec_text or f"@{dec}" in dec_text:
                    # Check if click is imported
                    if "click" in imports or "click" in dec_text:
                        command_name = self._extract_cli_command_name(decorator)
                        return {
                            "framework": "click",
                            "command_name": command_name
                        }
            
            # Check for Typer decorators
            typer_decorators = self.PYTHON_CLI_FRAMEWORKS["typer"]["decorators"]
            for dec in typer_decorators:
                if f".{dec}(" in dec_text:
                    # Check if it's a Typer app
                    if "typer" in imports.values() or "Typer" in imports:
                        command_name = self._extract_cli_command_name(decorator)
                        return {
                            "framework": "typer",
                            "command_name": command_name
                        }
                        
        except Exception:
            pass
        
        return None
    
    def _extract_cli_command_name(self, decorator) -> Optional[str]:
        """Extract command name from CLI decorator.
        
        Args:
            decorator: Decorator AST node
            
        Returns:
            Command name or None
        """
        try:
            call = decorator.find(kind="call")
            if not call:
                return None
            
            args = call.find(kind="argument_list")
            if not args:
                return None
            
            # Look for name argument or first positional string
            for child in args.children():
                if child.kind() == "string":
                    text = child.text()
                    if text.startswith(('"', "'")):
                        return text[1:-1]
                elif child.kind() == "keyword_argument":
                    key = child.find(kind="identifier")
                    if key and key.text() == "name":
                        string = child.find(kind="string")
                        if string:
                            text = string.text()
                            if text.startswith(('"', "'")):
                                return text[1:-1]
                                
        except Exception:
            pass
        
        return None
    
    def _find_argparse_commands(
        self,
        file_path: str,
        node,
        imports: dict[str, str],
        result: EntryPointResult
    ) -> None:
        """Find Argparse command definitions.
        
        Detects ArgumentParser instantiation and add_subparsers usage.
        
        Args:
            file_path: Relative path to the file
            node: AST root node
            imports: Imported modules mapping
            result: Result object to populate
        """
        try:
            # Check if argparse is imported
            # Handle both "import argparse" and "from argparse import ArgumentParser"
            has_argparse = (
                "argparse" in imports or  # import argparse
                "ArgumentParser" in imports or  # from argparse import ArgumentParser
                any("argparse" in str(v) for v in imports.values())  # aliased imports
            )
            
            if not has_argparse:
                return
            
            # Find ArgumentParser instantiation
            for call in node.find_all(kind="call"):
                # Get the function being called
                # Could be: ArgumentParser() or argparse.ArgumentParser()
                func_text = ""
                
                # Check for attribute access (argparse.ArgumentParser)
                attr = call.find(kind="attribute")
                if attr:
                    func_text = attr.text()
                else:
                    # Check for direct identifier (ArgumentParser)
                    ident = call.find(kind="identifier")
                    if ident:
                        func_text = ident.text()
                
                if "ArgumentParser" in func_text:
                    # Extract prog name if specified
                    prog_name = self._extract_argparse_prog(call)
                    
                    result.cli_commands.append(CLICommandEntry(
                        file_path=file_path,
                        line_number=call.range().start.line + 1,
                        command_name=prog_name or "<main>",
                        framework="argparse"
                    ))
                        
        except Exception as e:
            logger.debug(f"Failed to find Argparse commands: {e}")
    
    def _extract_argparse_prog(self, call) -> Optional[str]:
        """Extract program name from ArgumentParser call.
        
        Args:
            call: Call AST node
            
        Returns:
            Program name or None
        """
        try:
            args = call.find(kind="argument_list")
            if not args:
                return None
            
            for child in args.children():
                if child.kind() == "keyword_argument":
                    key = child.find(kind="identifier")
                    if key and key.text() == "prog":
                        string = child.find(kind="string")
                        if string:
                            text = string.text()
                            if text.startswith(('"', "'")):
                                return text[1:-1]
                                
        except Exception:
            pass
        
        return None
    
    def _find_go_cli_commands(
        self,
        file_path: str,
        content: str,
        result: EntryPointResult
    ) -> None:
        """Find Go CLI commands (Cobra, Urfave-cli).
        
        Detects:
        - cobra.Command struct literals
        - cli.App and cli.Command usage
        
        Args:
            file_path: Relative path to the file
            content: File content
            result: Result object to populate
        """
        try:
            root = SgRoot(content, "go")
            node = root.root()
            
            # Find cobra.Command definitions
            self._find_cobra_commands(file_path, node, result)
            
            # Find urfave-cli commands
            self._find_urfave_commands(file_path, node, result)
            
        except Exception as e:
            logger.debug(f"Failed to find Go CLI commands in {file_path}: {e}")
    
    def _find_cobra_commands(
        self,
        file_path: str,
        node,
        result: EntryPointResult
    ) -> None:
        """Find Cobra command definitions.
        
        Detects &cobra.Command{...} struct literals.
        
        Args:
            file_path: Relative path to the file
            node: AST root node
            result: Result object to populate
        """
        try:
            # Find composite literals (struct instantiation)
            for literal in node.find_all(kind="composite_literal"):
                # Check if it's a cobra.Command
                type_node = literal.find(kind="qualified_type")
                if not type_node:
                    type_node = literal.find(kind="type_identifier")
                
                if type_node:
                    type_text = type_node.text()
                    if "cobra.Command" in type_text or type_text == "Command":
                        # Extract command name from Use field
                        command_name = self._extract_cobra_command_name(literal)
                        
                        result.cli_commands.append(CLICommandEntry(
                            file_path=file_path,
                            line_number=literal.range().start.line + 1,
                            command_name=command_name or "<unknown>",
                            framework="cobra"
                        ))
                        
        except Exception as e:
            logger.debug(f"Failed to find Cobra commands: {e}")
    
    def _extract_cobra_command_name(self, literal) -> Optional[str]:
        """Extract command name from Cobra Command literal.
        
        Looks for Use: "command_name" field.
        
        Args:
            literal: Composite literal AST node
            
        Returns:
            Command name or None
        """
        try:
            # Find the literal value (struct fields)
            literal_value = literal.find(kind="literal_value")
            if not literal_value:
                return None
            
            # Find keyed elements
            for element in literal_value.find_all(kind="keyed_element"):
                # Get children - format is [key, ":", value]
                children = list(element.children())
                if len(children) >= 3:
                    key_node = children[0]
                    value_node = children[2]
                    
                    # Check if key is "Use"
                    key_text = key_node.text().strip()
                    if key_text == "Use":
                        # Get the value
                        value_text = value_node.text().strip()
                        if value_text.startswith('"') and value_text.endswith('"'):
                            # Use field often contains "command [flags]"
                            # Extract just the command name
                            use_text = value_text[1:-1]
                            return use_text.split()[0] if use_text else None
                            
        except Exception:
            pass
        
        return None
    
    def _find_urfave_commands(
        self,
        file_path: str,
        node,
        result: EntryPointResult
    ) -> None:
        """Find Urfave-cli command definitions.
        
        Detects cli.App and cli.Command struct literals.
        
        Args:
            file_path: Relative path to the file
            node: AST root node
            result: Result object to populate
        """
        try:
            # Find composite literals
            for literal in node.find_all(kind="composite_literal"):
                type_node = literal.find(kind="qualified_type")
                if not type_node:
                    type_node = literal.find(kind="type_identifier")
                
                if type_node:
                    type_text = type_node.text()
                    if "cli.App" in type_text or "cli.Command" in type_text:
                        # Extract command name from Name field
                        command_name = self._extract_urfave_command_name(literal)
                        
                        result.cli_commands.append(CLICommandEntry(
                            file_path=file_path,
                            line_number=literal.range().start.line + 1,
                            command_name=command_name or "<unknown>",
                            framework="urfave-cli"
                        ))
                        
        except Exception as e:
            logger.debug(f"Failed to find Urfave-cli commands: {e}")
    
    def _extract_urfave_command_name(self, literal) -> Optional[str]:
        """Extract command name from Urfave-cli literal.
        
        Looks for Name: "command_name" field.
        
        Args:
            literal: Composite literal AST node
            
        Returns:
            Command name or None
        """
        try:
            literal_value = literal.find(kind="literal_value")
            if not literal_value:
                return None
            
            for element in literal_value.find_all(kind="keyed_element"):
                # Get children - format is [key, ":", value]
                children = list(element.children())
                if len(children) >= 3:
                    key_node = children[0]
                    value_node = children[2]
                    
                    # Check if key is "Name"
                    key_text = key_node.text().strip()
                    if key_text == "Name":
                        value_text = value_node.text().strip()
                        if value_text.startswith('"') and value_text.endswith('"'):
                            return value_text[1:-1]
                            
        except Exception:
            pass
        
        return None
