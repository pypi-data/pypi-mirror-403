"""Enhanced MCP tools for Code Knowledge Graph.

New tools added in the code-knowledge-graph-enhancement spec:
- trace_call_chain: Function call chain tracing
- find_entry_points: Project entry point discovery
- symbol_search: AST-based symbol search
- detect_circular_deps: Circular dependency detection
- get_import_graph: Import relationship graph (with target_file support)
- analyze_change_impact: Change impact analysis (with enhanced test detection)
- find_all_usages: Symbol usage finder (with usage type classification)
- get_complexity_metrics: Code complexity analysis
- check_layer_violations: Architecture layer checking
- find_dead_code: Dead code detection
"""

from pathlib import Path
from fastmcp import FastMCP

from core.services import (
    SymbolSearchService,
    SymbolType,
    SkeletonMode,
    EntryPointDetector,
    EntryPointType,
    DependencyAnalysisService,
    UsageFinderService,
)
from core.services.call_chain import CallChainService
from core.services.complexity_analyzer import ComplexityAnalyzer
from core.services.layer_checker import LayerChecker
from core.services.dead_code_finder import DeadCodeFinder
from .base import get_storage


def register_enhanced_tools(mcp: FastMCP) -> None:
    """Register enhanced tools with the MCP server."""

    @mcp.tool
    def trace_call_chain(
        project_path: str,
        start_symbol: str,
        direction: str = "downstream",
        depth: int = 5,
        limit_per_level: int = 20,
        prune_standard_libs: bool = True
    ) -> dict:
        """追踪函数调用链 | Trace call chains. 详见 get_tool_guide("trace_call_chain")
        
        Args:
            project_path: 项目路径
            start_symbol: 起始函数名
            direction: upstream/downstream (default: downstream)
            depth: 深度 1-10 (default: 5)
            limit_per_level: 每层限制 1-100 (default: 20)
            prune_standard_libs: 剪枝标准库 (default: true)
        """
        project_root = Path(project_path)
        if not project_root.exists():
            return {"error": "NOT_FOUND", "details": f"Path does not exist: {project_path}"}
        
        if direction not in ("upstream", "downstream"):
            return {"error": "INVALID_PARAMS", "details": f"Invalid direction: {direction}. Must be 'upstream' or 'downstream'"}
        
        # Clamp parameters
        depth = max(1, min(10, depth))
        limit_per_level = max(1, min(100, limit_per_level))
        
        storage = get_storage()
        
        # Check if project is scanned
        project = storage.get_project(str(project_root.resolve()))
        if not project:
            return {"error": "NOT_SCANNED", "details": "Please scan the project first using scan_project | 请先使用scan_project扫描项目"}
        
        service = CallChainService(storage)
        result = service.trace_call_chain(
            project_path=str(project_root.resolve()),
            start_symbol=start_symbol,
            direction=direction,
            depth=depth,
            limit_per_level=limit_per_level,
            prune_standard_libs=prune_standard_libs
        )
        
        # Convert result to dict
        chains_data = []
        for chain in result.chains:
            chain_nodes = []
            for node in chain:
                chain_nodes.append({
                    "function_name": node.function_name,
                    "file_path": node.file_path,
                    "line_number": node.line_number,
                    "container_name": node.container_name,
                    "call_type": node.call_type,
                    "is_cycle": node.is_cycle,
                    "depth": node.depth
                })
            chains_data.append(chain_nodes)
        
        return {
            "success": True,
            "start_symbol": result.start_symbol,
            "direction": result.direction,
            "depth": result.depth,
            "chains": chains_data,
            "has_cycle": result.has_cycle,
            "truncated": result.truncated,
            "message": result.message
        }

    @mcp.tool
    def find_entry_points(
        project_path: str,
        types: list[str] | None = None
    ) -> dict:
        """查找项目入口点 | Find entry points. 详见 get_tool_guide("find_entry_points")
        
        Args:
            project_path: 项目路径
            types: 类型列表 [http_routes, main_entry, database_models, cli_commands]（可选）
        """
        project_root = Path(project_path)
        if not project_root.exists():
            return {"error": "NOT_FOUND", "details": f"Path does not exist: {project_path}"}
        
        storage = get_storage()
        
        # Check if project is scanned
        project = storage.get_project(str(project_root.resolve()))
        if not project:
            return {"error": "NOT_SCANNED", "details": "Please scan the project first using scan_project | 请先使用scan_project扫描项目"}
        
        # Convert type strings to EntryPointType enum
        entry_point_types = None
        if types:
            try:
                entry_point_types = [EntryPointType(t) for t in types]
            except ValueError as e:
                return {"error": "INVALID_PARAMS", "details": f"Invalid entry point type: {e}"}
        
        detector = EntryPointDetector(storage=storage, project_root=project_root)
        result = detector.find_entry_points(
            project_path=str(project_root.resolve()),
            types=entry_point_types
        )
        
        return {
            "success": True,
            "project_path": result.project_path,
            "http_routes": [
                {
                    "file_path": r.file_path,
                    "line_number": r.line_number,
                    "route_path": r.route_path,
                    "http_method": r.http_method,
                    "handler_name": r.handler_name,
                    "framework": r.framework
                }
                for r in result.http_routes
            ],
            "main_entries": [
                {
                    "file_path": e.file_path,
                    "line_number": e.line_number,
                    "entry_type": e.entry_type
                }
                for e in result.main_entries
            ],
            "database_models": [
                {
                    "file_path": m.file_path,
                    "line_number": m.line_number,
                    "model_name": m.model_name,
                    "framework": m.framework,
                    "table_name": m.table_name
                }
                for m in result.database_models
            ],
            "cli_commands": [
                {
                    "file_path": c.file_path,
                    "line_number": c.line_number,
                    "command_name": c.command_name,
                    "framework": c.framework
                }
                for c in result.cli_commands
            ],
            "message": result.message
        }

    @mcp.tool
    def symbol_search(
        project_path: str,
        query: str,
        symbol_types: list[str] | None = None,
        case_sensitive: bool = False,
        prefix_match: bool = True,
        limit: int = 50
    ) -> dict:
        """AST符号搜索 | Symbol search. 详见 get_tool_guide("symbol_search")
        
        Args:
            project_path: 项目路径
            query: 符号名称
            symbol_types: [function, class, method, variable, struct, interface]（可选）
            case_sensitive: 大小写敏感 (default: false)
            prefix_match: 前缀匹配 (default: true)
            limit: 结果限制 1-200 (default: 50)
        """
        project_root = Path(project_path)
        if not project_root.exists():
            return {"error": "NOT_FOUND", "details": f"Path does not exist: {project_path}"}
        
        if not query or not query.strip():
            return {"error": "INVALID_PARAMS", "details": "Query cannot be empty"}
        
        # Clamp limit
        limit = max(1, min(200, limit))
        
        storage = get_storage()
        
        # Check if project is scanned
        project = storage.get_project(str(project_root.resolve()))
        if not project:
            return {"error": "NOT_SCANNED", "details": "Please scan the project first using scan_project | 请先使用scan_project扫描项目"}
        
        # Convert symbol type strings to SymbolType enum
        types_enum = None
        if symbol_types:
            try:
                types_enum = [SymbolType(t) for t in symbol_types]
            except ValueError as e:
                return {"error": "INVALID_PARAMS", "details": f"Invalid symbol type: {e}"}
        
        service = SymbolSearchService(storage)
        result = service.search(
            project_path=str(project_root.resolve()),
            query=query.strip(),
            symbol_types=types_enum,
            case_sensitive=case_sensitive,
            prefix_match=prefix_match,
            limit=limit
        )
        
        return {
            "success": True,
            "query": result.query,
            "results": [
                {
                    "name": r.name,
                    "symbol_type": r.symbol_type.value,
                    "file_path": r.file_path,
                    "line_number": r.line_number,
                    "signature": r.signature,
                    "docstring": r.docstring,
                    "container_name": r.container_name,
                    "is_exported": r.is_exported,
                    "match_score": r.match_score
                }
                for r in result.results
            ],
            "total_count": result.total_count,
            "truncated": result.truncated
        }

    @mcp.tool
    def detect_circular_deps(
        project_path: str,
        scope: str = "file"
    ) -> dict:
        """检测循环依赖 | Detect circular deps. 详见 get_tool_guide("detect_circular_deps")

        Args:
            project_path: 项目路径
            scope: file/module/package (default: file)
        """
        project_root = Path(project_path)
        if not project_root.exists():
            return {"error": "NOT_FOUND", "details": f"Path does not exist: {project_path}"}

        storage = get_storage()

        # Check if project is scanned
        project = storage.get_project(str(project_root.resolve()))
        if not project:
            return {"error": "NOT_SCANNED", "details": "Please scan the project first using scan_project | 请先使用scan_project扫描项目"}

        service = DependencyAnalysisService(storage)
        result = service.detect_circular_deps(
            project_path=str(project_root.resolve()),
            scope=scope
        )

        if result.message and "Invalid" in result.message:
            return {"error": "INVALID_PARAMS", "details": result.message}

        return {
            "success": True,
            "project_path": result.project_path,
            "scope": result.scope,
            "cycles": result.cycles,
            "count": result.count,
            "message": result.message
        }

    @mcp.tool
    def get_import_graph(
        project_path: str,
        scope: str = "internal",
        group_by: str = "file",
        target_file: str | None = None,
        direction: str = "both",
        depth: int = 2
    ) -> dict:
        """获取导入关系图 | Get import graph. 详见 get_tool_guide("get_import_graph")

        Args:
            project_path: 项目路径
            scope: internal/external/all (default: internal)
            group_by: file/directory/package (default: file)
            target_file: 聚焦文件（可选）
            direction: imports/imported_by/both (default: both)
            depth: 跳数 1-10 (default: 2)
        """
        project_root = Path(project_path)
        if not project_root.exists():
            return {"error": "NOT_FOUND", "details": f"Path does not exist: {project_path}"}

        storage = get_storage()

        # Check if project is scanned
        project = storage.get_project(str(project_root.resolve()))
        if not project:
            return {"error": "NOT_SCANNED", "details": "Please scan the project first using scan_project | 请先使用scan_project扫描项目"}

        # Clamp depth
        depth = max(1, min(10, depth))

        service = DependencyAnalysisService(storage)
        result = service.get_import_graph(
            project_path=str(project_root.resolve()),
            scope=scope,
            group_by=group_by,
            target_file=target_file,
            direction=direction,
            depth=depth
        )

        if result.message and "Invalid" in result.message:
            return {"error": "INVALID_PARAMS", "details": result.message}

        return {
            "success": True,
            "project_path": result.project_path,
            "scope": result.scope,
            "group_by": result.group_by,
            "nodes": [
                {
                    "id": n.id,
                    "type": n.node_type,
                    "file_count": n.file_count
                }
                for n in result.nodes
            ],
            "edges": [
                {
                    "from": e.from_node,
                    "to": e.to_node,
                    "type": e.edge_type,
                    "weight": e.weight
                }
                for e in result.edges
            ],
            "external": result.external,
            "message": result.message
        }

    @mcp.tool
    def analyze_change_impact(
        project_path: str,
        modified_files: list[str],
        depth: int = 3
    ) -> dict:
        """分析修改影响范围 | Analyze change impact. 详见 get_tool_guide("analyze_change_impact")

        Args:
            project_path: 项目路径
            modified_files: 修改的文件列表（相对路径）
            depth: 影响深度 1-10 (default: 3)
        """
        project_root = Path(project_path)
        if not project_root.exists():
            return {"error": "NOT_FOUND", "details": f"Path does not exist: {project_path}"}

        if not modified_files:
            return {"error": "INVALID_PARAMS", "details": "modified_files cannot be empty"}

        # Clamp depth
        depth = max(1, min(10, depth))

        storage = get_storage()

        # Check if project is scanned
        project = storage.get_project(str(project_root.resolve()))
        if not project:
            return {"error": "NOT_SCANNED", "details": "Please scan the project first using scan_project | 请先使用scan_project扫描项目"}

        service = DependencyAnalysisService(storage)
        result = service.analyze_change_impact(
            project_path=str(project_root.resolve()),
            modified_files=modified_files,
            depth=depth
        )

        return {
            "success": True,
            "project_path": result.project_path,
            "modified": result.modified_files,
            "directly_affected": result.directly_affected,
            "indirectly_affected": result.indirectly_affected,
            "affected_tests": result.affected_tests,
            "total_files_at_risk": result.total_files_at_risk,
            "message": result.message
        }

    @mcp.tool
    def find_all_usages(
        project_path: str,
        symbol_name: str,
        symbol_type: str | None = None,
        limit: int = 100,
        classify_types: bool = True
    ) -> dict:
        """查找符号所有使用位置 | Find all usages. 详见 get_tool_guide("find_all_usages")

        Args:
            project_path: 项目路径
            symbol_name: 符号名称
            symbol_type: 类型过滤（可选）
            limit: 结果限制 1-500 (default: 100)
            classify_types: 分类引用类型 (default: true)
        """
        project_root = Path(project_path)
        if not project_root.exists():
            return {"error": "NOT_FOUND", "details": f"Path does not exist: {project_path}"}

        if not symbol_name or not symbol_name.strip():
            return {"error": "INVALID_PARAMS", "details": "symbol_name cannot be empty"}

        # Clamp limit
        limit = max(1, min(500, limit))

        storage = get_storage()

        # Check if project is scanned
        project = storage.get_project(str(project_root.resolve()))
        if not project:
            return {"error": "NOT_SCANNED", "details": "Please scan the project first using scan_project | 请先使用scan_project扫描项目"}

        service = UsageFinderService(storage)
        result = service.find_all_usages(
            project_path=str(project_root.resolve()),
            symbol_name=symbol_name.strip(),
            symbol_type=symbol_type,
            limit=limit,
            classify_types=classify_types
        )

        definition_data = None
        if result.definition:
            definition_data = {
                "file": result.definition.file_path,
                "line": result.definition.line_number,
                "type": result.definition.symbol_type,
                "signature": result.definition.signature,
                "container": result.definition.container_name
            }

        response = {
            "success": True,
            "symbol": result.symbol_name,
            "definition": definition_data,
            "usages": [
                {
                    "file": u.file_path,
                    "line": u.line_number,
                    "type": u.usage_type,
                    "context": u.context,
                    "container": u.container_name
                }
                for u in result.usages
            ],
            "total": result.total,
            "message": result.message
        }

        # Add classified usages if available
        if result.usages_by_type:
            response["usages_by_type"] = result.usages_by_type.to_dict()
        if result.summary:
            response["summary"] = result.summary

        return response

    @mcp.tool
    def get_complexity_metrics(
        project_path: str,
        min_complexity: int = 10,
        limit: int = 50,
        directory: str | None = None
    ) -> dict:
        """分析代码复杂度 | Get complexity metrics. 详见 get_tool_guide("get_complexity_metrics")

        Args:
            project_path: 项目路径
            min_complexity: 最小阈值 1-100 (default: 10)
            limit: 热点数量 1-500 (default: 50)
            directory: 限定目录（可选）
        """
        project_root = Path(project_path)
        if not project_root.exists():
            return {"error": "NOT_FOUND", "details": f"Path does not exist: {project_path}"}

        storage = get_storage()

        # Check if project is scanned
        project = storage.get_project(str(project_root.resolve()))
        if not project:
            return {"error": "NOT_SCANNED", "details": "Please scan the project first using scan_project | 请先使用scan_project扫描项目"}

        # Clamp parameters
        min_complexity = max(1, min(100, min_complexity))
        limit = max(1, min(500, limit))

        analyzer = ComplexityAnalyzer(storage)
        result = analyzer.get_complexity_metrics(
            project_path=str(project_root.resolve()),
            min_complexity=min_complexity,
            limit=limit,
            directory=directory
        )

        return analyzer.to_dict(result)

    @mcp.tool
    def check_layer_violations(
        project_path: str,
        rules: dict[str, list[str]] | None = None,
        custom_patterns: dict[str, list[str]] | None = None
    ) -> dict:
        """检查架构分层违规 | Check layer violations. 详见 get_tool_guide("check_layer_violations")

        Args:
            project_path: 项目路径
            rules: 自定义规则 {layer: [allowed_deps]}（可选）
            custom_patterns: 自定义目录模式 {layer: [patterns]}（可选）
        """
        project_root = Path(project_path)
        if not project_root.exists():
            return {"error": "NOT_FOUND", "details": f"Path does not exist: {project_path}"}

        storage = get_storage()

        # Check if project is scanned
        project = storage.get_project(str(project_root.resolve()))
        if not project:
            return {"error": "NOT_SCANNED", "details": "Please scan the project first using scan_project | 请先使用scan_project扫描项目"}

        checker = LayerChecker(storage)
        result = checker.check_layer_violations(
            project_path=str(project_root.resolve()),
            rules=rules,
            custom_patterns=custom_patterns
        )

        return checker.to_dict(result)

    @mcp.tool
    def find_dead_code(
        project_path: str,
        include_exported: bool = False,
        include_tests: bool = False,
        confidence_threshold: str = "medium"
    ) -> dict:
        """检测死代码 | Find dead code. 详见 get_tool_guide("find_dead_code")

        Args:
            project_path: 项目路径
            include_exported: 包含导出符号 (default: false)
            include_tests: 包含测试文件 (default: false)
            confidence_threshold: low/medium/high (default: medium)
        """
        project_root = Path(project_path)
        if not project_root.exists():
            return {"error": "NOT_FOUND", "details": f"Path does not exist: {project_path}"}

        storage = get_storage()

        # Check if project is scanned
        project = storage.get_project(str(project_root.resolve()))
        if not project:
            return {"error": "NOT_SCANNED", "details": "Please scan the project first using scan_project | 请先使用scan_project扫描项目"}

        # Validate confidence threshold
        valid_thresholds = ["low", "medium", "high"]
        if confidence_threshold not in valid_thresholds:
            return {"error": "INVALID_PARAMS", "details": f"Invalid confidence_threshold: {confidence_threshold}. Must be one of {valid_thresholds}"}

        finder = DeadCodeFinder(storage)
        result = finder.find_dead_code(
            project_path=str(project_root.resolve()),
            include_exported=include_exported,
            include_tests=include_tests,
            confidence_threshold=confidence_threshold
        )

        return finder.to_dict(result)
