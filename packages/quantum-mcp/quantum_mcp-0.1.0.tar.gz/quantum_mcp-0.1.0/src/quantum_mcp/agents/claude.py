# Description: Claude agent implementation using Anthropic SDK.
# Description: Provides execute, stream, and health check for Claude models.
"""Claude agent implementation."""

from __future__ import annotations

import os
import time
from typing import TYPE_CHECKING, AsyncIterator

from quantum_mcp.agents.base import BaseAgent
from quantum_mcp.agents.protocol import AgentConfig, AgentResponse, AgentStatus

if TYPE_CHECKING:
    pass

DEFAULT_MODEL = "claude-3-5-sonnet-20241022"


class ClaudeAgent(BaseAgent):
    """Agent implementation for Claude models via Anthropic API.

    Uses the Anthropic Python SDK for communication with Claude.
    Supports both synchronous execution and streaming responses.
    """

    def __init__(self, config: AgentConfig) -> None:
        """Initialize Claude agent.

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
        """Initialize Anthropic client."""
        try:
            from anthropic import AsyncAnthropic

            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if api_key:
                self._client = AsyncAnthropic(api_key=api_key)
                self._logger.debug("Anthropic client initialized")
            else:
                self._logger.warning("ANTHROPIC_API_KEY not set")
        except ImportError:
            self._logger.warning("anthropic package not installed")

    @property
    def model(self) -> str:
        """Get model name."""
        return self._config.model or DEFAULT_MODEL

    async def execute(self, prompt: str) -> AgentResponse:
        """Execute prompt using Claude API.

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
                error="Anthropic client not initialized (missing API key or package)",
            )

        start_time = time.time()

        try:
            messages = [{"role": "user", "content": prompt}]

            kwargs = {
                "model": self.model,
                "max_tokens": self._config.max_tokens,
                "messages": messages,
            }

            if self._config.system_prompt:
                kwargs["system"] = self._config.system_prompt

            if self._config.temperature != 0.7:
                kwargs["temperature"] = self._config.temperature

            response = await self._client.messages.create(**kwargs)

            content = ""
            if response.content:
                content = response.content[0].text

            tokens_used = None
            if hasattr(response, "usage"):
                tokens_used = response.usage.input_tokens + response.usage.output_tokens

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
        """Stream response tokens from Claude API.

        Args:
            prompt: The prompt to execute

        Yields:
            Response tokens as they become available
        """
        if self._client is None:
            yield "Error: Anthropic client not initialized"
            return

        try:
            messages = [{"role": "user", "content": prompt}]

            kwargs = {
                "model": self.model,
                "max_tokens": self._config.max_tokens,
                "messages": messages,
            }

            if self._config.system_prompt:
                kwargs["system"] = self._config.system_prompt

            async with self._client.messages.stream(**kwargs) as stream:
                async for text in stream.text_stream:
                    yield text

        except Exception as e:
            self._logger.error("Stream failed", error=str(e))
            yield f"Error: {e}"

    async def health_check(self) -> bool:
        """Check if Claude API is accessible.

        Returns:
            True if healthy, False otherwise
        """
        if self._client is None:
            return False

        try:
            # Simple API check - list models or similar lightweight call
            # For now, just verify client is configured
            return True
        except Exception as e:
            self._logger.warning("Health check failed", error=str(e))
            return False
