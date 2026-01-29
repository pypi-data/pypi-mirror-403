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
        """扫描并分析项目代码依赖 | Scan and analyze project code dependencies.
        
        Args:
            path: 项目路径 | Project path
            incremental: 是否增量更新 | Whether to use incremental update
            include_external: 是否包含第三方依赖 | Whether to include external dependencies
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
        """获取项目目录树结构 | Get project directory tree structure.
        
        Args:
            path: 项目路径 | Project path
            directories_only: 是否只返回文件夹（不含文件）| Whether to return only directories (no files)
            max_depth: 最大深度限制，-1表示无限制 | Maximum depth limit, -1 for unlimited
            output_format: 输出格式 "json" 或 "ascii" | Output format "json" or "ascii"
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
        """获取所有已扫描的项目列表 | Get list of all scanned projects.
        
        Returns a list of projects that have been scanned and stored in the database.
        
        Args:
            paths_only: 是否只返回路径列表 | Whether to return only paths
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
        """获取项目详细信息 | Get project details.
        
        Args:
            path: 项目路径 | Project path
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
        """删除已扫描的项目 | Delete a scanned project.
        
        Args:
            path: 项目路径 | Project path
        """
        service = get_project_service()
        deleted = service.delete_project(str(Path(path).resolve()))
        
        if not deleted:
            return {"error": "NOT_FOUND", "details": f"Project not found: {path}"}
        
        return {
            "success": True,
            "message": f"Project deleted: {path}"
        }
