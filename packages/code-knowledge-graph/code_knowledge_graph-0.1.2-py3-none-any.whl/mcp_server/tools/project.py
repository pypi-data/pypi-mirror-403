"""Project management MCP tools.

Tools for scanning projects and managing project data.
"""

from pathlib import Path
from fastmcp import FastMCP

from .base import get_storage, get_project_service, filter_external_deps


def register_project_tools(mcp: FastMCP) -> None:
    """Register project management tools with the MCP server."""

    @mcp.tool
    def scan_project(path: str, incremental: bool = True, include_external: bool = False) -> dict:
        """扫描项目代码依赖（必须先执行）| Scan project dependencies (required first). 详见 get_tool_guide("scan_project")
        
        Args:
            path: 项目路径
            incremental: 增量更新 (default: true)
            include_external: 包含第三方依赖 (default: false)
        """
        project_path = Path(path)
        if not project_path.exists():
            return {"error": "NOT_FOUND", "details": f"Path does not exist: {path}"}
        
        service = get_project_service()
        result = service.scan_project(str(project_path.resolve()), incremental=incremental)
        
        response = {
            "success": True,
            "project_id": result.project_id,
            "project_path": result.project_path,
            "project_name": result.project_name,
            "file_count": result.total_files,
            "file_types": result.file_types,
            "scan_mode": result.scan_mode
        }
        
        if include_external:
            response["external_deps"] = result.external_deps
        
        return response

    @mcp.tool
    def get_project_tree(
        path: str, 
        directories_only: bool = False, 
        max_depth: int = -1,
        output_format: str = "json"
    ) -> dict:
        """获取项目目录树 | Get project directory tree. 详见 get_tool_guide("get_project_tree")
        
        Args:
            path: 项目路径
            directories_only: 仅文件夹 (default: false)
            max_depth: 最大深度，-1无限制 (default: -1)
            output_format: json/ascii (default: json)
        """
        from core.tree import TreeBuilder
        
        project_path = Path(path)
        if not project_path.exists():
            return {"error": "NOT_FOUND", "details": f"Path does not exist: {path}"}
        
        builder = TreeBuilder(project_path)
        
        if output_format == "ascii":
            tree_output = builder.to_ascii(
                directories_only=directories_only, 
                max_depth=max_depth
            )
            return {
                "success": True,
                "project_path": str(project_path.resolve()),
                "directories_only": directories_only,
                "max_depth": max_depth,
                "format": "ascii",
                "tree": tree_output
            }
        else:
            tree = builder.build(
                directories_only=directories_only, 
                max_depth=max_depth
            )
            return {
                "success": True,
                "project_path": str(project_path.resolve()),
                "directories_only": directories_only,
                "max_depth": max_depth,
                "format": "json",
                "tree": tree.to_dict()
            }

    @mcp.tool
    def list_projects(paths_only: bool = False) -> dict:
        """获取已扫描项目列表 | List scanned projects. 详见 get_tool_guide("list_projects")
        
        Args:
            paths_only: 仅返回路径 (default: false)
        """
        storage = get_storage()
        projects = storage.list_projects()
        
        if paths_only:
            return {
                "success": True,
                "paths": [p.path for p in projects],
                "total": len(projects)
            }
        
        return {
            "success": True,
            "projects": [
                {
                    "id": p.id,
                    "name": p.name,
                    "path": p.path,
                    "file_count": p.file_count,
                    "last_scanned": p.last_scanned.isoformat() if hasattr(p.last_scanned, 'isoformat') else str(p.last_scanned)
                }
                for p in projects
            ],
            "total": len(projects)
        }

    @mcp.tool
    def get_project_info(path: str) -> dict:
        """获取项目详情 | Get project details. 详见 get_tool_guide("get_project_info")
        
        Args:
            path: 项目路径
        """
        service = get_project_service()
        info = service.get_project_info(str(Path(path).resolve()))
        
        if info is None:
            return {"error": "NOT_FOUND", "details": f"Project not found: {path}"}
        
        return {
            "success": True,
            **info
        }

    @mcp.tool
    def delete_project(path: str) -> dict:
        """删除已扫描项目 | Delete scanned project. 详见 get_tool_guide("delete_project")
        
        Args:
            path: 项目路径
        """
        service = get_project_service()
        deleted = service.delete_project(str(Path(path).resolve()))
        
        if not deleted:
            return {"error": "NOT_FOUND", "details": f"Project not found: {path}"}
        
        return {
            "success": True,
            "message": f"Project deleted: {path}"
        }
