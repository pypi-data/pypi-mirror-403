# Description: MCP server implementation for quantum operations.
# Description: Exposes Azure Quantum capabilities via MCP protocol.
"""MCP server for quantum operations."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from functools import lru_cache
from typing import Any, Callable, Coroutine, Optional

import structlog
from mcp.server.fastmcp import FastMCP

from quantum_mcp.client import QuantumClient
from quantum_mcp.config import get_settings
from quantum_mcp.tools.registration import register_all_tools

logger = structlog.get_logger()


@dataclass
class CostEntry:
    """Record of a cost incurred."""

    job_id: str
    cost: float
    timestamp: datetime = field(default_factory=datetime.now)


class SessionManager:
    """Manage session state including job tracking."""

    def __init__(self) -> None:
        """Initialize session manager."""
        self._sessions: dict[str, dict[str, str]] = {}

    def create_session(self) -> str:
        """Create a new session.

        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())
        self._sessions[session_id] = {}
        return session_id

    def track_job(self, session_id: str, job_id: str, status: str) -> None:
        """Track a job in a session.

        Args:
            session_id: Session ID
            job_id: Job ID to track
            status: Initial job status
        """
        if session_id in self._sessions:
            self._sessions[session_id][job_id] = status

    def update_job_status(self, session_id: str, job_id: str, status: str) -> None:
        """Update job status.

        Args:
            session_id: Session ID
            job_id: Job ID
            status: New status
        """
        if session_id in self._sessions and job_id in self._sessions[session_id]:
            self._sessions[session_id][job_id] = status

    def get_session_jobs(self, session_id: str) -> dict[str, str]:
        """Get all jobs in a session.

        Args:
            session_id: Session ID

        Returns:
            Dictionary mapping job IDs to statuses
        """
        return self._sessions.get(session_id, {}).copy()

    def expire_session(self, session_id: str) -> None:
        """Expire a session.

        Args:
            session_id: Session ID to expire
        """
        if session_id in self._sessions:
            del self._sessions[session_id]


class ResultCache:
    """Cache for job results."""

    def __init__(self) -> None:
        """Initialize result cache."""
        self._cache: dict[str, dict[str, Any]] = {}

    def get(self, job_id: str) -> Optional[dict[str, Any]]:
        """Get cached result.

        Args:
            job_id: Job ID

        Returns:
            Cached result or None
        """
        return self._cache.get(job_id)

    def set(self, job_id: str, result: dict[str, Any]) -> None:
        """Cache a result.

        Args:
            job_id: Job ID
            result: Result to cache
        """
        self._cache[job_id] = result

    def invalidate(self, job_id: str) -> None:
        """Invalidate a cached result.

        Args:
            job_id: Job ID to invalidate
        """
        if job_id in self._cache:
            del self._cache[job_id]

    def clear(self) -> None:
        """Clear entire cache."""
        self._cache.clear()


class BudgetTracker:
    """Track spending against a budget limit."""

    def __init__(self, budget_limit: float = 10.0) -> None:
        """Initialize budget tracker.

        Args:
            budget_limit: Maximum allowed spending in USD
        """
        self._budget_limit = budget_limit
        self._spent = 0.0
        self._history: list[CostEntry] = []

    @property
    def budget_limit(self) -> float:
        """Get budget limit."""
        return self._budget_limit

    @property
    def spent(self) -> float:
        """Get total spent."""
        return self._spent

    @property
    def remaining(self) -> float:
        """Get remaining budget."""
        return self._budget_limit - self._spent

    def can_afford(self, cost: float) -> bool:
        """Check if a cost can be afforded.

        Args:
            cost: Cost to check

        Returns:
            True if can afford, False otherwise
        """
        return self._spent + cost <= self._budget_limit

    def record_cost(self, cost: float, job_id: str, strict: bool = False) -> None:
        """Record a cost.

        Args:
            cost: Cost in USD
            job_id: Associated job ID
            strict: If True, raise error if budget exceeded

        Raises:
            ValueError: If strict mode and budget would be exceeded
        """
        if strict and not self.can_afford(cost):
            raise ValueError(
                f"Budget exceeded: ${self._spent + cost:.2f} > ${self._budget_limit:.2f}"
            )

        self._spent += cost
        self._history.append(CostEntry(job_id=job_id, cost=cost))

    def get_history(self) -> list[dict[str, Any]]:
        """Get cost history.

        Returns:
            List of cost entries as dictionaries
        """
        return [
            {
                "job_id": entry.job_id,
                "cost": entry.cost,
                "timestamp": entry.timestamp.isoformat(),
            }
            for entry in self._history
        ]


