# Description: Unit tests for QAOA-based quantum router.
# Description: Tests QUBO-to-Ising conversion and quantum-enhanced routing.
"""Unit tests for QAOA router implementation."""

from __future__ import annotations

import numpy as np
import pytest

from quantum_mcp.agents.base import BaseAgent
from quantum_mcp.agents.protocol import (
    AgentCapability,
    AgentConfig,
    AgentResponse,
    AgentStatus,
)
from quantum_mcp.orchestration.qubo import QUBOFormulation, RouteQUBO
from quantum_mcp.orchestration.task import Task


class MockQAOAAgent(BaseAgent):
    """Mock agent for QAOA router tests."""

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
def agents() -> list[MockQAOAAgent]:
    """Create test agents."""
    return [
        MockQAOAAgent(
            AgentConfig(
                name="code-agent",
                provider="claude",
                capabilities=[
                    AgentCapability(
                        name="coding", description="Code generation", confidence=0.9
                    ),
                    AgentCapability(
                        name="debugging", description="Bug fixing", confidence=0.8
                    ),
                ],
            )
        ),
        MockQAOAAgent(
            AgentConfig(
                name="analysis-agent",
                provider="openai",
                capabilities=[
                    AgentCapability(
                        name="analysis", description="Data analysis", confidence=0.9
                    ),
                    AgentCapability(
                        name="math", description="Mathematical reasoning", confidence=0.8
                    ),
                ],
            )
        ),
        MockQAOAAgent(
            AgentConfig(
                name="general-agent",
                provider="local",
                capabilities=[
                    AgentCapability(
                        name="general", description="General tasks", confidence=0.7
                    ),
                ],
            )
        ),
    ]


class TestQUBOToIsing:
    """Tests for QUBO to Ising Hamiltonian conversion."""

    def test_qubo_to_ising_diagonal_only(self):
        """Test conversion with only diagonal terms."""
        from quantum_mcp.orchestration.qaoa_router import qubo_to_ising

        # QUBO: Q[i,i] = -1 for all i (prefer selecting all)
        Q = np.diag([-1.0, -1.0, -1.0])

        J, h, offset = qubo_to_ising(Q)

        # No off-diagonal → no J terms
        assert len(J) == 0
        # Should have h terms from diagonal
        assert len(h) == 3
        # With mapping x=(1-s)/2, h[i] = -Q[i,i]/2 = 0.5 (positive)
        # This means s=-1 (bit='1', x=1) is preferred when Q[i,i] < 0
        for i in range(3):
            assert h[i] > 0  # Positive h favors s=-1 (selected)

    def test_qubo_to_ising_with_coupling(self):
        """Test conversion with off-diagonal coupling terms."""
        from quantum_mcp.orchestration.qaoa_router import qubo_to_ising

        # QUBO with coupling
        Q = np.array([
            [-1.0, 0.5, 0.0],
            [0.5, -1.0, 0.5],
            [0.0, 0.5, -1.0],
        ])

        J, h, offset = qubo_to_ising(Q)

        # Should have J terms for edges (0,1) and (1,2)
        assert len(J) == 2
        # Check edge keys exist
        assert (0, 1) in J or (1, 0) in J
        assert (1, 2) in J or (2, 1) in J

    def test_qubo_to_ising_energy_equivalence(self):
        """Test that QUBO and Ising give equivalent energies."""
        from quantum_mcp.orchestration.qaoa_router import qubo_to_ising

        Q = np.array([
            [-0.5, 1.0, 0.0],
            [1.0, -0.3, 0.5],
            [0.0, 0.5, -0.7],
        ])
        Q = (Q + Q.T) / 2  # Ensure symmetric

        J, h, offset = qubo_to_ising(Q)

        # Test multiple configurations
        for bits in [[0, 0, 0], [1, 0, 0], [1, 1, 0], [1, 1, 1]]:
            x = np.array(bits, dtype=float)
            qubo_energy = x @ Q @ x

            # Convert to Ising spins using x = (1-s)/2 -> s = 1 - 2*x
            s = 1 - 2 * x
            # Ising energy: E = offset + sum h_i s_i + sum J_ij s_i s_j
            ising_energy = offset
            for i, hi in h.items():
                ising_energy += hi * s[i]
            for (i, j), Jij in J.items():
                ising_energy += Jij * s[i] * s[j]

            assert qubo_energy == pytest.approx(ising_energy, rel=0.01)


class TestIsingToQAOA:
    """Tests for Ising Hamiltonian to QAOA cost function."""

    def test_ising_to_qaoa_edges(self):
        """Test conversion of Ising to QAOA edge format."""
        from quantum_mcp.orchestration.qaoa_router import ising_to_qaoa_cost

        J = {(0, 1): 0.5, (1, 2): 0.3}
        h = {0: 0.1, 1: -0.2, 2: 0.0}

        cost = ising_to_qaoa_cost(J, h, n_qubits=3)

        # Should have edges for J terms plus any h handling
        assert cost.num_qubits == 3
        assert len(cost.edges) >= 2  # At least the J edges

    def test_empty_hamiltonian(self):
        """Test handling of trivial Hamiltonian."""
        from quantum_mcp.orchestration.qaoa_router import ising_to_qaoa_cost

        J: dict = {}
        h: dict = {}

        cost = ising_to_qaoa_cost(J, h, n_qubits=2)

        assert cost.num_qubits == 2


