"""MCP Server entry point using FastMCP.

Usage:
    python -m mcp_server.run
    
Or with FastMCP CLI:
    fastmcp run mcp_server/run.py

Configure in mcp.json:
    {
        "mcpServers": {
            "code-knowledge-graph": {
                "command": "uv",
                "args": ["run", "python", "-m", "mcp_server.run"],
                "cwd": "<project_path>"
            }
        }
    }
"""

import sys
import socket
import subprocess
import threading
import webbrowser
import time
import atexit
import signal
import logging
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def setup_logging():
    """Configure logging for the parser."""
    # Create a memory handler to store logs
    class MemoryHandler(logging.Handler):
        def __init__(self, capacity=1000):
            super().__init__()
            self.capacity = capacity
            self.buffer = []
        
        def emit(self, record):
            self.buffer.append({
                "time": record.created,
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "file": getattr(record, 'pathname', None),
                "line": getattr(record, 'lineno', None)
            })
            if len(self.buffer) > self.capacity:
                self.buffer.pop(0)
    
    # Setup parser logger
    parser_logger = logging.getLogger("code_knowledge_graph.parser")
    parser_logger.setLevel(logging.WARNING)  # Default to WARNING
    
    # Add memory handler
    memory_handler = MemoryHandler(capacity=1000)
    memory_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    parser_logger.addHandler(memory_handler)
    
    # Also add stderr handler for debugging
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.WARNING)
    stderr_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    parser_logger.addHandler(stderr_handler)


# Setup logging before importing other modules
setup_logging()

from fastmcp import FastMCP

from mcp_server.tools import (
    register_project_tools,
    register_stats_tools,
    register_context_tools,
    register_enhanced_tools,
    register_guide_tools,
)


def find_available_port(start_port: int = 18000, end_port: int = 18100) -> int:
    """Find an available port in the given range."""
    for port in range(start_port, end_port):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return port
        except OSError:
            continue
    raise RuntimeError(f"No available port found in range {start_port}-{end_port}")


# Global variable to track web server
_web_server_process = None
_web_server_port = None


def start_web_server_subprocess(port: int) -> subprocess.Popen:
    """Start the web server as a subprocess."""
    project_root = Path(__file__).parent.parent
    
    # Use uvicorn to run the web server
    process = subprocess.Popen(
        [
            sys.executable, "-m", "uvicorn",
            "web.server:app",
            "--host", "127.0.0.1",
            "--port", str(port),
            "--log-level", "warning",
            "--no-access-log"
        ],
        cwd=str(project_root),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        # On Windows, create a new process group so we can terminate it
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
    )
    return process


def cleanup_web_server():
    """Cleanup function to terminate web server on exit."""
    global _web_server_process
    if _web_server_process:
        try:
            if sys.platform == "win32":
                _web_server_process.terminate()
            else:
                _web_server_process.send_signal(signal.SIGTERM)
            _web_server_process.wait(timeout=3)
        except Exception:
            _web_server_process.kill()
        _web_server_process = None


def open_browser(port: int, delay: float = 2.0):
    """Open browser after a short delay to let server start."""
    time.sleep(delay)
    webbrowser.open(f"http://127.0.0.1:{port}")


def get_web_server_url() -> str | None:
    """Get the URL of the running web server."""
    if _web_server_port:
        return f"http://127.0.0.1:{_web_server_port}"
    return None


# Initialize FastMCP server
mcp = FastMCP(
    name="code-knowledge-graph",
    instructions="Code dependency knowledge graph analyzer. Scan projects, analyze dependencies, and get related code context."
)

# Register tools from different modules
register_project_tools(mcp)
register_stats_tools(mcp)
register_context_tools(mcp)
register_enhanced_tools(mcp)
register_guide_tools(mcp)


# Add a tool to get/open the web UI
@mcp.tool
def open_web_ui() -> dict:
    """打开 Web 可视化界面 | Open web UI. 详见 get_tool_guide("open_web_ui")"""
    url = get_web_server_url()
    if url:
        webbrowser.open(url)
        return {"success": True, "url": url, "message": "Web UI opened in browser"}
    return {"success": False, "message": "Web server not running"}





def main():
    """Main entry point for the MCP server."""
    global _web_server_port, _web_server_process
    
    # Start web server as subprocess
    try:
        _web_server_port = find_available_port()
        _web_server_process = start_web_server_subprocess(_web_server_port)
        
        # Register cleanup on exit
        atexit.register(cleanup_web_server)
        
        # Open browser in background thread
        browser_thread = threading.Thread(
            target=open_browser,
            args=(_web_server_port,),
            daemon=True
        )
        browser_thread.start()
        
    except Exception as e:
        # If web server fails to start, continue with MCP only
        print(f"Warning: Failed to start web server: {e}", file=sys.stderr)
    
    # Run MCP server (this blocks)
    try:
        mcp.run()
    finally:
        # Ensure cleanup on MCP exit
        cleanup_web_server()



if __name__ == "__main__":
    main()