@dataclass
class ToolInfo:
    """Information about a registered tool."""

    name: str
    description: str
    input_schema: dict[str, Any]


class QuantumMCPServer:
    """MCP server for quantum operations.

    Provides tool registration and execution for Azure Quantum operations.
    """

    def __init__(self, name: str = "quantum-mcp") -> None:
        """Initialize the MCP server.

        Args:
            name: Server name for MCP registration
        """
        self._name = name
        self._mcp = FastMCP(name)
        self._client: Optional[QuantumClient] = None
        self._tools: dict[str, Callable[..., Coroutine[Any, Any, str]]] = {}
        self._tool_info: dict[str, ToolInfo] = {}
        self._logger = logger.bind(component="QuantumMCPServer")

        # Register core tools
        self._register_core_tools()

    @property
    def name(self) -> str:
        """Get server name."""
        return self._name

    @property
    def mcp(self) -> FastMCP:
        """Get FastMCP instance."""
        return self._mcp

    @property
    def client(self) -> Optional[QuantumClient]:
        """Get quantum client (may be None if not connected)."""
        return self._client

    def set_client(self, client: QuantumClient) -> None:
        """Set the quantum client.

        Args:
            client: Configured QuantumClient instance
        """
        self._client = client
        self._logger.info("Quantum client configured")

    def list_tools(self) -> list[ToolInfo]:
        """List all registered tools.

        Returns:
            List of ToolInfo for each registered tool
        """
        return list(self._tool_info.values())

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> str:
        """Call a registered tool.

        Args:
            name: Tool name
            arguments: Tool arguments

        Returns:
            Tool result as string

        Raises:
            KeyError: If tool not found
        """
        if name not in self._tools:
            raise KeyError(f"Tool not found: {name}")

        self._logger.debug("Calling tool", tool=name, arguments=arguments)
        result = await self._tools[name](**arguments)
        return result

    def register_tool(
        self,
        name: str,
        description: str,
        schema: dict[str, Any],
        handler: Callable[..., Coroutine[Any, Any, str]],
    ) -> None:
        """Register a new tool.

        Args:
            name: Tool name
            description: Tool description
            schema: JSON schema for tool arguments
            handler: Async function to handle tool calls
        """
        self._tools[name] = handler
        self._tool_info[name] = ToolInfo(
            name=name,
            description=description,
            input_schema=schema,
        )

        # Register with FastMCP to expose via MCP protocol
        self._mcp.tool(name=name, description=description)(handler)

        self._logger.debug("Registered tool", tool=name)

    def _register_core_tools(self) -> None:
        """Register core utility tools."""
        # Ping tool for testing connectivity
        self.register_tool(
            name="ping",
            description="Test server connectivity. Returns a pong response.",
            schema={
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "Optional message to echo back",
                    }
                },
            },
            handler=self._ping_handler,
        )

        # Register all quantum tools
        register_all_tools(self)

    async def _ping_handler(self, message: Optional[str] = None) -> str:
        """Handle ping tool calls.

        Args:
            message: Optional message to echo

        Returns:
            Pong response with optional message
        """
        if message:
            return f"pong from quantum-mcp server: {message}"
        return "pong from quantum-mcp server"

    def run(self) -> None:
        """Run the MCP server (stdio mode)."""
        self._logger.info("Starting quantum-mcp server")
        self._mcp.run()


# Singleton instance
_server_instance: Optional[QuantumMCPServer] = None


@lru_cache(maxsize=1)
def create_server() -> QuantumMCPServer:
    """Create or get the singleton MCP server instance.

    Returns:
        QuantumMCPServer singleton instance
    """
    global _server_instance
    if _server_instance is None:
        _server_instance = QuantumMCPServer()

        # Try to configure quantum client
        try:
            settings = get_settings()
            if settings.has_azure_credentials:
                client = QuantumClient(settings)
                _server_instance.set_client(client)
        except Exception as e:
            logger.warning("Could not configure quantum client", error=str(e))

    return _server_instance


def get_server() -> QuantumMCPServer:
    """Get the existing server instance.

    Returns:
        QuantumMCPServer singleton instance

    Raises:
        RuntimeError: If server has not been created yet
    """
    if _server_instance is None:
        raise RuntimeError("Server not initialized. Call create_server() first.")
    return _server_instance
