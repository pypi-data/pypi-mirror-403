"""Embedding Provider interface and implementations.

This module provides abstract interface and implementations for embedding providers
supporting code vectorization. Supports OpenAI-compatible APIs and Ollama.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Literal
from enum import Enum
import asyncio

import httpx


class EmbeddingProviderType(str, Enum):
    """Embedding provider type."""
    OPENAI = "openai"
    OLLAMA = "ollama"


@dataclass
class EmbeddingConfig:
    """Configuration for embedding provider.

    Attributes:
        provider_type: Type of provider (openai or ollama)
        api_url: Base URL for the API
        api_key: API key for authentication (not required for Ollama)
        model: Model name to use
        dimensions: Output embedding dimensions (optional, model-specific)
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
    """
    provider_type: EmbeddingProviderType
    api_url: str
    model: str
    api_key: str = ""
    dimensions: Optional[int] = None
    timeout: int = 60
    max_retries: int = 3

    @classmethod
    def from_dict(cls, data: dict) -> "EmbeddingConfig":
        """Create config from dictionary."""
        provider_type = data.get("provider_type", "openai")
        if isinstance(provider_type, str):
            provider_type = EmbeddingProviderType(provider_type)

        return cls(
            provider_type=provider_type,
            api_url=data.get("api_url", "https://api.openai.com/v1"),
            api_key=data.get("api_key", ""),
            model=data.get("model", "text-embedding-3-small"),
            dimensions=data.get("dimensions"),
            timeout=data.get("timeout", 60),
            max_retries=data.get("max_retries", 3)
        )

    def is_valid(self) -> bool:
        """Check if configuration is valid."""
        if not self.api_url or not self.model:
            return False
        # OpenAI requires API key, Ollama doesn't
        if self.provider_type == EmbeddingProviderType.OPENAI and not self.api_key:
            return False
        return True


class EmbeddingProvider(ABC):
    """Abstract embedding provider interface."""

    @abstractmethod
    async def embed_text(self, text: str) -> list[float]:
        """Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            List of floats representing the embedding vector
        """
        pass

    @abstractmethod
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        pass

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if the provider is available and configured."""
        pass

    @abstractmethod
    def get_dimensions(self) -> Optional[int]:
        """Get the embedding dimensions for this model."""
        pass


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI-compatible embedding API provider.

    Supports any API that follows the OpenAI embeddings format.
    """

    # Default dimensions for known models
    KNOWN_DIMENSIONS = {
        "text-embedding-3-small": 1536,
        "text-embedding-3-large": 3072,
        "text-embedding-ada-002": 1536,
    }

    def __init__(self, config: EmbeddingConfig):
        """Initialize OpenAI embedding provider.

        Args:
            config: Embedding configuration
        """
        self.config = config
        self._client: Optional[httpx.AsyncClient] = None
        self._dimensions: Optional[int] = config.dimensions

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            headers = {"Content-Type": "application/json"}
            if self.config.api_key:
                headers["Authorization"] = f"Bearer {self.config.api_key}"

            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.config.timeout),
                headers=headers
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def is_available(self) -> bool:
        """Check if the provider is available."""
        if not self.config.is_valid():
            return False

        try:
            # Try to generate a test embedding
            embedding = await self.embed_text("test")
            if embedding:
                self._dimensions = len(embedding)
                return True
            return False
        except Exception:
            return False

    def get_dimensions(self) -> Optional[int]:
        """Get embedding dimensions."""
        if self._dimensions:
            return self._dimensions
        return self.KNOWN_DIMENSIONS.get(self.config.model)

    async def embed_text(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        embeddings = await self.embed_batch([text])
        return embeddings[0] if embeddings else []

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        if not texts:
            return []

        if not self.config.is_valid():
            raise ValueError("Embedding configuration is not valid")

        client = await self._get_client()

        # Prepare request body
        body = {
            "model": self.config.model,
            "input": texts
        }
        if self.config.dimensions:
            body["dimensions"] = self.config.dimensions

        last_error = None
        for attempt in range(self.config.max_retries):
            try:
                response = await client.post(
                    f"{self.config.api_url.rstrip('/')}/embeddings",
                    json=body
                )

                if response.status_code == 200:
                    data = response.json()
                    # Sort by index to ensure correct order
                    embeddings_data = sorted(data["data"], key=lambda x: x["index"])
                    embeddings = [item["embedding"] for item in embeddings_data]

                    # Update dimensions if not set
                    if embeddings and not self._dimensions:
                        self._dimensions = len(embeddings[0])

                    return embeddings
                elif response.status_code == 429:  # Rate limit
                    wait_time = (attempt + 1) * 2
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    last_error = f"API error: {response.status_code} - {response.text}"

            except httpx.TimeoutException:
                last_error = "Request timeout"
                await asyncio.sleep(1)
            except Exception as e:
                last_error = str(e)
                await asyncio.sleep(1)

        raise RuntimeError(f"Failed to generate embeddings after {self.config.max_retries} attempts: {last_error}")


class OllamaEmbeddingProvider(EmbeddingProvider):
    """Ollama embedding provider.

    Supports Ollama's embedding API format.
    """

    # Default dimensions for known Ollama models
    KNOWN_DIMENSIONS = {
        "nomic-embed-text": 768,
        "mxbai-embed-large": 1024,
        "all-minilm": 384,
        "snowflake-arctic-embed": 1024,
    }

    def __init__(self, config: EmbeddingConfig):
        """Initialize Ollama embedding provider.

        Args:
            config: Embedding configuration
        """
        self.config = config
        self._client: Optional[httpx.AsyncClient] = None
        self._dimensions: Optional[int] = config.dimensions

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.config.timeout),
                headers={"Content-Type": "application/json"}
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def is_available(self) -> bool:
        """Check if the provider is available."""
        if not self.config.api_url or not self.config.model:
            return False

        try:
            client = await self._get_client()
            # Check if Ollama is running and model is available
            response = await client.get(
                f"{self.config.api_url.rstrip('/')}/api/tags",
                timeout=5.0
            )
            if response.status_code == 200:
                data = response.json()
                models = [m.get("name", "").split(":")[0] for m in data.get("models", [])]
                return self.config.model.split(":")[0] in models
            return False
        except Exception:
            return False

    def get_dimensions(self) -> Optional[int]:
        """Get embedding dimensions."""
        if self._dimensions:
            return self._dimensions
        model_base = self.config.model.split(":")[0]
        return self.KNOWN_DIMENSIONS.get(model_base)

    async def embed_text(self, text: str) -> list[float]:
        """Generate embedding for a single text using Ollama."""
        if not self.config.api_url or not self.config.model:
            raise ValueError("Ollama configuration is not valid")

        client = await self._get_client()

        last_error = None
        for attempt in range(self.config.max_retries):
            try:
                response = await client.post(
                    f"{self.config.api_url.rstrip('/')}/api/embeddings",
                    json={
                        "model": self.config.model,
                        "prompt": text
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    embedding = data.get("embedding", [])

                    # Update dimensions if not set
                    if embedding and not self._dimensions:
                        self._dimensions = len(embedding)

                    return embedding
                else:
                    last_error = f"API error: {response.status_code} - {response.text}"

            except httpx.TimeoutException:
                last_error = "Request timeout"
                await asyncio.sleep(1)
            except Exception as e:
                last_error = str(e)
                await asyncio.sleep(1)

        raise RuntimeError(f"Failed to generate embedding after {self.config.max_retries} attempts: {last_error}")

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts.

        Note: Ollama doesn't support batch embedding natively,
        so we process texts one at a time with concurrency limit.
        """
        if not texts:
            return []

        # Process with limited concurrency to avoid overwhelming Ollama
        semaphore = asyncio.Semaphore(5)

        async def embed_with_semaphore(text: str) -> list[float]:
            async with semaphore:
                return await self.embed_text(text)

        tasks = [embed_with_semaphore(text) for text in texts]
        return await asyncio.gather(*tasks)


class NoOpEmbeddingProvider(EmbeddingProvider):
    """No-operation embedding provider for when embedding is disabled."""

    async def embed_text(self, text: str) -> list[float]:
        """Return empty list since embedding is disabled."""
        return []

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Return empty lists since embedding is disabled."""
        return [[] for _ in texts]

    async def is_available(self) -> bool:
        """Always return False since this is a no-op provider."""
        return False

    def get_dimensions(self) -> Optional[int]:
        """Return None since this is a no-op provider."""
        return None


def create_embedding_provider(config: Optional[EmbeddingConfig] = None) -> EmbeddingProvider:
    """Factory function to create embedding provider.

    Args:
        config: Embedding configuration. If None or invalid, returns NoOpProvider.

    Returns:
        EmbeddingProvider instance
    """
    if config is None or not config.is_valid():
        return NoOpEmbeddingProvider()

    if config.provider_type == EmbeddingProviderType.OLLAMA:
        return OllamaEmbeddingProvider(config)
    else:  # Default to OpenAI
        return OpenAIEmbeddingProvider(config)
