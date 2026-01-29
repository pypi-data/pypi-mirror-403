# Description: Local agent implementation for Ollama and local models.
# Description: Provides execute, stream, and health check for local LLMs.
"""Local/Ollama agent implementation."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any, AsyncIterator

import aiohttp

from quantum_mcp.agents.base import BaseAgent
from quantum_mcp.agents.protocol import AgentConfig, AgentResponse, AgentStatus

if TYPE_CHECKING:
    pass

DEFAULT_MODEL = "llama3.2"
DEFAULT_BASE_URL = "http://localhost:11434"


class LocalAgent(BaseAgent):
    """Agent implementation for local models via Ollama API.

    Uses the Ollama REST API for communication with local LLMs.
    Supports both synchronous execution and streaming responses.
    """

    def __init__(self, config: AgentConfig) -> None:
        """Initialize Local agent.

        Args:
            config: Agent configuration
        """
        super().__init__(config)

        # Set default model if not specified
        if self._config.model is None:
            self._config = AgentConfig(
                **{**self._config.model_dump(), "model": DEFAULT_MODEL}
            )

        self._base_url = config.metadata.get("base_url", DEFAULT_BASE_URL)
        self._logger.debug("Local agent initialized", base_url=self._base_url)

    @property
    def model(self) -> str:
        """Get model name."""
        return self._config.model or DEFAULT_MODEL

    @property
    def base_url(self) -> str:
        """Get Ollama base URL."""
        return self._base_url

    async def _make_request(
        self,
        endpoint: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Make HTTP request to Ollama API.

        Args:
            endpoint: API endpoint (e.g., /api/chat)
            payload: Request payload

        Returns:
            Response data
        """
        url = f"{self._base_url}{endpoint}"

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self._config.timeout_seconds),
            ) as response:
                response.raise_for_status()
                return await response.json()

    async def _check_server(self) -> bool:
        """Check if Ollama server is running.

        Returns:
            True if server is accessible
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self._base_url}/api/tags",
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as response:
                    return response.status == 200
        except Exception:
            return False

    async def execute(self, prompt: str) -> AgentResponse:
        """Execute prompt using Ollama API.

        Args:
            prompt: The prompt to execute

        Returns:
            AgentResponse with the result
        """
        start_time = time.time()

        try:
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
            }

            if self._config.system_prompt:
                payload["messages"].insert(
                    0, {"role": "system", "content": self._config.system_prompt}
                )

            if self._config.temperature != 0.7:
                payload["options"] = {"temperature": self._config.temperature}

            response = await self._make_request("/api/chat", payload)

            content = ""
            if "message" in response:
                content = response["message"].get("content", "")

            latency_ms = (time.time() - start_time) * 1000

            self._logger.debug(
                "Execution complete",
                latency_ms=latency_ms,
            )

            return AgentResponse(
                agent_id=self.agent_id,
                content=content,
                status=AgentStatus.SUCCESS,
                latency_ms=latency_ms,
                metadata={"model": self.model},
            )

        except aiohttp.ClientError as e:
            self._logger.error("Connection failed", error=str(e))
            return AgentResponse(
                agent_id=self.agent_id,
                content="",
                status=AgentStatus.ERROR,
                error=f"Connection error: {e}",
                latency_ms=(time.time() - start_time) * 1000,
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
        """Stream response tokens from Ollama API.

        Args:
            prompt: The prompt to execute

        Yields:
            Response tokens as they become available
        """
        try:
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": True,
            }

            if self._config.system_prompt:
                payload["messages"].insert(
                    0, {"role": "system", "content": self._config.system_prompt}
                )

            url = f"{self._base_url}/api/chat"

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self._config.timeout_seconds),
                ) as response:
                    response.raise_for_status()

                    async for line in response.content:
                        if line:
                            import json

                            try:
                                data = json.loads(line.decode("utf-8"))
                                if "message" in data and "content" in data["message"]:
                                    yield data["message"]["content"]
                            except json.JSONDecodeError:
                                continue

        except Exception as e:
            self._logger.error("Stream failed", error=str(e))
            yield f"Error: {e}"

    async def health_check(self) -> bool:
        """Check if Ollama server is accessible.

        Returns:
            True if healthy, False otherwise
        """
        return await self._check_server()
