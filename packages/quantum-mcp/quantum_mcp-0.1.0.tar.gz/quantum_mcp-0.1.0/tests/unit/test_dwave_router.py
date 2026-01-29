# Description: Unit tests for DWaveRouter implementation.
# Description: Tests routing with ExactSolver backend (no D-Wave hardware needed).
"""Unit tests for DWaveRouter."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import TYPE_CHECKING

import pytest

from quantum_mcp.agents.base import BaseAgent
from quantum_mcp.agents.protocol import AgentCapability, AgentConfig, AgentResponse
from quantum_mcp.backends import ExactSolverBackend
from quantum_mcp.orchestration import DWaveRouter, Task, create_router

if TYPE_CHECKING:
    pass


class MockAgent(BaseAgent):
    """Mock agent for testing."""

    def __init__(
        self,
        agent_id: str,
        name: str,
        capabilities: list[str] | None = None,
        provider: str = "test",
    ) -> None:
        """Initialize mock agent."""
        config = AgentConfig(
            name=name,
            provider=provider,
            capabilities=[
                AgentCapability(name=cap, description=f"{cap} capability", confidence=0.8)
                for cap in (capabilities or [])
            ],
        )
        super().__init__(config)
        # Override the auto-generated agent_id with our test ID
        self._agent_id = agent_id

    async def execute(self, prompt: str) -> AgentResponse:
        """Execute prompt (mock implementation)."""
        return AgentResponse(
            content=f"Processed by {self.name}: {prompt}",
            model=self.provider,
            usage={"prompt_tokens": 10, "completion_tokens": 20},
        )

    async def stream(self, prompt: str) -> AsyncIterator[str]:
        """Stream response (mock implementation)."""
        yield f"Processed by {self.name}: {prompt}"

    async def health_check(self) -> bool:
        """Check health (mock implementation)."""
        return True


@pytest.fixture
def agents() -> list[BaseAgent]:
    """Create test agents."""
    return [
        MockAgent("agent-1", "Agent One", ["code", "math"]),
        MockAgent("agent-2", "Agent Two", ["code", "writing"]),
        MockAgent("agent-3", "Agent Three", ["writing", "research"]),
    ]


@pytest.fixture
def task() -> Task:
    """Create a test task."""
    return Task(
        prompt="Test task content",
        required_capabilities=["code"],
        min_agents=1,
        max_agents=1,
    )


class TestDWaveRouterCreation:
    """Tests for DWaveRouter instantiation."""

    def test_create_router(self, agents: list[BaseAgent]) -> None:
        """Test creating a DWaveRouter."""
        router = DWaveRouter(agents)
        assert router is not None
        assert len(router.agents) == 3

    def test_create_router_via_factory(self, agents: list[BaseAgent]) -> None:
        """Test creating DWaveRouter via create_router factory."""
        router = create_router("dwave", agents)
        assert isinstance(router, DWaveRouter)

    def test_create_with_custom_backend(self, agents: list[BaseAgent]) -> None:
        """Test creating router with custom backend."""
        backend = ExactSolverBackend(max_variables=10)
        router = DWaveRouter(agents, backend=backend)
        assert router._backend is backend

    def test_create_with_custom_params(self, agents: list[BaseAgent]) -> None:
        """Test creating router with custom parameters."""
        router = DWaveRouter(
            agents,
            penalty=5.0,
            num_reads=50,
            backend_type="exact",
        )
        assert router._penalty == 5.0
        assert router._num_reads == 50
        assert router._backend_type == "exact"


class TestDWaveRouterRouting:
    """Tests for DWaveRouter routing functionality."""

    @pytest.mark.asyncio
    async def test_route_single_agent(
        self,
        agents: list[BaseAgent],
        task: Task,
    ) -> None:
        """Test routing to select a single agent."""
        router = DWaveRouter(agents, backend_type="exact")
        decision = await router.route(task)

        assert decision.task_id == task.task_id
        assert len(decision.selected_agents) == 1
        assert decision.strategy == "dwave"
        assert "energy=" in decision.reasoning

    @pytest.mark.asyncio
    async def test_route_multiple_agents(self, agents: list[BaseAgent]) -> None:
        """Test routing to select multiple agents."""
        task = Task(
            prompt="Multi-agent task",
            required_capabilities=["code"],
            min_agents=2,
            max_agents=2,
        )
        router = DWaveRouter(agents, backend_type="exact")
        decision = await router.route(task)

        assert len(decision.selected_agents) == 2

    @pytest.mark.asyncio
    async def test_route_prefers_capable_agents(
        self,
        agents: list[BaseAgent],
    ) -> None:
        """Test that routing prefers agents with matching capabilities."""
        task = Task(
            prompt="Code review task",
            required_capabilities=["code"],
            min_agents=1,
            max_agents=1,
        )
        router = DWaveRouter(agents, backend_type="exact")
        decision = await router.route(task)

        # Agent 1 and 2 have "code" capability, so one should be selected
        selected = decision.selected_agents[0]
        assert selected in ["agent-1", "agent-2"]

    @pytest.mark.asyncio
    async def test_route_includes_scores(
        self,
        agents: list[BaseAgent],
        task: Task,
    ) -> None:
        """Test that routing decision includes scores."""
        router = DWaveRouter(agents, backend_type="exact")
        decision = await router.route(task)

        assert len(decision.scores) == 3
        for agent_id in decision.scores:
            assert 0.0 <= decision.scores[agent_id] <= 1.0

    @pytest.mark.asyncio
    async def test_route_reasoning_format(
        self,
        agents: list[BaseAgent],
        task: Task,
    ) -> None:
        """Test reasoning string format."""
        router = DWaveRouter(agents, backend_type="exact")
        decision = await router.route(task)

        assert "D-Wave annealing" in decision.reasoning
        assert "energy=" in decision.reasoning
        assert "num_reads=" in decision.reasoning
        assert "samples=" in decision.reasoning


class TestDWaveRouterQUBOConversion:
    """Tests for QUBO matrix conversion."""

    @pytest.mark.asyncio
    async def test_matrix_to_qubo_dict(self, agents: list[BaseAgent]) -> None:
        """Test conversion of QUBO matrix to dict format."""
        task = Task(
            prompt="Test task",
            required_capabilities=["code"],
            min_agents=1,
            max_agents=1,
        )
        router = DWaveRouter(agents, backend_type="exact")
        qubo = router.get_qubo(task)

        Q_dict = router._matrix_to_qubo_dict(qubo)

        # Should have entries for all non-zero elements
        assert isinstance(Q_dict, dict)
        # Keys should be tuples of ints
        for key in Q_dict:
            assert isinstance(key, tuple)
            assert len(key) == 2
            assert key[0] <= key[1]  # Upper triangle

    @pytest.mark.asyncio
    async def test_decode_bitstring(self, agents: list[BaseAgent]) -> None:
        """Test decoding bitstring to agent IDs."""
        router = DWaveRouter(agents, backend_type="exact")
        agent_ids = ["agent-1", "agent-2", "agent-3"]

        # Select agents 0 and 2
        bitstring = {0: 1, 1: 0, 2: 1}
        selected = router._decode_bitstring(bitstring, agent_ids)

        assert selected == ["agent-1", "agent-3"]

    @pytest.mark.asyncio
    async def test_decode_empty_bitstring(self, agents: list[BaseAgent]) -> None:
        """Test decoding empty bitstring."""
        router = DWaveRouter(agents, backend_type="exact")
        agent_ids = ["agent-1", "agent-2"]

        bitstring = {0: 0, 1: 0}
        selected = router._decode_bitstring(bitstring, agent_ids)

        assert selected == []


class TestDWaveRouterBackendManagement:
    """Tests for backend lifecycle management."""

    @pytest.mark.asyncio
    async def test_lazy_backend_init(self, agents: list[BaseAgent]) -> None:
        """Test that backend is lazily initialized."""
        router = DWaveRouter(agents, backend_type="exact")
        assert router._backend is None

        task = Task(prompt="Test", min_agents=1, max_agents=1)
        await router.route(task)

        # Backend should now be initialized
        assert router._backend is not None
        assert router._backend.is_connected

    @pytest.mark.asyncio
    async def test_close_backend(self, agents: list[BaseAgent]) -> None:
        """Test closing the backend connection."""
        router = DWaveRouter(agents, backend_type="exact")
        task = Task(prompt="Test", min_agents=1, max_agents=1)
        await router.route(task)

        assert router._backend.is_connected
        await router.close()
        assert not router._backend.is_connected

    @pytest.mark.asyncio
    async def test_reuse_backend_connection(
        self,
        agents: list[BaseAgent],
    ) -> None:
        """Test that backend connection is reused across routes."""
        router = DWaveRouter(agents, backend_type="exact")

        task1 = Task(prompt="Task 1", min_agents=1, max_agents=1)
        task2 = Task(prompt="Task 2", min_agents=1, max_agents=1)

        await router.route(task1)
        backend1 = router._backend

        await router.route(task2)
        backend2 = router._backend

        # Should be the same backend instance
        assert backend1 is backend2


class TestDWaveRouterIntegration:
    """Integration tests for DWaveRouter with ExactSolver."""

    @pytest.mark.asyncio
    async def test_end_to_end_routing(self) -> None:
        """Test complete routing workflow."""
        agents = [
            MockAgent("fast", "Fast Agent", ["speed"], provider="local"),
            MockAgent("smart", "Smart Agent", ["reasoning"], provider="openai"),
            MockAgent("cheap", "Cheap Agent", ["budget"], provider="local"),
        ]

        task = Task(
            prompt="Complex reasoning task",
            required_capabilities=["reasoning"],
            preferred_providers=["openai"],
            min_agents=1,
            max_agents=1,
        )

        router = DWaveRouter(agents, backend_type="exact", num_reads=50)
        decision = await router.route(task)

        # Should select "smart" agent (has reasoning + preferred provider)
        assert "smart" in decision.selected_agents
        assert decision.scores["smart"] > decision.scores["fast"]
        assert decision.scores["smart"] > decision.scores["cheap"]

        await router.close()

    @pytest.mark.asyncio
    async def test_deterministic_results(self, agents: list[BaseAgent]) -> None:
        """Test that ExactSolver gives deterministic results."""
        task = Task(
            prompt="Deterministic test",
            required_capabilities=["code"],
            min_agents=1,
            max_agents=1,
        )

        # Run routing multiple times
        results = []
        for _ in range(3):
            router = DWaveRouter(agents, backend_type="exact")
            decision = await router.route(task)
            results.append(decision.selected_agents)
            await router.close()

        # All results should be the same
        assert all(r == results[0] for r in results)


class TestDWaveRouterEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_single_agent(self) -> None:
        """Test routing with only one agent."""
        agents = [MockAgent("only", "Only Agent", ["everything"])]
        task = Task(prompt="Single agent task", min_agents=1, max_agents=1)

        router = DWaveRouter(agents, backend_type="exact")
        decision = await router.route(task)

        assert decision.selected_agents == ["only"]

    @pytest.mark.asyncio
    async def test_no_matching_capabilities(self) -> None:
        """Test routing when no agent has required capabilities."""
        agents = [
            MockAgent("a1", "Agent 1", ["skill_a"]),
            MockAgent("a2", "Agent 2", ["skill_b"]),
        ]
        task = Task(
            prompt="Task needing skill_c",
            required_capabilities=["skill_c"],
            min_agents=1,
            max_agents=1,
        )

        router = DWaveRouter(agents, backend_type="exact")
        decision = await router.route(task)

        # Should still select an agent (best available)
        assert len(decision.selected_agents) == 1

    @pytest.mark.asyncio
    async def test_many_agents(self) -> None:
        """Test routing with many agents."""
        agents = [
            MockAgent(f"agent-{i}", f"Agent {i}", [f"skill-{i}"])
            for i in range(20)
        ]
        task = Task(prompt="Large pool task", min_agents=3, max_agents=3)

        router = DWaveRouter(agents, backend_type="exact")
        decision = await router.route(task)

        assert len(decision.selected_agents) == 3
        assert len(set(decision.selected_agents)) == 3  # All unique