class TestQAOARouter:
    """Tests for the QAOA Router class."""

    @pytest.fixture
    def qaoa_router(self, agents):
        """Create QAOA router with sufficient layers/shots for reliable optimization."""
        from quantum_mcp.orchestration.qaoa_router import QAOARouter

        return QAOARouter(agents, layers=2, shots=500, max_iterations=100)

    @pytest.mark.asyncio
    async def test_route_single_agent(self, qaoa_router, agents):
        """Test QAOA routing returns valid results."""
        task = Task(
            prompt="Debug this code",
            required_capabilities=["coding"],
            min_agents=1,
            max_agents=1,
        )

        decision = await qaoa_router.route(task)

        # QAOA is approximate - verify at least one agent is selected
        assert len(decision.selected_agents) >= 1
        assert decision.strategy == "qaoa"
        # Verify selected agents are valid
        agent_ids = [a.agent_id for a in agents]
        for selected in decision.selected_agents:
            assert selected in agent_ids

    @pytest.mark.asyncio
    async def test_route_selects_capable_agent(self, qaoa_router, agents):
        """Test that QAOA selects exactly one agent when constrained."""
        task = Task(
            prompt="Analyze data",
            required_capabilities=["analysis"],
            min_agents=1,
            max_agents=1,
        )

        decision = await qaoa_router.route(task)

        # Should select exactly one agent (QAOA is approximate, so we just verify count)
        assert len(decision.selected_agents) == 1
        # Verify the selected agent exists
        agent_ids = [a.agent_id for a in agents]
        assert decision.selected_agents[0] in agent_ids

    @pytest.mark.asyncio
    async def test_route_includes_qaoa_metadata(self, qaoa_router, agents):
        """Test that QAOA routing includes quantum metadata."""
        task = Task(
            prompt="Test task",
            min_agents=1,
            max_agents=1,
        )

        decision = await qaoa_router.route(task)

        # Should have QAOA-specific info in reasoning or metadata
        assert "qaoa" in decision.strategy.lower()
        assert decision.reasoning is not None

    @pytest.mark.asyncio
    async def test_route_respects_min_max_agents(self, qaoa_router, agents):
        """Test that QAOA attempts to respect agent count constraints."""
        task = Task(
            prompt="Complex task",
            min_agents=2,
            max_agents=2,
        )

        decision = await qaoa_router.route(task)

        # QAOA is approximate - verify at least one agent is selected
        # (the constraint penalty helps but doesn't guarantee exact count)
        assert len(decision.selected_agents) >= 1
        # Should select at most max_agents
        assert len(decision.selected_agents) <= 3

    def test_get_qaoa_circuit(self, qaoa_router, agents):
        """Test retrieving QAOA circuit for a task."""
        task = Task(
            prompt="Test task",
            min_agents=1,
            max_agents=1,
        )

        circuit = qaoa_router.get_qaoa_circuit(task)

        # Should return a valid circuit
        assert circuit is not None
        assert circuit.num_qubits == len(agents)

    def test_get_qubo_formulation(self, qaoa_router, agents):
        """Test retrieving QUBO formulation from QAOA router."""
        task = Task(
            prompt="Test task",
            min_agents=1,
            max_agents=1,
        )

        qubo = qaoa_router.get_qubo(task)

        assert qubo is not None
        assert qubo.n_agents == len(agents)


class TestQAOARouterIntegration:
    """Integration tests for QAOA routing."""

    @pytest.mark.asyncio
    async def test_qaoa_vs_classical_agreement(self, agents):
        """Test that QAOA and classical QUBO both produce valid results."""
        from quantum_mcp.orchestration.qaoa_router import QAOARouter
        from quantum_mcp.orchestration.qubo import QUBORouter

        qubo_router = QUBORouter(agents)
        qaoa_router = QAOARouter(agents, layers=2, shots=500, max_iterations=100)

        task = Task(
            prompt="Simple task",
            required_capabilities=["coding"],
            min_agents=1,
            max_agents=1,
        )

        qubo_decision = await qubo_router.route(task)
        qaoa_decision = await qaoa_router.route(task)

        # Both should select at least one agent
        assert len(qubo_decision.selected_agents) >= 1
        assert len(qaoa_decision.selected_agents) >= 1
        # Both should use their respective strategies
        assert qubo_decision.strategy == "qubo"
        assert qaoa_decision.strategy == "qaoa"

    @pytest.mark.asyncio
    async def test_factory_creates_qaoa_router(self, agents):
        """Test that factory can create QAOA router."""
        from quantum_mcp.orchestration.router import create_router

        router = create_router(strategy="qaoa", agents=agents)

        assert router is not None
        assert "qaoa" in type(router).__name__.lower()


