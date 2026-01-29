# Description: Agents module for multi-agent system.
# Description: Exports protocol, base classes, and agent implementations.
"""Agents module for multi-agent system."""

from quantum_mcp.agents.base import BaseAgent
from quantum_mcp.agents.claude import ClaudeAgent
from quantum_mcp.agents.factory import create_agent, create_agents_from_configs
from quantum_mcp.agents.local import LocalAgent
from quantum_mcp.agents.openai import OpenAIAgent
from quantum_mcp.agents.protocol import (
    AgentCapability,
    AgentConfig,
    AgentProtocol,
    AgentResponse,
    AgentStatus,
)
from quantum_mcp.agents.tool import ToolAgent

__all__ = [
    "AgentCapability",
    "AgentConfig",
    "AgentProtocol",
    "AgentResponse",
    "AgentStatus",
    "BaseAgent",
    "ClaudeAgent",
    "LocalAgent",
    "OpenAIAgent",
    "ToolAgent",
    "create_agent",
    "create_agents_from_configs",
]
