"""MCP Server implementation for Code Knowledge Graph.

This module implements the Model Context Protocol (MCP) server
that exposes code knowledge graph tools for AI integration.
"""

import json
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from core.storage import StorageBackend, SQLiteStorage
from core.services import (
    StatsService,
    ProjectService,
    FunctionAnalysisService,
    RelatedContextService,
    LLMConfig,
    EmbeddingConfig,
    EmbeddingProviderType,
    CodeSummarizer,
    create_llm_provider,
    create_embedding_provider,
    create_summarizer,
    # New services for enhanced features
    SymbolSearchService,
    SymbolType,
    SkeletonExtractor,
    SkeletonMode,
    EntryPointDetector,
    EntryPointType,
)
from core.services.call_chain import CallChainService


class MCPErrorCode(Enum):
    """MCP error codes for structured error responses.
    
    Provides standardized error codes for all MCP tool responses.
    
    **Validates: Requirement 6.6** - Structured error responses
    """
    NOT_FOUND = "NOT_FOUND"
    INVALID_PARAMS = "INVALID_PARAMS"
    PARSE_ERROR = "PARSE_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    NOT_SCANNED = "NOT_SCANNED"
    LIMIT_EXCEEDED = "LIMIT_EXCEEDED"
    UNKNOWN_TOOL = "UNKNOWN_TOOL"
    LLM_NOT_CONFIGURED = "LLM_NOT_CONFIGURED"
    EMBEDDING_NOT_CONFIGURED = "EMBEDDING_NOT_CONFIGURED"
    SEARCH_ERROR = "SEARCH_ERROR"


