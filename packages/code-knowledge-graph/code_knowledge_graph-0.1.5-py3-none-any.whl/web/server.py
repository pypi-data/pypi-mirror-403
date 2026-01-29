"""FastAPI web server for Code Knowledge Graph visualization and API."""

from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Query, HTTPException, Body
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel, Field

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.scanner import CodeScanner
from core.graph import GraphBuilder
from core.tree import TreeBuilder
from core.storage import SQLiteStorage
from core.services import (
    StatsService,
    ProjectService,
    FunctionAnalysisService,
    RelatedContextService,
)


# Pydantic models for request/response
class ScanRequest(BaseModel):
    """Request model for project scan."""
    path: str = Field(..., description="Project path to scan")
    incremental: bool = Field(True, description="Use incremental update")


class FunctionAnalysisRequest(BaseModel):
    """Request model for function analysis."""
    files: list[str] = Field(..., max_length=10, description="File paths to analyze")


class ProjectStatsResponse(BaseModel):
    """Response model for project statistics."""
    project_path: str
    total_files: int
    subdirectory: Optional[str] = None
    stats: list[dict]


# Initialize application
app = FastAPI(
    title="Code Knowledge Graph",
    version="2.0.0",
    description="Code dependency analysis and visualization service"
)

# Setup Jinja2 templates
templates_dir = Path(__file__).parent / "templates"
env = Environment(loader=FileSystemLoader(templates_dir))

# Storage and services - initialized lazily
_storage = None
_stats_service = None
_project_service = None
_function_analysis = None


def get_storage():
    """Get or create storage instance."""
    global _storage
    if _storage is None:
        db_path = Path(__file__).parent.parent / "code_knowledge.db"
        _storage = SQLiteStorage(str(db_path))
    return _storage


def get_stats_service():
    """Get or create stats service."""
    global _stats_service
    if _stats_service is None:
        _stats_service = StatsService(get_storage())
    return _stats_service


def get_project_service():
    """Get or create project service."""
    global _project_service
    if _project_service is None:
        _project_service = ProjectService(get_storage())
    return _project_service


def get_function_analysis():
    """Get or create function analysis service."""
    global _function_analysis
    if _function_analysis is None:
        _function_analysis = FunctionAnalysisService()
    return _function_analysis


# ============================================================================
# Visualization Endpoints
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def index():
    """Serve the main visualization page."""
    template = env.get_template("index.html")
    return template.render()


@app.get("/api/tree")
async def get_tree(path: str = Query(..., description="Project path to analyze")):
    """Get directory tree for a project."""
    project_path = Path(path)

    if not project_path.exists():
        raise HTTPException(status_code=404, detail=f"Path not found: {path}")

    if not project_path.is_dir():
        raise HTTPException(status_code=400, detail=f"Path is not a directory: {path}")

    try:
        builder = TreeBuilder(project_path)
        tree = builder.build()
        return tree.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/graph")
async def get_graph(path: str = Query(..., description="Project path to analyze")):
    """Get dependency graph for a project."""
    project_path = Path(path)

    if not project_path.exists():
        raise HTTPException(status_code=404, detail=f"Path not found: {path}")

    if not project_path.is_dir():
        raise HTTPException(status_code=400, detail=f"Path is not a directory: {path}")

    try:
        scanner = CodeScanner(project_path)
        files = scanner.scan()

        builder = GraphBuilder(project_path)
        graph = builder.build(files)

        return graph.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Project Management Endpoints
# ============================================================================

