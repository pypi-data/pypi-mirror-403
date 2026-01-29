# Description: Base agent class providing common functionality for all agents.
# Description: Abstract base that concrete agent implementations extend.
"""Base agent class for multi-agent system."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, AsyncIterator

import structlog

from quantum_mcp.agents.protocol import (
    AgentCapability,
    AgentConfig,
    AgentResponse,
)

if TYPE_CHECKING:
    pass

logger = structlog.get_logger()


class BaseAgent(ABC):
    """Abstract base class for all agent implementations.

    Provides common functionality for agent identification, capability
    management, and logging. Concrete implementations must provide
    execute(), stream(), and health_check() methods.
    """

    def __init__(self, config: AgentConfig) -> None:
        """Initialize base agent.

        Args:
            config: Agent configuration
        """
        self._config = config
        self._agent_id = f"{config.name}-{uuid.uuid4().hex[:8]}"
        self._logger = logger.bind(
            agent_id=self._agent_id,
            agent_name=config.name,
            provider=config.provider,
        )
        self._logger.debug("Agent initialized")

    @property
    def agent_id(self) -> str:
        """Get unique agent identifier."""
        return self._agent_id

    @property
    def name(self) -> str:
        """Get agent name."""
        return self._config.name

    @property
    def provider(self) -> str:
        """Get agent provider type."""
        return self._config.provider

    @property
    def model(self) -> str | None:
        """Get model name if specified."""
        return self._config.model

    @property
    def config(self) -> AgentConfig:
        """Get full agent configuration."""
        return self._config

    def has_capability(self, capability_name: str) -> bool:
        """Check if agent has a specific capability.

        Args:
            capability_name: Name of the capability to check

        Returns:
            True if agent has the capability
        """
        return any(
            cap.name == capability_name for cap in self._config.capabilities
        )

    def get_capabilities(self) -> list[AgentCapability]:
        """Get all capabilities of this agent.

        Returns:
            List of agent capabilities
        """
        return self._config.capabilities.copy()

    def get_capability(self, name: str) -> AgentCapability | None:
        """Get a specific capability by name.

        Args:
            name: Capability name to find

        Returns:
            AgentCapability if found, None otherwise
        """
        for cap in self._config.capabilities:
            if cap.name == name:
                return cap
        return None

    @abstractmethod
    async def execute(self, prompt: str) -> AgentResponse:
        """Execute a prompt and return the response.

        Args:
            prompt: The prompt to execute

        Returns:
            AgentResponse with the result

        Raises:
            NotImplementedError: Subclasses must implement this method
        """
        raise NotImplementedError

    @abstractmethod
    async def stream(self, prompt: str) -> AsyncIterator[str]:
        """Stream response tokens for a prompt.

        Args:
            prompt: The prompt to execute

        Yields:
            Response tokens as they become available

        Raises:
            NotImplementedError: Subclasses must implement this method
        """
        raise NotImplementedError
        yield  # Make this a generator

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the agent is healthy and ready.

        Returns:
            True if healthy, False otherwise

        Raises:
            NotImplementedError: Subclasses must implement this method
        """
        raise NotImplementedError

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"{self.__class__.__name__}("
            f"agent_id={self._agent_id!r}, "
            f"name={self.name!r}, "
            f"provider={self.provider!r})"
        )
