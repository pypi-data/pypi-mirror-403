# Description: Tool agent wrapper exposing MCP tools as agents.
# Description: Allows tools to participate in multi-agent orchestration.
"""Tool agent wrapper for MCP tools."""

from __future__ import annotations

import json
import time
from typing import TYPE_CHECKING, Any, AsyncIterator

from quantum_mcp.agents.base import BaseAgent
from quantum_mcp.agents.protocol import AgentConfig, AgentResponse, AgentStatus

if TYPE_CHECKING:
    from quantum_mcp.server import QuantumMCPServer


class ToolAgent(BaseAgent):
    """Agent wrapper for MCP tools.

    Wraps an MCP tool as an agent, allowing tools to participate
    in multi-agent orchestration. The prompt is parsed as JSON
    arguments for the tool.
    """

    def __init__(
        self,
        config: AgentConfig,
        server: "QuantumMCPServer",
    ) -> None:
        """Initialize Tool agent.

        Args:
            config: Agent configuration
            server: MCP server instance with registered tools
        """
        super().__init__(config)
        self._server = server
        self._tool_name = config.metadata.get("tool_name", "")

        if not self._tool_name:
            raise ValueError("tool_name must be specified in config.metadata")

        self._logger.debug("Tool agent initialized", tool=self._tool_name)

    @property
    def tool_name(self) -> str:
        """Get wrapped tool name."""
        return self._tool_name

    @property
    def model(self) -> str | None:
        """Tool agents don't have a model."""
        return None

    async def execute(self, prompt: str) -> AgentResponse:
        """Execute tool with provided arguments.

        The prompt is parsed as JSON and passed as tool arguments.
        If the prompt is plain text, it's wrapped in a simple structure.

        Args:
            prompt: JSON string of tool arguments, or plain text

        Returns:
            AgentResponse with the tool result
        """
        start_time = time.time()

        try:
            # Parse prompt as JSON arguments
            try:
                arguments = json.loads(prompt)
            except json.JSONDecodeError:
                # Treat as plain text input for simple tools
                arguments = {"input": prompt}

            # Call the tool
            result = await self._server.call_tool(self._tool_name, arguments)

            latency_ms = (time.time() - start_time) * 1000

            self._logger.debug(
                "Tool execution complete",
                tool=self._tool_name,
                latency_ms=latency_ms,
            )

            return AgentResponse(
                agent_id=self.agent_id,
                content=result,
                status=AgentStatus.SUCCESS,
                latency_ms=latency_ms,
                metadata={"tool": self._tool_name},
            )

        except KeyError as e:
            self._logger.error("Tool not found", error=str(e))
            return AgentResponse(
                agent_id=self.agent_id,
                content="",
                status=AgentStatus.ERROR,
                error=f"Tool not found: {e}",
                latency_ms=(time.time() - start_time) * 1000,
            )
        except Exception as e:
            self._logger.error("Tool execution failed", error=str(e))
            return AgentResponse(
                agent_id=self.agent_id,
                content="",
                status=AgentStatus.ERROR,
                error=str(e),
                latency_ms=(time.time() - start_time) * 1000,
            )

    async def stream(self, prompt: str) -> AsyncIterator[str]:
        """Stream is not supported for tools - returns full result.

        Args:
            prompt: Tool arguments

        Yields:
            Complete result as single chunk
        """
        response = await self.execute(prompt)
        yield response.content

    async def health_check(self) -> bool:
        """Check if the wrapped tool is available.

        Returns:
            True if tool is registered and available
        """
        try:
            tools = self._server.list_tools()
            tool_names = [t.name for t in tools]
            return self._tool_name in tool_names
        except Exception as e:
            self._logger.warning("Health check failed", error=str(e))
            return False

    def get_tool_schema(self) -> dict[str, Any] | None:
        """Get the JSON schema for this tool's arguments.

        Returns:
            Tool argument schema, or None if not found
        """
        try:
            tools = self._server.list_tools()
            for tool in tools:
                if tool.name == self._tool_name:
                    return tool.input_schema
            return None
        except Exception:
            return None
