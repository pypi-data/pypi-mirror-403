# Description: Tests for QUBO formulation of agent routing.
# Description: Validates QUBO construction, constraint encoding, and optimization.
"""Tests for QUBO formulation of agent routing."""

import pytest
import numpy as np

from quantum_mcp.orchestration.qubo import (
    QUBORouter,
    QUBOFormulation,
    RouteQUBO,
)
from quantum_mcp.orchestration.task import Task
from quantum_mcp.agents import AgentConfig, AgentCapability
from quantum_mcp.agents.base import BaseAgent
from quantum_mcp.agents.protocol import AgentResponse, AgentStatus


class MockQUBOAgent(BaseAgent):
    """Mock agent for QUBO routing tests."""

    def __init__(self, config: AgentConfig, latency_ms: float = 50.0):
        super().__init__(config)
        self._latency_ms = latency_ms

    async def execute(self, prompt: str) -> AgentResponse:
        return AgentResponse(
            agent_id=self.agent_id,
            content=f"Response from {self.name}",
            status=AgentStatus.SUCCESS,
            tokens_used=100,
            latency_ms=self._latency_ms,
        )

    async def stream(self, prompt: str):
        yield f"Response from {self.name}"

    async def health_check(self) -> bool:
        return True


@pytest.fixture
def agents() -> list[MockQUBOAgent]:
    """Create test agents with different capabilities."""
    return [
        MockQUBOAgent(
            AgentConfig(
                name="code-agent",
                provider="claude",
                capabilities=[
                    AgentCapability(name="code", description="Code generation"),
                    AgentCapability(name="python", description="Python expertise"),
                ],
            )
        ),
        MockQUBOAgent(
            AgentConfig(
                name="analysis-agent",
                provider="openai",
                capabilities=[
                    AgentCapability(name="analysis", description="Data analysis"),
                    AgentCapability(name="reasoning", description="Complex reasoning"),
                ],
            )
        ),
        MockQUBOAgent(
            AgentConfig(
                name="general-agent",
                provider="local",
                capabilities=[
                    AgentCapability(name="general", description="General tasks"),
                ],
            )
        ),
    ]


class TestQUBOFormulation:
    """Test QUBO matrix construction."""

    def test_create_qubo_matrix(self, agents):
        """Test QUBO matrix has correct shape."""
        formulation = QUBOFormulation(n_agents=len(agents))

        # QUBO matrix should be n x n
        assert formulation.n_agents == 3

    def test_set_linear_coefficients(self, agents):
        """Test setting linear (diagonal) coefficients."""
        formulation = QUBOFormulation(n_agents=3)

        # Set scores for each agent
        scores = [0.8, 0.6, 0.3]
        formulation.set_linear_terms(scores)

        Q = formulation.get_qubo_matrix()

        # Diagonal should contain negated scores (for maximization)
        assert Q[0, 0] == pytest.approx(-0.8, rel=0.01)
        assert Q[1, 1] == pytest.approx(-0.6, rel=0.01)
        assert Q[2, 2] == pytest.approx(-0.3, rel=0.01)

    def test_add_selection_constraint(self, agents):
        """Test adding constraint for number of selections."""
        formulation = QUBOFormulation(n_agents=3)
        formulation.set_linear_terms([0.5, 0.5, 0.5])

        # Constraint: select exactly 1 agent
        formulation.add_selection_constraint(target=1, penalty=10.0)

        Q = formulation.get_qubo_matrix()

        # Should have off-diagonal terms from (x1 + x2 + x3 - 1)^2
        # In x^T Q x, off-diagonal (i,j) contributes 2*Q[i,j]*x_i*x_j
        # We want 2*penalty contribution, so Q[i,j] = penalty = 10
        assert Q[0, 1] == pytest.approx(10.0, rel=0.01)
        assert Q[0, 2] == pytest.approx(10.0, rel=0.01)
        assert Q[1, 2] == pytest.approx(10.0, rel=0.01)

    def test_qubo_energy_calculation(self, agents):
        """Test calculating energy for a given selection."""
        formulation = QUBOFormulation(n_agents=3)
        formulation.set_linear_terms([0.8, 0.6, 0.3])
        formulation.add_selection_constraint(target=1, penalty=10.0)

        # Selection: only agent 0
        selection = np.array([1, 0, 0])
        energy = formulation.calculate_energy(selection)

        # Energy should be low (good solution)
        assert energy < 0  # Negative because we're maximizing score

    def test_constraint_violation_increases_energy(self, agents):
        """Test that violating constraints increases energy."""
        formulation = QUBOFormulation(n_agents=3)
        formulation.set_linear_terms([0.8, 0.6, 0.3])
        formulation.add_selection_constraint(target=1, penalty=10.0)

        # Valid selection: exactly 1 agent
        valid = np.array([1, 0, 0])
        valid_energy = formulation.calculate_energy(valid)

        # Invalid selection: 2 agents (violates constraint)
        invalid = np.array([1, 1, 0])
        invalid_energy = formulation.calculate_energy(invalid)

        # Invalid should have higher energy due to penalty
        assert invalid_energy > valid_energy


