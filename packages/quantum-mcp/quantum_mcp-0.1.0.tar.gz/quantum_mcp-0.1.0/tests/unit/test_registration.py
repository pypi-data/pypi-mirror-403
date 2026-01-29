# Description: Tests for MCP tool registration.
# Description: Validates all quantum computing tools are properly registered.
"""Tests for MCP tool registration."""

import pytest

from quantum_mcp.server import QuantumMCPServer


class TestToolRegistration:
    """Test tool registration with MCP server."""

    @pytest.fixture
    def server(self):
        """Create server instance for testing."""
        return QuantumMCPServer(name="test-server")

    def test_server_registers_ping_tool(self, server):
        """Test ping tool is registered."""
        tools = server.list_tools()
        tool_names = [t.name for t in tools]
        assert "ping" in tool_names

    def test_server_registers_quantum_tools(self, server):
        """Test quantum algorithm tools are registered."""
        tools = server.list_tools()
        tool_names = [t.name for t in tools]

        expected_quantum_tools = [
            "quantum_vqe",
            "quantum_qaoa",
            "quantum_kernel",
            "quantum_run_qsharp",
            "quantum_list_backends",
            "quantum_simulate",
            "quantum_estimate_cost",
            "quantum_anneal",
        ]

        for tool_name in expected_quantum_tools:
            assert tool_name in tool_names, f"Missing quantum tool: {tool_name}"

    def test_all_tools_have_descriptions(self, server):
        """Test all tools have non-empty descriptions."""
        tools = server.list_tools()

        for tool in tools:
            assert tool.description, f"Tool {tool.name} has no description"
            assert len(tool.description) > 10, f"Tool {tool.name} has short description"

    def test_all_tools_have_schemas(self, server):
        """Test all tools have input schemas."""
        tools = server.list_tools()

        for tool in tools:
            assert tool.input_schema, f"Tool {tool.name} has no schema"
            assert "type" in tool.input_schema, f"Tool {tool.name} schema missing type"

    def test_total_tool_count(self, server):
        """Test total number of registered tools."""
        tools = server.list_tools()
        # 1 ping + 8 quantum = 9 tools
        assert len(tools) == 9, f"Expected 9 tools, got {len(tools)}"

    def test_quantum_vqe_schema(self, server):
        """Test quantum_vqe has correct schema properties."""
        tools = server.list_tools()
        vqe_tool = next((t for t in tools if t.name == "quantum_vqe"), None)

        assert vqe_tool is not None
        schema = vqe_tool.input_schema
        props = schema.get("properties", {})

        assert "num_qubits" in props
        assert "ansatz_type" in props
        assert "depth" in props
        assert "hamiltonian_type" in props
        assert "optimizer" in props
        assert "max_iterations" in props
        assert "shots" in props

    @pytest.mark.asyncio
    async def test_ping_tool_callable(self, server):
        """Test ping tool can be called."""
        result = await server.call_tool("ping", {"message": "test"})
        assert "pong" in result.lower()
        assert "test" in result

    @pytest.mark.asyncio
    async def test_unknown_tool_raises(self, server):
        """Test calling unknown tool raises KeyError."""
        with pytest.raises(KeyError, match="Tool not found"):
            await server.call_tool("nonexistent_tool", {})
