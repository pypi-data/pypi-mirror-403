# Description: Integration tests for the MCP server.
# Description: Validates server startup, tool registration, and basic operations.
"""Integration tests for the MCP server."""

import pytest

from quantum_mcp.server import (
    BudgetTracker,
    QuantumMCPServer,
    ResultCache,
    SessionManager,
)


class TestMCPServerStartup:
    """Test MCP server initialization and startup."""

    def test_server_creates_successfully(self):
        """Test server can be created."""
        server = QuantumMCPServer(name="test-server")
        assert server.name == "test-server"
        assert server.mcp is not None

    def test_server_has_ping_tool(self):
        """Test server has core ping tool registered."""
        server = QuantumMCPServer(name="test-server")
        tools = server.list_tools()
        tool_names = [t.name for t in tools]
        assert "ping" in tool_names

    def test_server_registers_quantum_tools(self):
        """Test server registers all quantum tools."""
        server = QuantumMCPServer(name="test-server")
        tools = server.list_tools()
        tool_names = [t.name for t in tools]

        # Core quantum tools
        assert "quantum_list_backends" in tool_names
        assert "quantum_simulate" in tool_names
        assert "quantum_estimate_cost" in tool_names

    def test_server_registers_algorithm_tools(self):
        """Test server registers algorithm tools."""
        server = QuantumMCPServer(name="test-server")
        tools = server.list_tools()
        tool_names = [t.name for t in tools]

        # Algorithm tools
        assert "quantum_vqe" in tool_names
        assert "quantum_qaoa" in tool_names
        assert "quantum_kernel" in tool_names

    def test_server_registers_qsharp_tools(self):
        """Test server registers Q# tools."""
        server = QuantumMCPServer(name="test-server")
        tools = server.list_tools()
        tool_names = [t.name for t in tools]

        # Q# tools
        assert "quantum_run_qsharp" in tool_names

    def test_server_registers_annealing_tools(self):
        """Test server registers quantum annealing tools."""
        server = QuantumMCPServer(name="test-server")
        tools = server.list_tools()
        tool_names = [t.name for t in tools]

        # Annealing tools
        assert "quantum_anneal" in tool_names

    def test_all_tools_have_descriptions(self):
        """Test all tools have descriptions."""
        server = QuantumMCPServer(name="test-server")
        tools = server.list_tools()

        for tool in tools:
            assert tool.description is not None
            assert len(tool.description) > 10, f"Tool {tool.name} has short description"

    def test_all_tools_have_schemas(self):
        """Test all tools have input schemas."""
        server = QuantumMCPServer(name="test-server")
        tools = server.list_tools()

        for tool in tools:
            assert tool.input_schema is not None
            assert "type" in tool.input_schema


class TestMCPServerToolExecution:
    """Test MCP server tool execution."""

    @pytest.mark.asyncio
    async def test_ping_tool_responds(self):
        """Test ping tool responds correctly."""
        server = QuantumMCPServer(name="test-server")
        result = await server.call_tool("ping", {})
        assert "pong" in result.lower()
        assert "quantum-mcp" in result

    @pytest.mark.asyncio
    async def test_ping_with_message(self):
        """Test ping echoes message."""
        server = QuantumMCPServer(name="test-server")
        result = await server.call_tool("ping", {"message": "hello"})
        assert "hello" in result

    @pytest.mark.asyncio
    async def test_unknown_tool_raises(self):
        """Test calling unknown tool raises error."""
        server = QuantumMCPServer(name="test-server")
        with pytest.raises(KeyError, match="Tool not found"):
            await server.call_tool("unknown_tool", {})