class TestRouteQUBO:
    """Test RouteQUBO builder for routing problems."""

    def test_build_from_scores(self, agents):
        """Test building QUBO from agent scores."""
        scores = {"agent-0": 0.9, "agent-1": 0.7, "agent-2": 0.4}
        agent_ids = ["agent-0", "agent-1", "agent-2"]

        qubo = RouteQUBO.from_scores(
            agent_ids=agent_ids,
            scores=scores,
            min_agents=1,
            max_agents=1,
        )

        assert qubo.n_agents == 3
        assert qubo.agent_ids == agent_ids

    def test_decode_solution(self, agents):
        """Test decoding binary solution to agent IDs."""
        agent_ids = ["agent-0", "agent-1", "agent-2"]
        scores = {"agent-0": 0.9, "agent-1": 0.7, "agent-2": 0.4}

        qubo = RouteQUBO.from_scores(
            agent_ids=agent_ids,
            scores=scores,
            min_agents=1,
            max_agents=2,
        )

        # Simulate solution: agents 0 and 1 selected
        solution = np.array([1, 1, 0])
        selected = qubo.decode_solution(solution)

        assert "agent-0" in selected
        assert "agent-1" in selected
        assert "agent-2" not in selected

    def test_get_best_classical_solution(self, agents):
        """Test finding best solution via classical enumeration."""
        agent_ids = ["agent-0", "agent-1", "agent-2"]
        scores = {"agent-0": 0.9, "agent-1": 0.7, "agent-2": 0.4}

        qubo = RouteQUBO.from_scores(
            agent_ids=agent_ids,
            scores=scores,
            min_agents=1,
            max_agents=1,
        )

        # Classical solver should find agent-0 (highest score)
        solution, energy = qubo.solve_classical()
        selected = qubo.decode_solution(solution)

        assert "agent-0" in selected
        assert len(selected) == 1

    def test_range_constraint(self, agents):
        """Test min/max agent selection constraints."""
        agent_ids = ["agent-0", "agent-1", "agent-2"]
        scores = {"agent-0": 0.9, "agent-1": 0.7, "agent-2": 0.4}

        qubo = RouteQUBO.from_scores(
            agent_ids=agent_ids,
            scores=scores,
            min_agents=2,
            max_agents=2,
        )

        solution, _ = qubo.solve_classical()
        selected = qubo.decode_solution(solution)

        # Should select exactly 2 agents
        assert len(selected) == 2
        # Should be the top 2 scorers
        assert "agent-0" in selected
        assert "agent-1" in selected


class TestQUBORouter:
    """Test QUBORouter implementation."""

    @pytest.fixture
    def router(self, agents) -> QUBORouter:
        """Create QUBO router for testing."""
        return QUBORouter(agents)

    @pytest.mark.asyncio
    async def test_route_single_agent(self, router, agents):
        """Test routing to select single best agent."""
        task = Task(
            prompt="Write Python code",
            required_capabilities=["code", "python"],
            min_agents=1,
            max_agents=1,
        )

        decision = await router.route(task)

        assert len(decision.selected_agents) == 1
        assert decision.strategy == "qubo"
        # Should select code-agent (best match)
        assert "code-agent" in decision.selected_agents[0]

    @pytest.mark.asyncio
    async def test_route_multiple_agents(self, router, agents):
        """Test routing to select multiple agents."""
        task = Task(
            prompt="Analyze and code",
            required_capabilities=["analysis"],
            min_agents=2,
            max_agents=2,
        )

        decision = await router.route(task)

        assert len(decision.selected_agents) == 2
        # Should include analysis-agent
        agent_names = [a for a in decision.selected_agents]
        assert any("analysis" in a for a in agent_names)

    @pytest.mark.asyncio
    async def test_route_returns_qubo_info(self, router, agents):
        """Test that routing includes QUBO optimization info."""
        task = Task(
            prompt="Do something",
            min_agents=1,
            max_agents=1,
        )

        decision = await router.route(task)

        assert decision.strategy == "qubo"
        assert "qubo_energy" in decision.reasoning.lower() or decision.scores

    @pytest.mark.asyncio
    async def test_scores_in_decision(self, router, agents):
        """Test that decision includes agent scores."""
        task = Task(
            prompt="Write code",
            required_capabilities=["code"],
            min_agents=1,
            max_agents=1,
        )

        decision = await router.route(task)

        # Should have scores for all agents
        assert len(decision.scores) == len(agents)

    def test_get_qubo_formulation(self, router, agents):
        """Test getting the QUBO formulation for a task."""
        task = Task(
            prompt="Test task",
            required_capabilities=["code"],
            min_agents=1,
            max_agents=2,
        )

        qubo = router.get_qubo(task)

        assert qubo is not None
        assert qubo.n_agents == len(agents)

    def test_qubo_compatible_with_qaoa(self, router, agents):
        """Test that QUBO matrix is compatible with QAOA."""
        task = Task(
            prompt="Test task",
            min_agents=1,
            max_agents=1,
        )

        qubo = router.get_qubo(task)
        Q = qubo.formulation.get_qubo_matrix()

        # QUBO matrix should be symmetric
        assert np.allclose(Q, Q.T)

        # Should be square with n_agents dimensions
        assert Q.shape == (len(agents), len(agents))


class TestQUBOIntegration:
    """Integration tests for QUBO routing."""

    @pytest.mark.asyncio
    async def test_qubo_vs_capability_router_agreement(self, agents):
        """Test QUBO router agrees with capability router for simple cases."""
        from quantum_mcp.orchestration.router import CapabilityRouter

        qubo_router = QUBORouter(agents)
        cap_router = CapabilityRouter(agents)

        task = Task(
            prompt="Write Python code",
            required_capabilities=["code", "python"],
            min_agents=1,
            max_agents=1,
        )

        qubo_decision = await qubo_router.route(task)
        cap_decision = await cap_router.route(task)

        # Both should select the same agent for simple single-agent case
        assert qubo_decision.selected_agents == cap_decision.selected_agents

    @pytest.mark.asyncio
    async def test_factory_creates_qubo_router(self, agents):
        """Test create_router factory supports QUBO strategy."""
        from quantum_mcp.orchestration.router import create_router

        router = create_router("qubo", agents)

        assert isinstance(router, QUBORouter)