@app.get("/api/projects")
async def list_projects():
    """List all scanned projects.
    
    Returns a list of projects that have been scanned and stored in the database.
    """
    try:
        storage = get_storage()
        projects = storage.list_projects()
        
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/projects/{path:path}/graph")
async def get_stored_graph(path: str):
    """Get dependency graph from database for a stored project.
    
    This reads from the database instead of re-scanning the filesystem.
    """
    try:
        storage = get_storage()
        project = storage.get_project(path)
        
        if project is None:
            raise HTTPException(status_code=404, detail=f"Project not found in database: {path}")
        
        # Get all files for this project
        files = storage.get_files_by_project(project.id)
        
        # Build nodes
        nodes = []
        file_id_to_path = {}
        
        for f in files:
            file_id_to_path[f.id] = f.relative_path
            nodes.append({
                "id": f.relative_path,
                "label": f.relative_path.split("/")[-1].split("\\")[-1],
                "type": f.file_type,
                "size": f.size
            })
        
        # Build edges from imports
        edges = []
        external_nodes = set()
        
        for f in files:
            imports = storage.get_imports_by_file(f.id)
            for imp in imports:
                if imp.resolved_file_id and imp.resolved_file_id in file_id_to_path:
                    # Internal import - resolved to a file in the project
                    edges.append({
                        "from": f.relative_path,
                        "to": file_id_to_path[imp.resolved_file_id],
                        "type": imp.import_type
                    })
                else:
                    # External import
                    external_id = f"external:{imp.module}"
                    if external_id not in external_nodes:
                        external_nodes.add(external_id)
                        nodes.append({
                            "id": external_id,
                            "label": imp.module,
                            "type": "external",
                            "size": 0
                        })
                    edges.append({
                        "from": f.relative_path,
                        "to": external_id,
                        "type": imp.import_type
                    })
        
        return {
            "nodes": nodes,
            "edges": edges
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/projects/scan")
async def scan_project(request: ScanRequest):
    """Scan a project and store in database.

    This endpoint scans the project, builds dependency graph,
    and stores results for subsequent queries.
    """
    project_path = Path(request.path)

    if not project_path.exists():
        raise HTTPException(status_code=404, detail=f"Path not found: {request.path}")

    if not project_path.is_dir():
        raise HTTPException(status_code=400, detail=f"Path is not a directory: {request.path}")

    try:
        service = get_project_service()
        result = service.scan_project(
            str(project_path.resolve()),
            incremental=request.incremental
        )

        return {
            "success": True,
            "project_id": result.project_id,
            "project_path": result.project_path,
            "project_name": result.project_name,
            "file_count": result.total_files,
            "file_types": result.file_types,
            "external_deps": result.external_deps,
            "scan_mode": result.scan_mode,
            "stats": result.stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/projects/{path:path}/info")
async def get_project_info(path: str):
    """Get information about a stored project."""
    try:
        service = get_project_service()
        info = service.get_project_info(path)

        if info is None:
            raise HTTPException(
                status_code=404,
                detail=f"Project not found: {path}"
            )

        return info
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/projects/{path:path}")
async def delete_project(path: str):
    """Delete a project from storage."""
    try:
        service = get_project_service()
        deleted = service.delete_project(path)

        if not deleted:
            raise HTTPException(
                status_code=404,
                detail=f"Project not found: {path}"
            )

        return {"success": True, "message": f"Project deleted: {path}"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Statistics Endpoints
# ============================================================================

@app.get("/api/stats")
async def get_stats(path: str = Query(..., description="Project path to analyze")):
    """Get basic project statistics (legacy endpoint)."""
    project_path = Path(path)

    if not project_path.exists():
        raise HTTPException(status_code=404, detail=f"Path not found: {path}")

    try:
        scanner = CodeScanner(project_path)
        files = scanner.scan()

        stats = {
            "total_files": len(files),
            "by_type": {},
            "total_size": 0,
            "total_imports": 0,
        }

        for f in files:
            stats["by_type"][f.file_type] = stats["by_type"].get(f.file_type, 0) + 1
            stats["total_size"] += f.size
            stats["total_imports"] += len(f.imports)

        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/projects/{path:path}/stats")
async def get_file_stats(
    path: str,
    subdirectory: Optional[str] = Query(None, description="Subdirectory filter")
):
    """Get file type statistics for a stored project.

    Returns distribution of file types with counts and percentages.
    """
    try:
        service = get_stats_service()
        response = service.get_file_type_stats(path, subdirectory=subdirectory)

        if response is None:
            raise HTTPException(
                status_code=404,
                detail=f"Project not found: {path}"
            )

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
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/projects/{path:path}/references")
async def get_reference_ranking(
    path: str,
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    file_type: Optional[str] = Query(None, description="File type filter")
):
    """Get files ranked by incoming reference count.

    Returns the most referenced files in the project.
    """
    try:
        service = get_stats_service()
        response = service.get_reference_ranking(
            path,
            limit=limit,
            file_type=file_type
        )

        if response is None:
            raise HTTPException(
                status_code=404,
                detail=f"Project not found: {path}"
            )

        return {
            "project_path": response.project_path,
            "limit": limit,
            "file_type_filter": file_type,
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
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/projects/{path:path}/depth")
async def get_depth_analysis(
    path: str,
    subdirectory: Optional[str] = Query(None, description="Subdirectory filter")
):
    """Get directory and file depth analysis.

    Returns min/max/average file depths and distribution.
    """
    try:
        service = get_stats_service()
        response = service.get_depth_analysis(path, subdirectory=subdirectory)

        if response is None:
            raise HTTPException(
                status_code=404,
                detail=f"Project not found: {path}"
            )

        return {
            "project_path": response.project_path,
            "subdirectory": subdirectory,
            "directory_depth": response.directory_depth,
            "file_depth": response.file_depth
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Function Analysis Endpoints
# ============================================================================

@app.post("/api/functions/analyze")
async def analyze_functions(request: FunctionAnalysisRequest):
    """Analyze function-level dependencies between files.

    Maximum 10 files can be analyzed at once.
    Returns function definitions and call relationships.
    """
    if len(request.files) > 10:
        raise HTTPException(
            status_code=400,
            detail="Maximum 10 files allowed for function analysis"
        )

    try:
        service = get_function_analysis()
        result = service.analyze_files(request.files)
        return service.to_dict(result)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/functions/callers")
async def get_function_callers(
    files: str = Query(..., description="Comma-separated file paths"),
    function_name: str = Query(..., description="Function name to find callers for")
):
    """Find all functions that call a specific function."""
    file_list = [f.strip() for f in files.split(",") if f.strip()]

    if len(file_list) > 10:
        raise HTTPException(
            status_code=400,
            detail="Maximum 10 files allowed"
        )

    try:
        service = get_function_analysis()
        callers = service.get_function_callers(file_list, function_name)

        return {
            "function": function_name,
            "callers": [
                {
                    "caller_function": r.caller_function,
                    "caller_file": r.caller_file,
                    "caller_line": r.caller_line
                }
                for r in callers
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/functions/callees")
async def get_function_callees(
    files: str = Query(..., description="Comma-separated file paths"),
    function_name: str = Query(..., description="Function name to find callees for")
):
    """Find all functions called by a specific function."""
    file_list = [f.strip() for f in files.split(",") if f.strip()]

    if len(file_list) > 10:
        raise HTTPException(
            status_code=400,
            detail="Maximum 10 files allowed"
        )

    try:
        service = get_function_analysis()
        callees = service.get_function_callees(file_list, function_name)

        return {
            "function": function_name,
            "callees": [
                {
                    "callee_function": r.callee_function,
                    "callee_file": r.callee_file,
                    "callee_line": r.callee_line,
                    "is_external": r.is_external
                }
                for r in callees
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Related Code Context Endpoints (Repo Map)
# ============================================================================

@app.get("/api/projects/{path:path}/context/{file_path:path}")
async def get_related_code_context(
    path: str,
    file_path: str,
    hops: int = Query(1, ge=1, le=3, description="Dependency hops")
):
    """Get related code context for a file (Repo Map).

    Returns the target file and related files within N hops,
    including function/class signatures (not implementations).
    """
    project_path = Path(path)

    if not project_path.exists():
        raise HTTPException(status_code=404, detail=f"Project not found: {path}")

    try:
        storage = get_storage()
        service = RelatedContextService(storage, project_path)

        result = service.get_related_context(
            str(project_path.resolve()),
            file_path,
            hops=hops
        )

        return service.to_dict(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Health and Debug Endpoints
# ============================================================================

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "2.0.0"}


@app.get("/api/logs")
async def get_parse_logs(
    level: str = Query("WARNING", description="Log level filter"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum log entries")
):
    """Get parsing logs.
    
    Returns recent parsing logs for debugging.
    """
    import logging
    
    logger = logging.getLogger("code_knowledge_graph.parser")
    logs = []
    
    # Get logs from memory handler
    for handler in logger.handlers:
        if hasattr(handler, 'buffer'):
            logs = list(handler.buffer)[-limit:]
            break
    
    # Filter by level
    level_map = {"DEBUG": 10, "INFO": 20, "WARNING": 30, "ERROR": 40}
    min_level = level_map.get(level.upper(), 30)
    
    filtered_logs = [
        log for log in logs 
        if level_map.get(log.get("level", "WARNING"), 30) >= min_level
    ]
    
    return {
        "success": True,
        "level": level,
        "logs": filtered_logs,
        "total": len(filtered_logs)
    }


@app.post("/api/logs/level")
async def set_log_level(level: str = Body(..., embed=True)):
    """Set parsing log level.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
    """
    import logging
    
    valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR"]
    level = level.upper()
    
    if level not in valid_levels:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid level. Valid levels: {valid_levels}"
        )
    
    logger = logging.getLogger("code_knowledge_graph.parser")
    logger.setLevel(getattr(logging, level))
    
    return {"success": True, "level": level}


def run_server(host: str = "127.0.0.1", port: int = 8000):
    """Run the web server."""
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_server()