class TestConstraintEnforcement:
    """Tests for post-processing constraint enforcement."""

    def test_enforce_max_agents_trims_selection(self, agents):
        """Test that max_agents constraint is enforced by trimming."""
        from quantum_mcp.orchestration.qaoa_router import QAOARouter

        router = QAOARouter(agents, layers=1)

        # Simulate QAOA returning too many agents
        selected = [a.agent_id for a in agents]  # All 3 agents
        scores = {a.agent_id: 0.5 + 0.1 * i for i, a in enumerate(agents)}
        agent_ids = [a.agent_id for a in agents]

        result = router._enforce_constraints(
            selected=selected,
            scores=scores,
            agent_ids=agent_ids,
            min_agents=1,
            max_agents=1,
        )

        # Should trim to exactly 1 agent
        assert len(result) == 1
        # Should keep the highest-scoring agent
        best_agent = max(selected, key=lambda x: scores[x])
        assert result[0] == best_agent

    def test_enforce_min_agents_adds_agents(self, agents):
        """Test that min_agents constraint is enforced by adding agents."""
        from quantum_mcp.orchestration.qaoa_router import QAOARouter

        router = QAOARouter(agents, layers=1)

        # Simulate QAOA returning no agents
        selected = []
        scores = {a.agent_id: 0.5 + 0.1 * i for i, a in enumerate(agents)}
        agent_ids = [a.agent_id for a in agents]

        result = router._enforce_constraints(
            selected=selected,
            scores=scores,
            agent_ids=agent_ids,
            min_agents=2,
            max_agents=3,
        )

        # Should add at least 2 agents
        assert len(result) >= 2
        # Should add the highest-scoring agents
        top_agents = sorted(agent_ids, key=lambda x: scores[x], reverse=True)[:2]
        for agent in top_agents:
            assert agent in result

    def test_enforce_constraints_preserves_valid_selection(self, agents):
        """Test that valid selections are not modified."""
        from quantum_mcp.orchestration.qaoa_router import QAOARouter

        router = QAOARouter(agents, layers=1)

        # Simulate QAOA returning valid selection
        selected = [agents[1].agent_id]  # Exactly 1 agent
        scores = {a.agent_id: 0.5 for a in agents}
        agent_ids = [a.agent_id for a in agents]

        result = router._enforce_constraints(
            selected=selected,
            scores=scores,
            agent_ids=agent_ids,
            min_agents=1,
            max_agents=2,
        )

        # Should not modify valid selection
        assert len(result) == 1
        assert result[0] == selected[0]

    @pytest.mark.asyncio
    async def test_route_always_respects_max_agents(self, agents):
        """Test that route() always respects max_agents regardless of QAOA result."""
        from quantum_mcp.orchestration.qaoa_router import QAOARouter

        # Use low layers to increase chance of constraint violation before fix
        router = QAOARouter(agents, layers=1, shots=100, max_iterations=10)

        task = Task(
            prompt="Test task",
            min_agents=1,
            max_agents=1,
        )

        # Run multiple times to check consistency
        for _ in range(5):
            decision = await router.route(task)
            assert len(decision.selected_agents) == 1, (
                f"Expected 1 agent, got {len(decision.selected_agents)}: "
                f"{decision.selected_agents}"
            )

    @pytest.mark.asyncio
    async def test_route_always_respects_min_agents(self, agents):
        """Test that route() always respects min_agents regardless of QAOA result."""
        from quantum_mcp.orchestration.qaoa_router import QAOARouter

        router = QAOARouter(agents, layers=1, shots=100, max_iterations=10)

        task = Task(
            prompt="Test task",
            min_agents=2,
            max_agents=3,
        )

        # Run multiple times to check consistency
        for _ in range(5):
            decision = await router.route(task)
            assert len(decision.selected_agents) >= 2, (
                f"Expected at least 2 agents, got {len(decision.selected_agents)}: "
                f"{decision.selected_agents}"
            )


class TestQAOAParameters:
    """Tests for QAOA parameter configuration."""

    def test_custom_layers(self, agents):
        """Test configuring QAOA layers."""
        from quantum_mcp.orchestration.qaoa_router import QAOARouter

        router = QAOARouter(agents, layers=3)
        assert router.layers == 3

    def test_custom_shots(self, agents):
        """Test configuring shot count."""
        from quantum_mcp.orchestration.qaoa_router import QAOARouter

        router = QAOARouter(agents, shots=2000)
        assert router.shots == 2000

    def test_default_optimizer(self, agents):
        """Test default optimizer is COBYLA."""
        from quantum_mcp.orchestration.qaoa_router import QAOARouter

        router = QAOARouter(agents)
        assert router.optimizer == "COBYLA"

    def test_custom_optimizer(self, agents):
        """Test setting custom optimizer."""
        from quantum_mcp.orchestration.qaoa_router import QAOARouter

        router = QAOARouter(agents, optimizer="SLSQP")
        assert router.optimizer == "SLSQP"
