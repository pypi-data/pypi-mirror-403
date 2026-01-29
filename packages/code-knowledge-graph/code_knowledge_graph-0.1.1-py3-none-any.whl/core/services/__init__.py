"""Service layer for Code Knowledge Graph.

This module provides high-level services that orchestrate
storage, parsing, and analysis operations.
"""

from .stats import StatsService
from .project import ProjectService
from .function_analysis import (
    FunctionAnalysisService,
    FunctionRelation,
    FileAnalysis,
    FunctionRelationsResult,
)
from .related_context import (
    RelatedContextService,
    SignatureInfo,
    FileContext,
    RelatedCodeContext,
)
from .llm_provider import (
    LLMConfig,
    LLMProvider,
    OpenAICompatibleProvider,
    NoOpLLMProvider,
    create_llm_provider,
)
from .embedding_provider import (
    EmbeddingConfig,
    EmbeddingProviderType,
    EmbeddingProvider,
    OpenAIEmbeddingProvider,
    OllamaEmbeddingProvider,
    NoOpEmbeddingProvider,
    create_embedding_provider,
)
from .summarizer import (
    CodeSummarizer,
    CodeEntity,
    SummaryResult,
    SummarizationStats,
    create_summarizer,
)
from .symbol_search import (
    SymbolType,
    SymbolSearchResult,
    SymbolSearchResponse,
    SymbolSearchService,
)
from .skeleton import (
    SkeletonMode,
    SkeletonContent,
    ClassSkeleton,
    FunctionSkeleton,
    SkeletonExtractor,
)
from .entry_point import (
    EntryPointType,
    HTTPRouteEntry,
    MainEntry,
    DatabaseModelEntry,
    CLICommandEntry,
    EntryPointResult,
    EntryPointDetector,
)
from .call_chain import (
    CallChainNode,
    CallChainResult,
    CallChainService,
)
from .dependency_analysis import (
    DependencyScope,
    ImportScope,
    GroupBy,
    CircularDependencyResult,
    ImportGraphNode,
    ImportGraphEdge,
    ImportGraphResult,
    ChangeImpactResult,
    DependencyAnalysisService,
)
from .usage_finder import (
    SymbolDefinition,
    SymbolUsage,
    FindUsagesResult,
    UsageFinderService,
    UsagesByType,
    UsageType,
)
from .complexity_analyzer import (
    FunctionMetrics,
    HotspotInfo,
    DirectoryMetrics,
    ComplexityResult,
    ComplexityAnalyzer,
)
from .layer_checker import (
    LayerViolation,
    LayerStats,
    LayerCheckResult,
    LayerChecker,
)
from .dead_code_finder import (
    DeadCodeItem,
    DeadCodeStats,
    DeadCodeResult,
    DeadCodeFinder,
)

__all__ = [
    "StatsService",
    "ProjectService",
    "FunctionAnalysisService",
    "FunctionRelation",
    "FileAnalysis",
    "FunctionRelationsResult",
    "RelatedContextService",
    "SignatureInfo",
    "FileContext",
    "RelatedCodeContext",
    # LLM Provider
    "LLMConfig",
    "LLMProvider",
    "OpenAICompatibleProvider",
    "NoOpLLMProvider",
    "create_llm_provider",
    # Embedding Provider
    "EmbeddingConfig",
    "EmbeddingProviderType",
    "EmbeddingProvider",
    "OpenAIEmbeddingProvider",
    "OllamaEmbeddingProvider",
    "NoOpEmbeddingProvider",
    "create_embedding_provider",
    # Summarizer
    "CodeSummarizer",
    "CodeEntity",
    "SummaryResult",
    "SummarizationStats",
    "create_summarizer",
    # Symbol Search
    "SymbolType",
    "SymbolSearchResult",
    "SymbolSearchResponse",
    "SymbolSearchService",
    # Skeleton Extractor
    "SkeletonMode",
    "SkeletonContent",
    "ClassSkeleton",
    "FunctionSkeleton",
    "SkeletonExtractor",
    # Entry Point Detector
    "EntryPointType",
    "HTTPRouteEntry",
    "MainEntry",
    "DatabaseModelEntry",
    "CLICommandEntry",
    "EntryPointResult",
    "EntryPointDetector",
    # Call Chain Service
    "CallChainNode",
    "CallChainResult",
    "CallChainService",
    # Dependency Analysis Service
    "DependencyScope",
    "ImportScope",
    "GroupBy",
    "CircularDependencyResult",
    "ImportGraphNode",
    "ImportGraphEdge",
    "ImportGraphResult",
    "ChangeImpactResult",
    "DependencyAnalysisService",
    # Usage Finder Service
    "SymbolDefinition",
    "SymbolUsage",
    "FindUsagesResult",
    "UsageFinderService",
    "UsagesByType",
    "UsageType",
    # Complexity Analyzer
    "FunctionMetrics",
    "HotspotInfo",
    "DirectoryMetrics",
    "ComplexityResult",
    "ComplexityAnalyzer",
    # Layer Checker
    "LayerViolation",
    "LayerStats",
    "LayerCheckResult",
    "LayerChecker",
    # Dead Code Finder
    "DeadCodeItem",
    "DeadCodeStats",
    "DeadCodeResult",
    "DeadCodeFinder",
]
