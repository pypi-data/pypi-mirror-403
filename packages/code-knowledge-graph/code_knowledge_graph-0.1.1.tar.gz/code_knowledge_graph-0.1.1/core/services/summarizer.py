"""Code Summarizer service.

This module provides the CodeSummarizer service that generates
natural language summaries for code entities (functions, classes)
using LLM and stores embeddings for semantic search.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import asyncio
import logging

from core.storage import StorageBackend, CodeSummaryRecord
from core.parsers import get_parser
from .llm_provider import LLMProvider, LLMConfig, create_llm_provider, NoOpLLMProvider
from .embedding_provider import EmbeddingProvider, EmbeddingConfig, create_embedding_provider, NoOpEmbeddingProvider


logger = logging.getLogger(__name__)


@dataclass
class CodeEntity:
    """Represents a code entity to be summarized."""
    entity_type: str  # 'function' or 'class'
    name: str
    signature: str
    file_path: str
    file_id: int
    line_number: int
    docstring: Optional[str] = None


@dataclass
class SummaryResult:
    """Result of summarization for a single entity."""
    entity: CodeEntity
    summary: str  # Bilingual summary: "English | 中文"
    summary_en: str  # English only
    summary_zh: str  # Chinese only
    embedding: Optional[list[float]] = None
    success: bool = True
    error: Optional[str] = None


@dataclass
class SummarizationStats:
    """Statistics for a summarization run."""
    total_entities: int
    successful: int
    failed: int
    skipped: int
    files_processed: int


class CodeSummarizer:
    """Code summarization service.

    Generates natural language summaries for code entities using LLM
    and optionally stores vector embeddings for semantic search.
    """

    def __init__(
        self,
        storage: StorageBackend,
        llm_provider: Optional[LLMProvider] = None,
        embedding_provider: Optional[EmbeddingProvider] = None,
        top_files_threshold: int = 20,
        concurrency_limit: int = 5
    ):
        """Initialize code summarizer.

        Args:
            storage: Storage backend for persisting summaries
            llm_provider: LLM provider for generating summaries (optional)
            embedding_provider: Embedding provider for vectorization (optional)
            top_files_threshold: Number of top-referenced files to summarize
            concurrency_limit: Maximum concurrent LLM requests
        """
        self.storage = storage
        self.llm = llm_provider or NoOpLLMProvider()
        self.embedder = embedding_provider or NoOpEmbeddingProvider()
        self.threshold = top_files_threshold
        self.concurrency_limit = concurrency_limit
        self._semaphore = asyncio.Semaphore(concurrency_limit)

    @property
    def is_llm_enabled(self) -> bool:
        """Check if LLM summarization is enabled."""
        return not isinstance(self.llm, NoOpLLMProvider)

    @property
    def is_embedding_enabled(self) -> bool:
        """Check if embedding is enabled."""
        return not isinstance(self.embedder, NoOpEmbeddingProvider)

    async def summarize_project(
        self,
        project_id: int,
        project_path: str,
        force_rescan: bool = False
    ) -> SummarizationStats:
        """Generate summaries for top-referenced files in a project.

        Args:
            project_id: Project ID in database
            project_path: Path to project root
            force_rescan: If True, regenerate all summaries even if they exist

        Returns:
            SummarizationStats with operation results
        """
        if not self.is_llm_enabled:
            logger.info("LLM provider not configured, skipping summarization")
            return SummarizationStats(
                total_entities=0,
                successful=0,
                failed=0,
                skipped=0,
                files_processed=0
            )

        # Get top-referenced files
        top_files = self.storage.get_reference_ranking(
            project_id,
            limit=self.threshold
        )

        if not top_files:
            logger.info("No referenced files found for summarization")
            return SummarizationStats(
                total_entities=0,
                successful=0,
                failed=0,
                skipped=0,
                files_processed=0
            )

        # Extract entities from top files
        entities = []
        files_processed = 0
        project_root = Path(project_path)

        for ranking_item in top_files:
            file_path = ranking_item.file_path
            full_path = project_root / file_path

            if not full_path.exists():
                continue

            file_record = self.storage.get_file_by_path(project_id, file_path)
            if not file_record:
                continue

            try:
                file_entities = await self._extract_entities(
                    str(full_path),
                    file_path,
                    file_record.id
                )
                entities.extend(file_entities)
                files_processed += 1
            except Exception as e:
                logger.warning(f"Failed to extract entities from {file_path}: {e}")

        # Filter out entities with existing summaries unless force_rescan
        if not force_rescan:
            entities = await self._filter_existing_summaries(entities)

        if not entities:
            logger.info("No new entities to summarize")
            return SummarizationStats(
                total_entities=0,
                successful=0,
                failed=0,
                skipped=0,
                files_processed=files_processed
            )

        # Generate summaries concurrently
        results = await self._summarize_entities(entities, project_path)

        # Save successful summaries
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]

        if successful:
            await self._save_summaries(successful)

        return SummarizationStats(
            total_entities=len(entities),
            successful=len(successful),
            failed=len(failed),
            skipped=len(top_files) * 2 - len(entities),  # Approximate skipped
            files_processed=files_processed
        )

    async def summarize_file(
        self,
        project_id: int,
        project_path: str,
        file_path: str,
        force_rescan: bool = False
    ) -> SummarizationStats:
        """Generate summaries for a specific file.

        Args:
            project_id: Project ID in database
            project_path: Path to project root
            file_path: Relative path to file
            force_rescan: If True, regenerate summaries

        Returns:
            SummarizationStats with operation results
        """
        if not self.is_llm_enabled:
            logger.info("LLM provider not configured, skipping summarization")
            return SummarizationStats(
                total_entities=0,
                successful=0,
                failed=0,
                skipped=0,
                files_processed=0
            )

        project_root = Path(project_path)
        full_path = project_root / file_path

        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {full_path}")

        file_record = self.storage.get_file_by_path(project_id, file_path)
        if not file_record:
            raise ValueError(f"File not found in database: {file_path}")

        # Extract entities
        entities = await self._extract_entities(
            str(full_path),
            file_path,
            file_record.id
        )

        if not force_rescan:
            entities = await self._filter_existing_summaries(entities)

        if not entities:
            return SummarizationStats(
                total_entities=0,
                successful=0,
                failed=0,
                skipped=0,
                files_processed=1
            )

        # Generate summaries
        results = await self._summarize_entities(entities, project_path)

        # Save successful summaries
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]

        if successful:
            await self._save_summaries(successful)

        return SummarizationStats(
            total_entities=len(entities),
            successful=len(successful),
            failed=len(failed),
            skipped=0,
            files_processed=1
        )

    async def _extract_entities(
        self,
        full_path: str,
        relative_path: str,
        file_id: int
    ) -> list[CodeEntity]:
        """Extract functions and classes from a file."""
        entities = []

        try:
            # Determine file type and get parser
            path_obj = Path(full_path)
            suffix = path_obj.suffix.lower()

            parser = get_parser(suffix)
            if not parser:
                return entities

            # Parse file to get functions and classes
            parse_result = parser.parse_full(full_path)

            # Add functions
            for func in parse_result.functions:
                entities.append(CodeEntity(
                    entity_type='function',
                    name=func.name,
                    signature=func.signature,
                    file_path=relative_path,
                    file_id=file_id,
                    line_number=func.start_line,
                    docstring=func.docstring
                ))

            # Add classes
            for cls in parse_result.classes:
                entities.append(CodeEntity(
                    entity_type='class',
                    name=cls.name,
                    signature=cls.signature,
                    file_path=relative_path,
                    file_id=file_id,
                    line_number=cls.start_line,
                    docstring=cls.docstring
                ))

        except Exception as e:
            logger.warning(f"Failed to parse {full_path}: {e}")

        return entities

    async def _filter_existing_summaries(
        self,
        entities: list[CodeEntity]
    ) -> list[CodeEntity]:
        """Filter out entities that already have summaries."""
        filtered = []
        for entity in entities:
            existing = self.storage.get_summary(entity.file_id, entity.name)
            if not existing:
                filtered.append(entity)
        return filtered

    async def _summarize_entities(
        self,
        entities: list[CodeEntity],
        project_path: str
    ) -> list[SummaryResult]:
        """Generate summaries for entities concurrently."""

        async def summarize_one(entity: CodeEntity) -> SummaryResult:
            async with self._semaphore:
                try:
                    # Build context
                    context = f"File: {entity.file_path}"
                    if entity.docstring:
                        context += f"\nDocstring: {entity.docstring}"

                    # Generate bilingual summary
                    summary = await self.llm.generate_summary(
                        entity.signature,
                        context,
                        language="bilingual"
                    )

                    # Parse bilingual summary
                    summary_en, summary_zh = self._parse_bilingual_summary(summary)

                    # Generate embedding if enabled
                    embedding = None
                    if self.is_embedding_enabled:
                        try:
                            # Use signature + summary for embedding
                            embed_text = f"{entity.signature}\n{summary}"
                            embedding = await self.embedder.embed_text(embed_text)
                        except Exception as e:
                            logger.warning(f"Failed to generate embedding for {entity.name}: {e}")

                    return SummaryResult(
                        entity=entity,
                        summary=summary,
                        summary_en=summary_en,
                        summary_zh=summary_zh,
                        embedding=embedding,
                        success=True
                    )

                except Exception as e:
                    logger.error(f"Failed to summarize {entity.name}: {e}")
                    return SummaryResult(
                        entity=entity,
                        summary="",
                        summary_en="",
                        summary_zh="",
                        success=False,
                        error=str(e)
                    )

        tasks = [summarize_one(entity) for entity in entities]
        return await asyncio.gather(*tasks)

    def _parse_bilingual_summary(self, summary: str) -> tuple[str, str]:
        """Parse bilingual summary into English and Chinese parts.

        Args:
            summary: Bilingual summary in format "English | 中文"

        Returns:
            Tuple of (english_summary, chinese_summary)
        """
        if "|" in summary:
            parts = summary.split("|", 1)
            return parts[0].strip(), parts[1].strip()
        else:
            # If not bilingual format, return as both
            return summary.strip(), summary.strip()

    async def _save_summaries(self, results: list[SummaryResult]) -> None:
        """Save successful summaries to storage."""
        summaries = []
        for result in results:
            summaries.append({
                "file_id": result.entity.file_id,
                "entity_type": result.entity.entity_type,
                "entity_name": result.entity.name,
                "signature": result.entity.signature,
                "summary": result.summary,
                "summary_en": result.summary_en,
                "summary_zh": result.summary_zh,
                "line_number": result.entity.line_number,
                "embedding": result.embedding
            })

        if summaries:
            self.storage.save_summaries(summaries)

    async def get_summary_by_embedding(
        self,
        project_id: int,
        query: str,
        limit: int = 10
    ) -> list[CodeSummaryRecord]:
        """Find similar code by semantic search.

        Args:
            project_id: Project ID
            query: Natural language query
            limit: Maximum results to return

        Returns:
            List of similar code summaries
        """
        if not self.is_embedding_enabled:
            return []

        # Generate query embedding
        try:
            query_embedding = await self.embedder.embed_text(query)
        except Exception as e:
            logger.error(f"Failed to generate query embedding: {e}")
            return []

        # Search in storage (requires vector search capability)
        # This will need to be implemented in storage backend
        if hasattr(self.storage, 'search_by_embedding'):
            return self.storage.search_by_embedding(
                project_id,
                query_embedding,
                limit
            )

        return []

    async def close(self) -> None:
        """Close resources."""
        if hasattr(self.llm, 'close'):
            await self.llm.close()
        if hasattr(self.embedder, 'close'):
            await self.embedder.close()


def create_summarizer(
    storage: StorageBackend,
    llm_config: Optional[LLMConfig] = None,
    embedding_config: Optional[EmbeddingConfig] = None,
    top_files_threshold: int = 20
) -> CodeSummarizer:
    """Factory function to create CodeSummarizer.

    Args:
        storage: Storage backend
        llm_config: Optional LLM configuration
        embedding_config: Optional embedding configuration
        top_files_threshold: Number of top files to summarize

    Returns:
        Configured CodeSummarizer instance
    """
    llm_provider = create_llm_provider(llm_config)
    embedding_provider = create_embedding_provider(embedding_config)

    return CodeSummarizer(
        storage=storage,
        llm_provider=llm_provider,
        embedding_provider=embedding_provider,
        top_files_threshold=top_files_threshold
    )
