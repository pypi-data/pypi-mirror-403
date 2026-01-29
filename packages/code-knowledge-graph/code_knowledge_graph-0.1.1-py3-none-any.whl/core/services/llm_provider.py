"""LLM Provider interface and implementations.

This module provides abstract interface and implementations for LLM providers
supporting code summarization. Only OpenAI-compatible APIs are supported.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
import asyncio
import json

import httpx


@dataclass
class LLMConfig:
    """Configuration for LLM provider.

    Attributes:
        api_url: Base URL for the API (e.g., https://api.openai.com/v1)
        api_key: API key for authentication
        model: Model name to use (e.g., gpt-4o-mini)
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
    """
    api_url: str
    api_key: str
    model: str
    timeout: int = 30
    max_retries: int = 3

    @classmethod
    def from_dict(cls, data: dict) -> "LLMConfig":
        """Create config from dictionary."""
        return cls(
            api_url=data.get("api_url", "https://api.openai.com/v1"),
            api_key=data.get("api_key", ""),
            model=data.get("model", "gpt-4o-mini"),
            timeout=data.get("timeout", 30),
            max_retries=data.get("max_retries", 3)
        )

    def is_valid(self) -> bool:
        """Check if configuration is valid."""
        return bool(self.api_url and self.api_key and self.model)


class LLMProvider(ABC):
    """Abstract LLM provider interface."""

    @abstractmethod
    async def generate_summary(
        self,
        code_snippet: str,
        context: str,
        language: str = "bilingual"
    ) -> str:
        """Generate a one-sentence summary for code.

        Args:
            code_snippet: The code to summarize (function/class signature or full code)
            context: Additional context (file path, project info)
            language: Output language - "en", "zh", or "bilingual" (default)

        Returns:
            Natural language summary of the code
        """
        pass

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if the provider is available and configured."""
        pass


class OpenAICompatibleProvider(LLMProvider):
    """OpenAI-compatible API provider.

    Supports any API that follows the OpenAI chat completions format,
    including OpenAI, Azure OpenAI, local models with OpenAI-compatible servers,
    and other compatible services.
    """

    BILINGUAL_PROMPT = """You are a code documentation assistant. Generate a one-sentence summary describing what this code does.

Requirements:
1. Provide the summary in BOTH English and Chinese
2. Format: "English summary | 中文摘要"
3. Be concise - each language summary should be one sentence
4. Focus on WHAT the code does, not HOW it does it
5. Start with a verb (e.g., "Calculates...", "Returns...", "Validates...")

Context: {context}

Code:
```
{code}
```

Summary (format: "English | 中文"):"""

    ENGLISH_PROMPT = """You are a code documentation assistant. Generate a one-sentence summary describing what this code does.

Requirements:
1. Be concise - one sentence only
2. Focus on WHAT the code does, not HOW it does it
3. Start with a verb (e.g., "Calculates...", "Returns...", "Validates...")

Context: {context}

Code:
```
{code}
```

Summary:"""

    CHINESE_PROMPT = """你是一个代码文档助手。请用一句话描述这段代码的功能。

要求：
1. 简洁明了 - 只用一句话
2. 关注代码"做什么"，而不是"怎么做"
3. 以动词开头（例如："计算..."、"返回..."、"验证..."）

上下文：{context}

代码：
```
{code}
```

摘要："""

    def __init__(self, config: LLMConfig):
        """Initialize OpenAI-compatible provider.

        Args:
            config: LLM configuration
        """
        self.config = config
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.config.timeout),
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json"
                }
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
            client = await self._get_client()
            # Try a simple models list request to verify connectivity
            response = await client.get(
                f"{self.config.api_url.rstrip('/')}/models",
                timeout=5.0
            )
            return response.status_code in (200, 401, 403)  # 401/403 means API is reachable
        except Exception:
            return False

    async def generate_summary(
        self,
        code_snippet: str,
        context: str,
        language: str = "bilingual"
    ) -> str:
        """Generate code summary using OpenAI-compatible API.

        Args:
            code_snippet: Code to summarize
            context: Additional context
            language: "en", "zh", or "bilingual"

        Returns:
            Generated summary
        """
        if not self.config.is_valid():
            raise ValueError("LLM configuration is not valid")

        # Select prompt based on language
        if language == "zh":
            prompt = self.CHINESE_PROMPT.format(context=context, code=code_snippet)
        elif language == "en":
            prompt = self.ENGLISH_PROMPT.format(context=context, code=code_snippet)
        else:  # bilingual (default)
            prompt = self.BILINGUAL_PROMPT.format(context=context, code=code_snippet)

        client = await self._get_client()

        last_error = None
        for attempt in range(self.config.max_retries):
            try:
                response = await client.post(
                    f"{self.config.api_url.rstrip('/')}/chat/completions",
                    json={
                        "model": self.config.model,
                        "messages": [
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.3,
                        "max_tokens": 200
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"].strip()
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

        raise RuntimeError(f"Failed to generate summary after {self.config.max_retries} attempts: {last_error}")


class NoOpLLMProvider(LLMProvider):
    """No-operation LLM provider for when LLM is disabled."""

    async def generate_summary(
        self,
        code_snippet: str,
        context: str,
        language: str = "bilingual"
    ) -> str:
        """Return empty string since LLM is disabled."""
        return ""

    async def is_available(self) -> bool:
        """Always return False since this is a no-op provider."""
        return False


def create_llm_provider(config: Optional[LLMConfig] = None) -> LLMProvider:
    """Factory function to create LLM provider.

    Args:
        config: LLM configuration. If None or invalid, returns NoOpProvider.

    Returns:
        LLMProvider instance
    """
    if config is None or not config.is_valid():
        return NoOpLLMProvider()
    return OpenAICompatibleProvider(config)
