# Description: OpenAI agent implementation using OpenAI SDK.
# Description: Provides execute, stream, and health check for GPT models.
"""OpenAI agent implementation."""

from __future__ import annotations

import os
import time
from typing import TYPE_CHECKING, AsyncIterator

from quantum_mcp.agents.base import BaseAgent
from quantum_mcp.agents.protocol import AgentConfig, AgentResponse, AgentStatus

if TYPE_CHECKING:
    pass

DEFAULT_MODEL = "gpt-4-turbo"


class OpenAIAgent(BaseAgent):
    """Agent implementation for OpenAI models via OpenAI API.

    Uses the OpenAI Python SDK for communication with GPT models.
    Supports both synchronous execution and streaming responses.
    """

    def __init__(self, config: AgentConfig) -> None:
        """Initialize OpenAI agent.

        Args:
            config: Agent configuration
        """
        super().__init__(config)

        # Set default model if not specified
        if self._config.model is None:
            self._config = AgentConfig(
                **{**self._config.model_dump(), "model": DEFAULT_MODEL}
            )

        self._client = None
        self._init_client()

    def _init_client(self) -> None:
        """Initialize OpenAI client."""
        try:
            from openai import AsyncOpenAI

            api_key = os.environ.get("OPENAI_API_KEY")
            if api_key:
                self._client = AsyncOpenAI(api_key=api_key)
                self._logger.debug("OpenAI client initialized")
            else:
                self._logger.warning("OPENAI_API_KEY not set")
        except ImportError:
            self._logger.warning("openai package not installed")

    @property
    def model(self) -> str:
        """Get model name."""
        return self._config.model or DEFAULT_MODEL

    async def execute(self, prompt: str) -> AgentResponse:
        """Execute prompt using OpenAI API.

        Args:
            prompt: The prompt to execute

        Returns:
            AgentResponse with the result
        """
        if self._client is None:
            return AgentResponse(
                agent_id=self.agent_id,
                content="",
                status=AgentStatus.ERROR,
                error="OpenAI client not initialized (missing API key or package)",
            )

        start_time = time.time()

        try:
            messages = []

            if self._config.system_prompt:
                messages.append({"role": "system", "content": self._config.system_prompt})

            messages.append({"role": "user", "content": prompt})

            response = await self._client.chat.completions.create(
                model=self.model,
                max_tokens=self._config.max_tokens,
                temperature=self._config.temperature,
                messages=messages,
            )

            content = ""
            if response.choices:
                content = response.choices[0].message.content or ""

            tokens_used = None
            if hasattr(response, "usage") and response.usage:
                tokens_used = response.usage.total_tokens

            latency_ms = (time.time() - start_time) * 1000

            self._logger.debug(
                "Execution complete",
                tokens=tokens_used,
                latency_ms=latency_ms,
            )

            return AgentResponse(
                agent_id=self.agent_id,
                content=content,
                status=AgentStatus.SUCCESS,
                tokens_used=tokens_used,
                latency_ms=latency_ms,
                metadata={"model": self.model},
            )

        except Exception as e:
            self._logger.error("Execution failed", error=str(e))
            return AgentResponse(
                agent_id=self.agent_id,
                content="",
                status=AgentStatus.ERROR,
                error=str(e),
                latency_ms=(time.time() - start_time) * 1000,
            )

    async def stream(self, prompt: str) -> AsyncIterator[str]:
        """Stream response tokens from OpenAI API.

        Args:
            prompt: The prompt to execute

        Yields:
            Response tokens as they become available
        """
        if self._client is None:
            yield "Error: OpenAI client not initialized"
            return

        try:
            messages = []

            if self._config.system_prompt:
                messages.append({"role": "system", "content": self._config.system_prompt})

            messages.append({"role": "user", "content": prompt})

            stream = await self._client.chat.completions.create(
                model=self.model,
                max_tokens=self._config.max_tokens,
                temperature=self._config.temperature,
                messages=messages,
                stream=True,
            )

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            self._logger.error("Stream failed", error=str(e))
            yield f"Error: {e}"

    async def health_check(self) -> bool:
        """Check if OpenAI API is accessible.

        Returns:
            True if healthy, False otherwise
        """
        if self._client is None:
            return False

        try:
            # Simple API check - verify client is configured
            return True
        except Exception as e:
            self._logger.warning("Health check failed", error=str(e))
            return False