class TestSessionManager:
    """Test session management."""

    def test_create_session(self):
        """Test creating a session."""
        manager = SessionManager()
        session_id = manager.create_session()
        assert session_id is not None
        assert len(session_id) > 0

    def test_track_job(self):
        """Test tracking a job in session."""
        manager = SessionManager()
        session_id = manager.create_session()
        manager.track_job(session_id, "job-123", "pending")

        jobs = manager.get_session_jobs(session_id)
        assert "job-123" in jobs
        assert jobs["job-123"] == "pending"

    def test_update_job_status(self):
        """Test updating job status."""
        manager = SessionManager()
        session_id = manager.create_session()
        manager.track_job(session_id, "job-123", "pending")
        manager.update_job_status(session_id, "job-123", "completed")

        jobs = manager.get_session_jobs(session_id)
        assert jobs["job-123"] == "completed"

    def test_expire_session(self):
        """Test expiring a session."""
        manager = SessionManager()
        session_id = manager.create_session()
        manager.track_job(session_id, "job-123", "pending")
        manager.expire_session(session_id)

        jobs = manager.get_session_jobs(session_id)
        assert len(jobs) == 0


class TestResultCache:
    """Test result caching."""

    def test_cache_set_get(self):
        """Test setting and getting cached results."""
        cache = ResultCache()
        cache.set("job-123", {"result": "success", "counts": {"00": 100}})

        result = cache.get("job-123")
        assert result is not None
        assert result["result"] == "success"

    def test_cache_miss(self):
        """Test cache miss returns None."""
        cache = ResultCache()
        result = cache.get("nonexistent")
        assert result is None

    def test_cache_invalidate(self):
        """Test invalidating cached result."""
        cache = ResultCache()
        cache.set("job-123", {"result": "success"})
        cache.invalidate("job-123")

        result = cache.get("job-123")
        assert result is None

    def test_cache_clear(self):
        """Test clearing entire cache."""
        cache = ResultCache()
        cache.set("job-1", {"result": "a"})
        cache.set("job-2", {"result": "b"})
        cache.clear()

        assert cache.get("job-1") is None
        assert cache.get("job-2") is None


class TestBudgetTracker:
    """Test budget tracking."""

    def test_budget_initialization(self):
        """Test budget tracker initialization."""
        tracker = BudgetTracker(budget_limit=100.0)
        assert tracker.budget_limit == 100.0
        assert tracker.spent == 0.0
        assert tracker.remaining == 100.0

    def test_can_afford(self):
        """Test can_afford check."""
        tracker = BudgetTracker(budget_limit=10.0)
        assert tracker.can_afford(5.0) is True
        assert tracker.can_afford(15.0) is False

    def test_record_cost(self):
        """Test recording costs."""
        tracker = BudgetTracker(budget_limit=10.0)
        tracker.record_cost(2.5, "job-1")
        tracker.record_cost(3.5, "job-2")

        assert tracker.spent == 6.0
        assert tracker.remaining == 4.0

    def test_strict_mode_raises(self):
        """Test strict mode raises on budget exceed."""
        tracker = BudgetTracker(budget_limit=5.0)
        tracker.record_cost(3.0, "job-1")

        with pytest.raises(ValueError, match="Budget exceeded"):
            tracker.record_cost(5.0, "job-2", strict=True)

    def test_get_history(self):
        """Test getting cost history."""
        tracker = BudgetTracker(budget_limit=10.0)
        tracker.record_cost(1.0, "job-1")
        tracker.record_cost(2.0, "job-2")

        history = tracker.get_history()
        assert len(history) == 2
        assert history[0]["job_id"] == "job-1"
        assert history[0]["cost"] == 1.0


class TestToolCount:
    """Test expected tool counts."""

    def test_minimum_tools_registered(self):
        """Test minimum expected tools are registered."""
        server = QuantumMCPServer(name="test-server")
        tools = server.list_tools()

        # Expected minimum tools:
        # - ping (1)
        # - quantum tools (3): list_backends, simulate, estimate_cost
        # - algorithm tools (4): vqe, qaoa, kernel, anneal
        # - qsharp tools (1): run_qsharp
        # Total: 9

        assert len(tools) >= 9, f"Expected at least 9 tools, got {len(tools)}"

    def test_list_registered_tools(self):
        """Print all registered tools (for documentation)."""
        server = QuantumMCPServer(name="test-server")
        tools = server.list_tools()

        tool_names = sorted([t.name for t in tools])
        print(f"\nRegistered tools ({len(tools)} total):")
        for name in tool_names:
            print(f"  - {name}")

        # This test always passes - it's for documentation
        assert True
