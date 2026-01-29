"""Statistics and analysis MCP tools.

Tools for file statistics, reference ranking, and depth analysis.
"""

import logging
from pathlib import Path
from fastmcp import FastMCP

from .base import get_stats_service, get_function_analysis, filter_external_deps


def register_stats_tools(mcp: FastMCP) -> None:
    """Register statistics tools with the MCP server."""

    @mcp.tool
    def get_file_stats(path: str, subdirectory: str | None = None) -> dict:
        """获取文件类型统计 | Get file type stats. 详见 get_tool_guide("get_file_stats")
        
        Args:
            path: 项目路径
            subdirectory: 子目录过滤（可选）
        """
        service = get_stats_service()
        response = service.get_file_type_stats(str(Path(path).resolve()), subdirectory=subdirectory)
        
        if response is None:
            return {"error": "NOT_FOUND", "details": f"Project not found: {path}"}
        
        return {
            "project_path": response.project_path,
            "subdirectory": subdirectory,
            "total_files": response.total_files,
            "stats": [
                {
                    "type": s.file_type,
                    "count": s.count,
                    "percentage": s.percentage,
                    "total_size": s.total_size
                }
                for s in response.stats
            ]
        }

    @mcp.tool
    def get_reference_ranking(
        path: str, 
        limit: int = 20, 
        file_type: str | None = None,
        include_external: bool = False
    ) -> dict:
        """获取被引用最多的文件 | Get top referenced files. 详见 get_tool_guide("get_reference_ranking")
        
        Args:
            path: 项目路径
            limit: 结果数量 (default: 20)
            file_type: 文件类型过滤（可选）
            include_external: 包含第三方 (default: false)
        """
        service = get_stats_service()
        response = service.get_reference_ranking(
            str(Path(path).resolve()), 
            limit=limit, 
            file_type=file_type,
            include_external=include_external
        )
        
        if response is None:
            return {"error": "NOT_FOUND", "details": f"Project not found: {path}"}
        
        return {
            "project_path": response.project_path,
            "limit": limit,
            "file_type_filter": file_type,
            "include_external": include_external,
            "total_results": response.total_results,
            "results": [
                {
                    "file": r.file_path,
                    "count": r.reference_count,
                    "references": r.referencing_files
                }
                for r in response.results
            ]
        }

    @mcp.tool
    def get_depth_analysis(path: str, subdirectory: str | None = None) -> dict:
        """获取目录层级分析 | Get depth analysis. 详见 get_tool_guide("get_depth_analysis")
        
        Args:
            path: 项目路径
            subdirectory: 子目录过滤（可选）
        """
        service = get_stats_service()
        response = service.get_depth_analysis(str(Path(path).resolve()), subdirectory=subdirectory)
        
        if response is None:
            return {"error": "NOT_FOUND", "details": f"Project not found: {path}"}
        
        return {
            "project_path": response.project_path,
            "subdirectory": subdirectory,
            "directory_depth": response.directory_depth,
            "file_depth": response.file_depth
        }

    @mcp.tool
    def get_function_relations(files: list[str], include_external: bool = False) -> dict:
        """获取文件间函数调用关系（最多50文件）| Get function relations. 详见 get_tool_guide("get_function_relations")

        Args:
            files: 文件路径列表（最多50个）
            include_external: 包含第三方调用 (default: false)
        """
        if len(files) > 50:
            return {"error": "LIMIT_EXCEEDED", "details": "Maximum 50 files allowed"}
        
        try:
            service = get_function_analysis()
            result = service.analyze_files(files)
            data = service.to_dict(result)
            return filter_external_deps(data, include_external)
        except FileNotFoundError as e:
            return {"error": "NOT_FOUND", "details": str(e)}

    @mcp.tool
    def get_parse_logs(level: str = "WARNING", limit: int = 100) -> dict:
        """获取解析日志 | Get parse logs. 详见 get_tool_guide("get_parse_logs")
        
        Args:
            level: DEBUG/INFO/WARNING/ERROR (default: WARNING)
            limit: 日志条数 (default: 100)
        """
        # Get logs from the parser logger
        logger = logging.getLogger("code_knowledge_graph.parser")
        
        # Get handler if exists, otherwise return empty
        logs = []
        for handler in logger.handlers:
            if hasattr(handler, 'buffer'):
                logs = list(handler.buffer)[-limit:]
                break
        
        return {
            "success": True,
            "level": level,
            "logs": logs,
            "total": len(logs),
            "message": "Use scan_project to generate parse logs | 使用 scan_project 生成解析日志"
        }

    @mcp.tool  
    def set_log_level(level: str = "WARNING") -> dict:
        """设置日志级别 | Set log level. 详见 get_tool_guide("set_log_level")
        
        Args:
            level: DEBUG/INFO/WARNING/ERROR (default: WARNING)
        """
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR"]
        level = level.upper()
        
        if level not in valid_levels:
            return {"error": "INVALID_LEVEL", "details": f"Valid levels: {valid_levels}"}
        
        logger = logging.getLogger("code_knowledge_graph.parser")
        logger.setLevel(getattr(logging, level))
        
        return {
            "success": True,
            "level": level,
            "message": f"Log level set to {level}"
        }
