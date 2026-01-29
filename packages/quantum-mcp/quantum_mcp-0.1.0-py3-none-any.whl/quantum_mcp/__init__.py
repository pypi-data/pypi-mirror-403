# Description: Main package for Quantum MCP Server.
# Description: Provides Azure Quantum integration and multi-agent orchestration via MCP protocol.
"""Quantum Computing and Multi-Agent Orchestration MCP Server."""

from quantum_mcp.config import Settings, get_settings

__version__ = "0.1.0"
__all__ = ["Settings", "get_settings", "__version__"]
