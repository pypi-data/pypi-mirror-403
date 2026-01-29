# Description: Factory function for creating agent instances.
# Description: Creates appropriate agent type based on provider configuration.
"""Agent factory for creating agent instances."""

from __future__ import annotations

from typing import TYPE_CHECKING

from quantum_mcp.agents.base import BaseAgent
from quantum_mcp.agents.claude import ClaudeAgent
from quantum_mcp.agents.local import LocalAgent
from quantum_mcp.agents.openai import OpenAIAgent
from quantum_mcp.agents.protocol import AgentConfig

if TYPE_CHECKING:
    from quantum_mcp.server import QuantumMCPServer


def create_agent(
    config: AgentConfig,
    server: "QuantumMCPServer | None" = None,
) -> BaseAgent:
    """Create an agent instance based on provider type.

    Args:
        config: Agent configuration specifying provider and settings
        server: MCP server instance (required for tool agents)

    Returns:
        Configured agent instance

    Raises:
        ValueError: If provider is unknown or tool agent lacks server
    """
    provider = config.provider.lower()

    if provider == "claude":
        return ClaudeAgent(config)

    elif provider == "openai":
        return OpenAIAgent(config)

    elif provider in ("local", "ollama"):
        return LocalAgent(config)

    elif provider == "tool":
        if server is None:
            raise ValueError("Tool agents require a server instance")
        from quantum_mcp.agents.tool import ToolAgent

        return ToolAgent(config, server)

    else:
        raise ValueError(f"Unknown provider: {provider}")


def create_agents_from_configs(
    configs: list[AgentConfig],
    server: "QuantumMCPServer | None" = None,
) -> list[BaseAgent]:
    """Create multiple agents from a list of configurations.

    Args:
        configs: List of agent configurations
        server: MCP server instance (required for tool agents)

    Returns:
        List of configured agent instances
    """
    return [create_agent(config, server) for config in configs]
