# Description: Test MCP server foundation.
# Description: Validates server creation, tool registration, and error handling.
"""Test MCP server foundation."""

import pytest

from quantum_mcp.server import QuantumMCPServer, create_server


class TestServerCreation:
    """Test server creation."""

    def test_create_server(self):
        """Test server can be created."""
        server = create_server()
        assert server is not None

    def test_server_has_name(self):
        """Test server has a name."""
        server = create_server()
        assert server.name == "quantum-mcp"

    def test_server_singleton(self):
        """Test create_server returns same instance."""
        server1 = create_server()
        server2 = create_server()
        assert server1 is server2


class TestQuantumMCPServer:
    """Test QuantumMCPServer class."""

    @pytest.fixture
    def server(self):
        """Create fresh server instance for testing."""
        return QuantumMCPServer()

    def test_server_initialization(self, server: QuantumMCPServer):
        """Test server initializes properly."""
        assert server.mcp is not None
        assert server.name == "quantum-mcp"

    def test_server_has_quantum_client(self, server: QuantumMCPServer):
        """Test server has quantum client reference."""
        assert hasattr(server, "client")

    def test_registered_tools_exist(self, server: QuantumMCPServer):
        """Test that tools are registered."""
        tools = server.list_tools()
        assert len(tools) > 0

    def test_ping_tool_registered(self, server: QuantumMCPServer):
        """Test ping tool is registered."""
        tools = server.list_tools()
        tool_names = [t.name for t in tools]
        assert "ping" in tool_names


class TestToolRegistration:
    """Test tool registration mechanism."""

    @pytest.fixture
    def server(self):
        """Create fresh server instance for testing."""
        return QuantumMCPServer()

    def test_tool_has_description(self, server: QuantumMCPServer):
        """Test registered tools have descriptions."""
        tools = server.list_tools()
        for tool in tools:
            assert tool.description is not None
            assert len(tool.description) > 0

    def test_tool_has_schema(self, server: QuantumMCPServer):
        """Test registered tools have input schema."""
        tools = server.list_tools()
        for tool in tools:
            assert tool.input_schema is not None


class TestPingTool:
    """Test the ping tool functionality."""

    @pytest.fixture
    def server(self):
        """Create fresh server instance for testing."""
        return QuantumMCPServer()

    @pytest.mark.asyncio
    async def test_ping_returns_pong(self, server: QuantumMCPServer):
        """Test ping tool returns pong response."""
        result = await server.call_tool("ping", {})
        assert "pong" in result.lower() or "quantum-mcp" in result.lower()

    @pytest.mark.asyncio
    async def test_ping_with_message(self, server: QuantumMCPServer):
        """Test ping tool with custom message."""
        result = await server.call_tool("ping", {"message": "hello"})
        assert "hello" in result.lower()
