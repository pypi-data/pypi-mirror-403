"""Tool guide module for lazy-loading tool documentation.

This module provides the get_tool_guide tool that allows AI to query
detailed tool documentation on-demand, reducing initial token consumption.
"""

import json
from pathlib import Path
from fastmcp import FastMCP

# Path to the JSON guide file
GUIDE_FILE = Path(__file__).parent / "tool_guides.json"

# Cache for loaded guides
_guides_cache: dict | None = None


def load_guides() -> dict:
    """Load tool guides from JSON file with caching."""
    global _guides_cache
    if _guides_cache is None:
        with open(GUIDE_FILE, "r", encoding="utf-8") as f:
            _guides_cache = json.load(f)
    return _guides_cache


def register_guide_tools(mcp: FastMCP) -> None:
    """Register guide tools with the MCP server."""

    @mcp.tool
    def get_tool_guide(
        tool_name: str | None = None,
        category: str | None = None,
        task: str | None = None,
        list_only: bool = False
    ) -> dict:
        """获取工具详细使用指南（按需加载）| Get detailed tool usage guide (lazy load)
        
        Args:
            tool_name: 工具名（获取单个工具详情）
            category: 分类过滤 project/stats/analysis/quality/context
            task: 任务描述（返回推荐工具）
            list_only: 仅返回工具列表（不含详情）
        """
        guides = load_guides()
        
        # 1. Query single tool
        if tool_name:
            tool = guides["tools"].get(tool_name)
            if not tool:
                return {
                    "error": "TOOL_NOT_FOUND",
                    "details": f"Tool '{tool_name}' not found",
                    "available_tools": list(guides["tools"].keys())
                }
            return {"success": True, "tool": tool}
        
        # 2. Query by category
        if category:
            cat = guides["categories"].get(category)
            if not cat:
                return {
                    "error": "CATEGORY_NOT_FOUND",
                    "details": f"Category '{category}' not found",
                    "available_categories": list(guides["categories"].keys())
                }
            
            if list_only:
                return {
                    "success": True,
                    "category": category,
                    "name_zh": cat["name_zh"],
                    "name_en": cat["name_en"],
                    "tools": cat["tools"]
                }
            
            # Return full details for all tools in category
            tools = {}
            for t in cat["tools"]:
                if t in guides["tools"]:
                    tools[t] = guides["tools"][t]
            
            return {
                "success": True,
                "category": category,
                "name_zh": cat["name_zh"],
                "name_en": cat["name_en"],
                "description_zh": cat["description_zh"],
                "description_en": cat["description_en"],
                "tools": tools
            }
        
        # 3. Query by task
        if task:
            task_lower = task.lower()
            
            for mapping in guides["task_mapping"]:
                if (task_lower in mapping["task_zh"].lower() or 
                    task_lower in mapping["task_en"].lower()):
                    primary = mapping["primary"]
                    related = mapping["related"]
                    
                    result = {
                        "success": True,
                        "task": task,
                        "matched_task_zh": mapping["task_zh"],
                        "matched_task_en": mapping["task_en"],
                        "recommended_tool": primary,
                        "related_tools": related,
                        "tool_detail": guides["tools"].get(primary)
                    }
                    
                    # Include related tool details if any
                    if related:
                        result["related_tool_details"] = {
                            t: guides["tools"].get(t) 
                            for t in related 
                            if t in guides["tools"]
                        }
                    
                    return result
            
            # No exact match, return all task mappings for reference
            return {
                "success": False,
                "message": f"No exact match for task: {task}",
                "available_tasks": [
                    {"zh": m["task_zh"], "en": m["task_en"], "tool": m["primary"]}
                    for m in guides["task_mapping"]
                ]
            }
        
        # 4. Return overview (list_only mode)
        if list_only:
            return {
                "success": True,
                "categories": {
                    k: {
                        "name_zh": v["name_zh"],
                        "name_en": v["name_en"],
                        "tools": v["tools"]
                    }
                    for k, v in guides["categories"].items()
                },
                "total_tools": len(guides["tools"]),
                "message": "Use tool_name, category, or task parameter to get details"
            }
        
        # 5. Return full overview with task mapping
        return {
            "success": True,
            "categories": {
                k: {
                    "name_zh": v["name_zh"],
                    "name_en": v["name_en"],
                    "description_zh": v["description_zh"],
                    "description_en": v["description_en"],
                    "tools": v["tools"]
                }
                for k, v in guides["categories"].items()
            },
            "task_mapping": [
                {
                    "task_zh": m["task_zh"],
                    "task_en": m["task_en"],
                    "primary": m["primary"],
                    "related": m["related"]
                }
                for m in guides["task_mapping"]
            ],
            "total_tools": len(guides["tools"]),
            "message": "Use tool_name, category, or task parameter to get specific details"
        }
