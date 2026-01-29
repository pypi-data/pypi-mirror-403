# Description: Agent protocol defining the interface for all agents.
# Description: Contains capability, config, response models and Protocol class.
"""Agent protocol and data models for multi-agent system."""

from __future__ import annotations

from abc import abstractmethod
from enum import Enum
from typing import TYPE_CHECKING, AsyncIterator, Protocol, runtime_checkable

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    pass


class AgentStatus(str, Enum):
    """Status of an agent response or operation."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"


class AgentCapability(BaseModel):
    """Describes a capability that an agent possesses.

    Capabilities are used for routing decisions and capability matching.
    """

    name: str = Field(..., description="Unique capability identifier")
    description: str = Field(..., description="Human-readable description")
    domains: list[str] = Field(
        default_factory=list,
        description="Specific domains or languages this capability covers",
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Agent's confidence in this capability (0-1)",
    )


class AgentConfig(BaseModel):
    """Configuration for an agent instance.

    Used to initialize agents with provider-specific settings.
    """

    name: str = Field(..., description="Human-readable agent name")
    provider: str = Field(..., description="Provider type (claude, openai, local, tool)")
    model: str | None = Field(
        default=None,
        description="Specific model to use (e.g., claude-3-opus, gpt-4)",
    )
    capabilities: list[AgentCapability] = Field(
        default_factory=list,
        description="List of agent capabilities",
    )
    max_tokens: int = Field(
        default=4096,
        ge=1,
        description="Maximum tokens in response",
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature",
    )
    system_prompt: str | None = Field(
        default=None,
        description="System prompt to prepend to all requests",
    )
    timeout_seconds: float = Field(
        default=60.0,
        ge=1.0,
        description="Request timeout in seconds",
    )
    metadata: dict[str, str] = Field(
        default_factory=dict,
        description="Additional provider-specific configuration",
    )


class AgentResponse(BaseModel):
    """Response from an agent execution.

    Contains the response content, status, and execution metrics.
    """

    agent_id: str = Field(..., description="ID of the agent that produced this response")
    content: str = Field(..., description="Response content")
    status: AgentStatus = Field(..., description="Execution status")
    error: str | None = Field(
        default=None,
        description="Error message if status is ERROR",
    )
    tokens_used: int | None = Field(
        default=None,
        description="Number of tokens consumed",
    )
    latency_ms: float | None = Field(
        default=None,
        description="Response latency in milliseconds",
    )
    metadata: dict[str, str] = Field(
        default_factory=dict,
        description="Additional response metadata",
    )


@runtime_checkable
class AgentProtocol(Protocol):
    """Protocol defining the interface for all agents.

    All agent implementations must conform to this interface.
    Provides a consistent API for execution, streaming, and health checks.
    """

    @property
    def agent_id(self) -> str:
        """Unique identifier for this agent instance."""
        ...

    @property
    def name(self) -> str:
        """Human-readable name for this agent."""
        ...

    @property
    def provider(self) -> str:
        """Provider type (claude, openai, local, tool)."""
        ...

    def has_capability(self, capability_name: str) -> bool:
        """Check if agent has a specific capability.

        Args:
            capability_name: Name of the capability to check

        Returns:
            True if agent has the capability, False otherwise
        """
        ...

    def get_capabilities(self) -> list[AgentCapability]:
        """Get all capabilities of this agent.

        Returns:
            List of AgentCapability instances
        """
        ...

    @abstractmethod
    async def execute(self, prompt: str) -> AgentResponse:
        """Execute a prompt and return the response.

        Args:
            prompt: The prompt to execute

        Returns:
            AgentResponse with the result
        """
        ...

    @abstractmethod
    async def stream(self, prompt: str) -> AsyncIterator[str]:
        """Stream response tokens for a prompt.

        Args:
            prompt: The prompt to execute

        Yields:
            Response tokens as they become available
        """
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the agent is healthy and ready.

        Returns:
            True if healthy, False otherwise
        """
        ...