class MCPServer:
    """MCP Protocol Server for Code Knowledge Graph.

    Provides tools for:
    - Project scanning and analysis
    - File type statistics
    - Reference ranking
    - Depth analysis
    - Function relations
    - Related code context (Repo Map)
    - LLM-powered code summarization (optional)
    - Semantic code search via embeddings (optional)
    """

    def __init__(
        self,
        storage: Optional[StorageBackend] = None,
        db_path: str = "code_knowledge.db",
        llm_config: Optional[LLMConfig] = None,
        embedding_config: Optional[EmbeddingConfig] = None
    ):
        """Initialize MCP server.

        Args:
            storage: Optional storage backend instance
            db_path: Path to SQLite database (used if storage not provided)
            llm_config: Optional LLM configuration for code summarization
                       If not provided, summarization will be disabled
            embedding_config: Optional embedding configuration for semantic search
                             If not provided, embedding will be disabled
        """
        self.storage = storage or SQLiteStorage(db_path)
        self.stats_service = StatsService(self.storage)
        self.project_service = ProjectService(self.storage)
        self.function_analysis = FunctionAnalysisService()
        self.related_context_service = None  # Initialized per project

        # Store configurations
        self.llm_config = llm_config
        self.embedding_config = embedding_config

        # Create summarizer with optional LLM and embedding providers
        self.summarizer = create_summarizer(
            storage=self.storage,
            llm_config=llm_config,
            embedding_config=embedding_config
        )
        
        # Initialize new services for enhanced features
        self.symbol_search_service = SymbolSearchService(self.storage)
        self.call_chain_service = CallChainService(self.storage)

    @classmethod
    def from_config(
        cls,
        db_path: str = "code_knowledge.db",
        llm_api_url: Optional[str] = None,
        llm_api_key: Optional[str] = None,
        llm_model: Optional[str] = None,
        embedding_provider_type: str = "openai",
        embedding_api_url: Optional[str] = None,
        embedding_api_key: Optional[str] = None,
        embedding_model: Optional[str] = None
    ) -> "MCPServer":
        """Create MCPServer from configuration parameters.

        This is a convenience method for creating the server with
        configuration passed as individual parameters.

        Args:
            db_path: Path to SQLite database
            llm_api_url: LLM API base URL (OpenAI-compatible)
            llm_api_key: LLM API key
            llm_model: LLM model name
            embedding_provider_type: "openai" or "ollama"
            embedding_api_url: Embedding API base URL
            embedding_api_key: Embedding API key (not required for Ollama)
            embedding_model: Embedding model name

        Returns:
            Configured MCPServer instance
        """
        # Build LLM config if all required params provided
        llm_config = None
        if llm_api_url and llm_api_key and llm_model:
            llm_config = LLMConfig(
                api_url=llm_api_url,
                api_key=llm_api_key,
                model=llm_model
            )

        # Build embedding config if required params provided
        embedding_config = None
        if embedding_api_url and embedding_model:
            provider_type = EmbeddingProviderType(embedding_provider_type)
            embedding_config = EmbeddingConfig(
                provider_type=provider_type,
                api_url=embedding_api_url,
                api_key=embedding_api_key or "",
                model=embedding_model
            )

        return cls(
            db_path=db_path,
            llm_config=llm_config,
            embedding_config=embedding_config
        )

    def get_tools(self) -> list[dict]:
        """Return list of available MCP tools.

        Returns:
            List of tool definitions with name, description, and input schema
        """
        tools = [
            {
                "name": "scan_project",
                "description": "扫描并分析项目代码依赖 | Scan and analyze project code dependencies",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "项目路径 | Project path"
                        },
                        "generate_summaries": {
                            "type": "boolean",
                            "default": False,
                            "description": "是否生成代码摘要（需要配置LLM）| Whether to generate code summaries (requires LLM config)"
                        }
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "get_file_stats",
                "description": "获取项目文件类型统计 | Get project file type statistics",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "项目路径 | Project path"
                        },
                        "subdirectory": {
                            "type": "string",
                            "description": "子目录过滤（可选）| Subdirectory filter (optional)"
                        }
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "get_reference_ranking",
                "description": "获取被引用最多的文件排名 | Get top referenced files ranking",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "项目路径 | Project path"
                        },
                        "limit": {
                            "type": "integer",
                            "default": 20,
                            "description": "返回结果数量限制 | Limit of results"
                        },
                        "file_type": {
                            "type": "string",
                            "description": "文件类型过滤（可选）| File type filter (optional)"
                        }
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "get_depth_analysis",
                "description": "获取目录和文件层级分析 | Get directory and file depth analysis",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "项目路径 | Project path"
                        },
                        "subdirectory": {
                            "type": "string",
                            "description": "子目录过滤（可选）| Subdirectory filter (optional)"
                        }
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "get_function_relations",
                "description": "获取指定文件间的函数调用关系（最多10个文件）| Get function call relations between files (max 10)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "files": {
                            "type": "array",
                            "items": {"type": "string"},
                            "maxItems": 10,
                            "description": "要分析的文件路径列表 | List of file paths to analyze"
                        }
                    },
                    "required": ["files"]
                }
            },
            {
                "name": "get_related_code_context",
                "description": "获取文件的关联代码上下文(Repo Map)，支持骨架模式以减少Token消耗 | Get related code context (Repo Map) with skeleton mode support for reduced token usage",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "project_path": {
                            "type": "string",
                            "description": "项目路径 | Project path"
                        },
                        "file_path": {
                            "type": "string",
                            "description": "目标文件相对路径 | Target file relative path"
                        },
                        "hops": {
                            "type": "integer",
                            "default": 1,
                            "minimum": 1,
                            "maximum": 3,
                            "description": "依赖跳数 | Dependency hops"
                        },
                        "mode": {
                            "type": "string",
                            "enum": ["full", "skeleton", "signature_only"],
                            "default": "skeleton",
                            "description": "内容模式：full（完整内容）、skeleton（骨架模式，保留签名和文档）、signature_only（仅签名）| Content mode: full (complete content), skeleton (signatures and docs), signature_only (signatures only)"
                        }
                    },
                    "required": ["project_path", "file_path"]
                }
            },
            {
                "name": "generate_summaries",
                "description": "为项目生成代码摘要（需要配置LLM）| Generate code summaries for project (requires LLM config)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "项目路径 | Project path"
                        },
                        "file_path": {
                            "type": "string",
                            "description": "指定文件路径（可选，不指定则处理引用最多的文件）| Specific file path (optional)"
                        },
                        "force_rescan": {
                            "type": "boolean",
                            "default": False,
                            "description": "是否强制重新生成 | Whether to force regeneration"
                        }
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "semantic_search",
                "description": "语义搜索代码（需要配置Embedding）| Semantic code search (requires embedding config)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "项目路径 | Project path"
                        },
                        "query": {
                            "type": "string",
                            "description": "搜索查询（自然语言）| Search query (natural language)"
                        },
                        "limit": {
                            "type": "integer",
                            "default": 10,
                            "description": "返回结果数量限制 | Limit of results"
                        }
                    },
                    "required": ["path", "query"]
                }
            },
            {
                "name": "get_summary_status",
                "description": "获取LLM摘要和嵌入配置状态 | Get LLM summarization and embedding configuration status",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            # New tools for enhanced features (Task 8)
            {
                "name": "trace_call_chain",
                "description": "追踪函数调用链，支持向上追溯（谁调用了我）和向下追踪（我调用了谁）| Trace function call chain, supports upstream (who calls me) and downstream (who do I call) tracing",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "project_path": {
                            "type": "string",
                            "description": "项目路径 | Project path"
                        },
                        "start_symbol": {
                            "type": "string",
                            "description": "起始函数名 | Starting function name"
                        },
                        "direction": {
                            "type": "string",
                            "enum": ["upstream", "downstream"],
                            "default": "downstream",
                            "description": "追踪方向：upstream（向上追溯调用者）或 downstream（向下追踪被调用者）| Trace direction: upstream (trace callers) or downstream (trace callees)"
                        },
                        "depth": {
                            "type": "integer",
                            "default": 5,
                            "minimum": 1,
                            "maximum": 10,
                            "description": "最大追踪深度 | Maximum trace depth"
                        },
                        "limit_per_level": {
                            "type": "integer",
                            "default": 20,
                            "minimum": 1,
                            "maximum": 100,
                            "description": "每层最大节点数 | Maximum nodes per depth level"
                        },
                        "prune_standard_libs": {
                            "type": "boolean",
                            "default": True,
                            "description": "是否剪枝标准库和第三方库调用 | Whether to prune standard library and third-party calls"
                        }
                    },
                    "required": ["project_path", "start_symbol"]
                }
            },
            {
                "name": "find_entry_points",
                "description": "查找项目入口点，包括HTTP路由、main函数、数据库模型和CLI命令 | Find project entry points including HTTP routes, main functions, database models, and CLI commands",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "project_path": {
                            "type": "string",
                            "description": "项目路径 | Project path"
                        },
                        "types": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": ["http_routes", "main_entry", "database_models", "cli_commands"]
                            },
                            "description": "要查找的入口点类型（可选，不指定则查找所有类型）| Entry point types to find (optional, finds all if not specified)"
                        }
                    },
                    "required": ["project_path"]
                }
            },
            {
                "name": "symbol_search",
                "description": "基于AST的精确符号搜索，支持类型过滤和前缀匹配 | AST-based precise symbol search with type filtering and prefix matching",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "project_path": {
                            "type": "string",
                            "description": "项目路径 | Project path"
                        },
                        "query": {
                            "type": "string",
                            "description": "搜索查询（符号名称）| Search query (symbol name)"
                        },
                        "symbol_types": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": ["function", "class", "method", "variable", "struct", "interface"]
                            },
                            "description": "符号类型过滤（可选）| Symbol type filter (optional)"
                        },
                        "case_sensitive": {
                            "type": "boolean",
                            "default": False,
                            "description": "是否大小写敏感 | Whether to match case"
                        },
                        "prefix_match": {
                            "type": "boolean",
                            "default": True,
                            "description": "是否启用前缀匹配 | Whether to enable prefix matching"
                        },
                        "limit": {
                            "type": "integer",
                            "default": 50,
                            "minimum": 1,
                            "maximum": 200,
                            "description": "返回结果数量限制 | Limit of results"
                        }
                    },
                    "required": ["project_path", "query"]
                }
            }
        ]

        return tools

    async def call_tool(self, name: str, arguments: dict) -> dict[str, Any]:
        """Execute a tool call.

        Args:
            name: Tool name
            arguments: Tool arguments

        Returns:
            Tool result as dictionary

        Raises:
            ValueError: If tool name is unknown or arguments are invalid
        """
        handlers = {
            "scan_project": self._handle_scan_project,
            "get_file_stats": self._handle_get_file_stats,
            "get_reference_ranking": self._handle_get_reference_ranking,
            "get_depth_analysis": self._handle_get_depth_analysis,
            "get_function_relations": self._handle_get_function_relations,
            "get_related_code_context": self._handle_get_related_code_context,
            "generate_summaries": self._handle_generate_summaries,
            "semantic_search": self._handle_semantic_search,
            "get_summary_status": self._handle_get_summary_status,
            # New handlers for enhanced features (Task 8)
            "trace_call_chain": self._handle_trace_call_chain,
            "find_entry_points": self._handle_find_entry_points,
            "symbol_search": self._handle_symbol_search,
        }

        handler = handlers.get(name)
        if not handler:
            return self._error_response(
                "Unknown tool",
                "UNKNOWN_TOOL",
                f"Tool '{name}' is not available"
            )

        try:
            return await handler(arguments)
        except ValueError as e:
            return self._error_response(
                "Invalid parameters",
                "INVALID_PARAMS",
                str(e)
            )
        except Exception as e:
            return self._error_response(
                "Internal error",
                "INTERNAL",
                str(e)
            )

    async def _handle_scan_project(self, args: dict) -> dict:
        """Handle scan_project tool call."""
        path = args.get("path")
        if not path:
            raise ValueError("Missing required parameter: path")

        project_path = Path(path)
        if not project_path.exists():
            return self._error_response(
                "Project not found",
                "NOT_FOUND",
                f"Path does not exist: {path}"
            )

        generate_summaries = args.get("generate_summaries", False)
        result = self.project_service.scan_project(str(project_path.resolve()))

        response = {
            "success": True,
            "project_path": result.project_path,
            "project_name": result.project_name,
            "file_count": result.total_files,
            "last_scanned": result.scan_mode,
            "file_types": result.file_types,
            "llm_enabled": self.summarizer.is_llm_enabled,
            "embedding_enabled": self.summarizer.is_embedding_enabled
        }

        # Generate summaries if requested and LLM is configured
        if generate_summaries:
            if not self.summarizer.is_llm_enabled:
                response["summary_warning"] = "LLM not configured, summaries not generated | LLM未配置，摘要未生成"
            else:
                try:
                    stats = await self.summarizer.summarize_project(
                        result.project_id,
                        result.project_path
                    )
                    response["summarization"] = {
                        "total_entities": stats.total_entities,
                        "successful": stats.successful,
                        "failed": stats.failed,
                        "files_processed": stats.files_processed
                    }
                except Exception as e:
                    response["summary_error"] = str(e)

        return response

    async def _handle_get_file_stats(self, args: dict) -> dict:
        """Handle get_file_stats tool call."""
        path = args.get("path")
        if not path:
            raise ValueError("Missing required parameter: path")

        subdirectory = args.get("subdirectory")

        response = self.stats_service.get_file_type_stats(
            str(Path(path).resolve()),
            subdirectory=subdirectory
        )

        if response is None:
            return self._error_response(
                "Project not found",
                "NOT_FOUND",
                f"Project not found: {path}"
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

    async def _handle_get_reference_ranking(self, args: dict) -> dict:
        """Handle get_reference_ranking tool call."""
        path = args.get("path")
        if not path:
            raise ValueError("Missing required parameter: path")

        limit = args.get("limit", 20)
        file_type = args.get("file_type")

        response = self.stats_service.get_reference_ranking(
            str(Path(path).resolve()),
            limit=limit,
            file_type=file_type
        )

        if response is None:
            return self._error_response(
                "Project not found",
                "NOT_FOUND",
                f"Project not found: {path}"
            )

        return {
            "project_path": response.project_path,
            "limit": limit,
            "file_type_filter": file_type,
            "results": [
                {
                    "file": r.file_path,
                    "count": r.reference_count,
                    "references": r.referencing_files
                }
                for r in response.results
            ]
        }

    async def _handle_get_depth_analysis(self, args: dict) -> dict:
        """Handle get_depth_analysis tool call."""
        path = args.get("path")
        if not path:
            raise ValueError("Missing required parameter: path")

        subdirectory = args.get("subdirectory")

        response = self.stats_service.get_depth_analysis(
            str(Path(path).resolve()),
            subdirectory=subdirectory
        )

        if response is None:
            return self._error_response(
                "Project not found",
                "NOT_FOUND",
                f"Project not found: {path}"
            )

        return {
            "project_path": response.project_path,
            "subdirectory": subdirectory,
            "directory_depth": response.directory_depth,
            "file_depth": response.file_depth
        }

    async def _handle_get_function_relations(self, args: dict) -> dict:
        """Handle get_function_relations tool call."""
        files = args.get("files")
        if not files:
            raise ValueError("Missing required parameter: files")

        if len(files) > 10:
            return self._error_response(
                "Too many files",
                "LIMIT_EXCEEDED",
                "Maximum 10 files allowed for function analysis"
            )

        try:
            result = self.function_analysis.analyze_files(files)
            return self.function_analysis.to_dict(result)
        except FileNotFoundError as e:
            return self._error_response(
                "File not found",
                "NOT_FOUND",
                str(e)
            )

    async def _handle_get_related_code_context(self, args: dict) -> dict:
        """Handle get_related_code_context tool call.
        
        **Validates: Requirement 6.2** - mode parameter support for skeleton view
        """
        project_path = args.get("project_path")
        file_path = args.get("file_path")
        hops = args.get("hops", 1)
        mode = args.get("mode", "skeleton")  # Default to skeleton mode

        if not project_path:
            raise ValueError("Missing required parameter: project_path")
        if not file_path:
            raise ValueError("Missing required parameter: file_path")

        # Validate mode parameter
        valid_modes = ["full", "skeleton", "signature_only"]
        if mode not in valid_modes:
            raise ValueError(f"Invalid mode: {mode}. Must be one of: {valid_modes}")

        project_root = Path(project_path)
        if not project_root.exists():
            return self._error_response(
                "Project not found",
                MCPErrorCode.NOT_FOUND.value,
                f"Path does not exist: {project_path}"
            )

        # Create service for this project with skeleton extractor
        context_service = RelatedContextService(self.storage, project_root)
        
        # Convert mode string to SkeletonMode enum
        skeleton_mode = SkeletonMode(mode)

        result = context_service.get_related_context(
            str(project_root.resolve()),
            file_path,
            hops=hops,
            mode=skeleton_mode
        )

        return context_service.to_dict(result)

    async def _handle_generate_summaries(self, args: dict) -> dict:
        """Handle generate_summaries tool call."""
        path = args.get("path")
        if not path:
            raise ValueError("Missing required parameter: path")

        project_path = Path(path)
        if not project_path.exists():
            return self._error_response(
                "Project not found",
                "NOT_FOUND",
                f"Path does not exist: {path}"
            )

        if not self.summarizer.is_llm_enabled:
            return self._error_response(
                "LLM not configured | LLM未配置",
                "LLM_NOT_CONFIGURED",
                "Please configure LLM API URL, key, and model to use summarization | 请配置LLM的API URL、密钥和模型以使用摘要功能"
            )

        # Get project from storage
        project = self.storage.get_project(str(project_path.resolve()))
        if not project:
            return self._error_response(
                "Project not scanned",
                "NOT_SCANNED",
                "Please scan the project first using scan_project | 请先使用scan_project扫描项目"
            )

        file_path = args.get("file_path")
        force_rescan = args.get("force_rescan", False)

        try:
            if file_path:
                # Summarize specific file
                stats = await self.summarizer.summarize_file(
                    project.id,
                    str(project_path.resolve()),
                    file_path,
                    force_rescan=force_rescan
                )
            else:
                # Summarize top-referenced files
                stats = await self.summarizer.summarize_project(
                    project.id,
                    str(project_path.resolve()),
                    force_rescan=force_rescan
                )

            return {
                "success": True,
                "project_path": str(project_path.resolve()),
                "file_path": file_path,
                "total_entities": stats.total_entities,
                "successful": stats.successful,
                "failed": stats.failed,
                "skipped": stats.skipped,
                "files_processed": stats.files_processed,
                "message_en": f"Successfully generated {stats.successful} summaries",
                "message_zh": f"成功生成{stats.successful}个摘要"
            }
        except FileNotFoundError as e:
            return self._error_response(
                "File not found",
                "NOT_FOUND",
                str(e)
            )

    async def _handle_semantic_search(self, args: dict) -> dict:
        """Handle semantic_search tool call."""
        path = args.get("path")
        query = args.get("query")

        if not path:
            raise ValueError("Missing required parameter: path")
        if not query:
            raise ValueError("Missing required parameter: query")

        project_path = Path(path)
        if not project_path.exists():
            return self._error_response(
                "Project not found",
                "NOT_FOUND",
                f"Path does not exist: {path}"
            )

        if not self.summarizer.is_embedding_enabled:
            return self._error_response(
                "Embedding not configured | Embedding未配置",
                "EMBEDDING_NOT_CONFIGURED",
                "Please configure embedding API URL and model to use semantic search | 请配置Embedding的API URL和模型以使用语义搜索"
            )

        # Get project from storage
        project = self.storage.get_project(str(project_path.resolve()))
        if not project:
            return self._error_response(
                "Project not scanned",
                "NOT_SCANNED",
                "Please scan the project first using scan_project | 请先使用scan_project扫描项目"
            )

        limit = args.get("limit", 10)

        try:
            results = await self.summarizer.get_summary_by_embedding(
                project.id,
                query,
                limit=limit
            )

            return {
                "success": True,
                "project_path": str(project_path.resolve()),
                "query": query,
                "results": [
                    {
                        "entity_type": r.entity_type,
                        "entity_name": r.entity_name,
                        "signature": r.signature,
                        "summary": r.summary,
                        "summary_en": r.summary_en,
                        "summary_zh": r.summary_zh,
                        "line_number": r.line_number
                    }
                    for r in results
                ],
                "total_results": len(results)
            }
        except Exception as e:
            return self._error_response(
                "Search failed",
                "SEARCH_ERROR",
                str(e)
            )

    async def _handle_get_summary_status(self, args: dict) -> dict:
        """Handle get_summary_status tool call."""
        return {
            "llm_enabled": self.summarizer.is_llm_enabled,
            "embedding_enabled": self.summarizer.is_embedding_enabled,
            "llm_config": {
                "configured": self.llm_config is not None and self.llm_config.is_valid(),
                "api_url": self.llm_config.api_url if self.llm_config else None,
                "model": self.llm_config.model if self.llm_config else None
            } if self.llm_config else {"configured": False},
            "embedding_config": {
                "configured": self.embedding_config is not None and self.embedding_config.is_valid(),
                "provider_type": self.embedding_config.provider_type.value if self.embedding_config else None,
                "api_url": self.embedding_config.api_url if self.embedding_config else None,
                "model": self.embedding_config.model if self.embedding_config else None
            } if self.embedding_config else {"configured": False},
            "message_en": "LLM and embedding status",
            "message_zh": "LLM和嵌入模型状态"
        }

    # =========================================================================
    # New handlers for enhanced features (Task 8)
    # =========================================================================

    async def _handle_trace_call_chain(self, args: dict) -> dict:
        """Handle trace_call_chain tool call.
        
        Traces function call chains using recursive CTE queries.
        
        **Validates: Requirement 6.1** - trace_call_chain tool
        """
        project_path = args.get("project_path")
        start_symbol = args.get("start_symbol")
        direction = args.get("direction", "downstream")
        depth = args.get("depth", 5)
        limit_per_level = args.get("limit_per_level", 20)
        prune_standard_libs = args.get("prune_standard_libs", True)

        if not project_path:
            raise ValueError("Missing required parameter: project_path")
        if not start_symbol:
            raise ValueError("Missing required parameter: start_symbol")

        # Validate direction
        if direction not in ("upstream", "downstream"):
            raise ValueError(f"Invalid direction: {direction}. Must be 'upstream' or 'downstream'")

        project_root = Path(project_path)
        if not project_root.exists():
            return self._error_response(
                "Project not found",
                MCPErrorCode.NOT_FOUND.value,
                f"Path does not exist: {project_path}"
            )

        # Check if project is scanned
        project = self.storage.get_project(str(project_root.resolve()))
        if not project:
            return self._error_response(
                "Project not scanned",
                MCPErrorCode.NOT_SCANNED.value,
                "Please scan the project first using scan_project | 请先使用scan_project扫描项目"
            )

        # Trace call chain
        result = self.call_chain_service.trace_call_chain(
            project_path=str(project_root.resolve()),
            start_symbol=start_symbol,
            direction=direction,
            depth=depth,
            limit_per_level=limit_per_level,
            prune_standard_libs=prune_standard_libs
        )

        # Convert result to dict with relative paths
        chains_data = []
        for chain in result.chains:
            chain_nodes = []
            for node in chain:
                chain_nodes.append({
                    "function_name": node.function_name,
                    "file_path": node.file_path,  # Already relative
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

    async def _handle_find_entry_points(self, args: dict) -> dict:
        """Handle find_entry_points tool call.
        
        Finds project entry points using AST-based detection.
        
        **Validates: Requirement 6.3** - find_entry_points tool
        """
        project_path = args.get("project_path")
        types_arg = args.get("types")

        if not project_path:
            raise ValueError("Missing required parameter: project_path")

        project_root = Path(project_path)
        if not project_root.exists():
            return self._error_response(
                "Project not found",
                MCPErrorCode.NOT_FOUND.value,
                f"Path does not exist: {project_path}"
            )

        # Check if project is scanned
        project = self.storage.get_project(str(project_root.resolve()))
        if not project:
            return self._error_response(
                "Project not scanned",
                MCPErrorCode.NOT_SCANNED.value,
                "Please scan the project first using scan_project | 请先使用scan_project扫描项目"
            )

        # Convert type strings to EntryPointType enum
        entry_point_types = None
        if types_arg:
            try:
                entry_point_types = [EntryPointType(t) for t in types_arg]
            except ValueError as e:
                raise ValueError(f"Invalid entry point type: {e}")

        # Create detector and find entry points
        detector = EntryPointDetector(
            storage=self.storage,
            project_root=project_root
        )
        
        result = detector.find_entry_points(
            project_path=str(project_root.resolve()),
            types=entry_point_types
        )

        # Convert result to dict with relative paths
        return {
            "success": True,
            "project_path": result.project_path,
            "http_routes": [
                {
                    "file_path": r.file_path,  # Already relative
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

    async def _handle_symbol_search(self, args: dict) -> dict:
        """Handle symbol_search tool call.
        
        Performs AST-based symbol search with type filtering and prefix matching.
        
        **Validates: Requirement 6.4** - symbol_search tool
        """
        project_path = args.get("project_path")
        query = args.get("query")
        symbol_types_arg = args.get("symbol_types")
        case_sensitive = args.get("case_sensitive", False)
        prefix_match = args.get("prefix_match", True)
        limit = args.get("limit", 50)

        if not project_path:
            raise ValueError("Missing required parameter: project_path")
        if not query:
            raise ValueError("Missing required parameter: query")

        project_root = Path(project_path)
        if not project_root.exists():
            return self._error_response(
                "Project not found",
                MCPErrorCode.NOT_FOUND.value,
                f"Path does not exist: {project_path}"
            )

        # Check if project is scanned
        project = self.storage.get_project(str(project_root.resolve()))
        if not project:
            return self._error_response(
                "Project not scanned",
                MCPErrorCode.NOT_SCANNED.value,
                "Please scan the project first using scan_project | 请先使用scan_project扫描项目"
            )

        # Convert symbol type strings to SymbolType enum
        symbol_types = None
        if symbol_types_arg:
            try:
                symbol_types = [SymbolType(t) for t in symbol_types_arg]
            except ValueError as e:
                raise ValueError(f"Invalid symbol type: {e}")

        # Perform search
        result = self.symbol_search_service.search(
            project_path=str(project_root.resolve()),
            query=query,
            symbol_types=symbol_types,
            case_sensitive=case_sensitive,
            prefix_match=prefix_match,
            limit=limit
        )

        # Convert result to dict with relative paths
        return {
            "success": True,
            "query": result.query,
            "results": [
                {
                    "name": r.name,
                    "symbol_type": r.symbol_type.value,
                    "file_path": r.file_path,  # Already relative
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

    def _error_response(
        self,
        error: str,
        code: str,
        details: Optional[str] = None
    ) -> dict:
        """Create an error response.
        
        **Validates: Requirement 6.6** - Structured error responses

        Args:
            error: Error message
            code: Error code
            details: Optional detailed message

        Returns:
            Error response dictionary
        """
        response = {
            "error": error,
            "code": code
        }
        if details:
            response["details"] = details
        return response

    async def close_async(self) -> None:
        """Close the MCP server and release resources asynchronously."""
        if self.summarizer:
            await self.summarizer.close()
        if hasattr(self.storage, 'close'):
            self.storage.close()

    def close(self) -> None:
        """Close the MCP server and release resources."""
        if hasattr(self.storage, 'close'):
            self.storage.close()
