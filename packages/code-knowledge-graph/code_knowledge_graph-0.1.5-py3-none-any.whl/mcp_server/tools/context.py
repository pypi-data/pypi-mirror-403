"""Related code context MCP tools.

Tools for getting related code context (Repo Map).
"""

from pathlib import Path
from fastmcp import FastMCP

from core.services import RelatedContextService, SkeletonMode
from .base import get_storage


def register_context_tools(mcp: FastMCP) -> None:
    """Register context tools with the MCP server."""

    @mcp.tool
    def get_related_code_context(
        project_path: str, 
        file_path: str, 
        hops: int = 1,
        mode: str = "skeleton",
        include_external: bool = False
    ) -> dict:
        """获取关联代码上下文（Repo Map）| Get related code context. 详见 get_tool_guide("get_related_code_context")
        
        Args:
            project_path: 项目路径
            file_path: 目标文件相对路径
            hops: 依赖跳数 1-3 (default: 1)
            mode: full/skeleton/signature_only (default: skeleton)
            include_external: 包含第三方 (default: false)
        """
        project_root = Path(project_path)
        if not project_root.exists():
            return {"error": "NOT_FOUND", "details": f"Path does not exist: {project_path}"}
        
        # Validate mode
        valid_modes = ["full", "skeleton", "signature_only"]
        if mode not in valid_modes:
            return {"error": "INVALID_PARAMS", "details": f"Invalid mode: {mode}. Must be one of: {valid_modes}"}
        
        hops = max(1, min(3, hops))  # Clamp to 1-3
        
        storage = get_storage()
        service = RelatedContextService(storage, project_root)
        
        # Convert mode string to SkeletonMode enum
        skeleton_mode = SkeletonMode(mode)
        
        result = service.get_related_context(
            str(project_root.resolve()), 
            file_path, 
            hops=hops,
            mode=skeleton_mode,
            include_external=include_external
        )
        return service.to_dict(result)
