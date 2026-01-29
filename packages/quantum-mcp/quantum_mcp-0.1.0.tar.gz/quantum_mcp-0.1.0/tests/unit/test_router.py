# Description: Tests for classical router implementations.
# Description: Validates capability matching, load balancing, and learned routing.
"""Tests for classical router implementations."""

import pytest
from unittest.mock import MagicMock, AsyncMock

from quantum_mcp.agents import (
    AgentCapability,
    AgentConfig,
    AgentResponse,
    AgentStatus,
    BaseAgent,
)
from quantum_mcp.orchestration.task import Task, TaskPriority
from quantum_mcp.orchestration.router import (
    Router,
    CapabilityRouter,
    LoadBalancingRouter,
    LearnedRouter,
    RoutingDecision,
    create_router,
)


class MockAgent(BaseAgent):
    """Mock agent for router testing."""

    def __init__(self, config: AgentConfig, load: int = 0):
        super().__init__(config)
        self._load = load

    async def execute(self, prompt: str) -> AgentResponse:
        return AgentResponse(
            agent_id=self.agent_id,
            content=f"Response from {self.name}",
            status=AgentStatus.SUCCESS,
        )

    async def stream(self, prompt: str):
        yield f"Response from {self.name}"

    async def health_check(self) -> bool:
        return True

    @property
    def current_load(self) -> int:
        return self._load


class TestRoutingDecision:
    """Test RoutingDecision model."""

    def test_decision_creation(self):
        """Test creating a routing decision."""
        decision = RoutingDecision(
            task_id="task-123",
            selected_agents=["agent-1", "agent-2"],
            strategy="capability",
            scores={"agent-1": 0.95, "agent-2": 0.85},
        )
        assert decision.task_id == "task-123"
        assert len(decision.selected_agents) == 2
        assert decision.strategy == "capability"

    def test_decision_reasoning(self):
        """Test decision with reasoning."""
        decision = RoutingDecision(
            task_id="task-123",
            selected_agents=["agent-1"],
            strategy="load_balancing",
            reasoning="Selected agent with lowest load",
        )
        assert decision.reasoning == "Selected agent with lowest load"


class TestCapabilityRouter:
    """Test capability-based routing."""

    @pytest.fixture
    def agents(self) -> list[MockAgent]:
        """Create test agents with different capabilities."""
        return [
            MockAgent(AgentConfig(
                name="coder",
                provider="claude",
                capabilities=[
                    AgentCapability(name="code", description="Code generation"),
                    AgentCapability(name="python", description="Python"),
                ],
            )),
            MockAgent(AgentConfig(
                name="reasoner",
                provider="openai",
                capabilities=[
                    AgentCapability(name="reasoning", description="Complex reasoning"),
                    AgentCapability(name="math", description="Mathematics"),
                ],
            )),
            MockAgent(AgentConfig(
                name="generalist",
                provider="local",
                capabilities=[
                    AgentCapability(name="general", description="General tasks"),
                ],
            )),
        ]

    @pytest.fixture
    def router(self, agents) -> CapabilityRouter:
        """Create capability router."""
        return CapabilityRouter(agents=agents)

    @pytest.mark.asyncio
    async def test_route_by_capability(self, router):
        """Test routing to agent with matching capability."""
        task = Task(
            prompt="Write Python code",
            required_capabilities=["code", "python"],
        )
        decision = await router.route(task)

        assert len(decision.selected_agents) >= 1
        assert "coder" in decision.selected_agents[0]

    @pytest.mark.asyncio
    async def test_route_no_match_returns_generalist(self, router):
        """Test routing falls back when no capability match."""
        task = Task(
            prompt="Do something obscure",
            required_capabilities=["obscure_capability"],
        )
        decision = await router.route(task)

        # Should still return an agent (best available)
        assert len(decision.selected_agents) >= 1

    @pytest.mark.asyncio
    async def test_route_multi_agent(self, router):
        """Test routing for multi-agent task."""
        task = Task(
            prompt="Complex task",
            min_agents=2,
            max_agents=3,
        )
        decision = await router.route(task)

        assert len(decision.selected_agents) >= 2
        assert len(decision.selected_agents) <= 3

    @pytest.mark.asyncio
    async def test_route_preferred_provider(self, router):
        """Test routing respects preferred provider."""
        task = Task(
            prompt="Any task",
            preferred_providers=["openai"],
        )
        decision = await router.route(task)

        # Should prefer openai agent
        assert any("reasoner" in a for a in decision.selected_agents)

    def test_score_agent(self, router, agents):
        """Test agent scoring for capability match."""
        task = Task(
            prompt="Code task",
            required_capabilities=["code"],
        )
        score = router._score_agent(agents[0], task)
        assert score > 0

        # Agent without matching capability scores lower
        score_no_match = router._score_agent(agents[1], task)
        assert score > score_no_match


class TestLoadBalancingRouter:
    """Test load-balancing routing."""

    @pytest.fixture
    def agents(self) -> list[MockAgent]:
        """Create test agents with different loads."""
        return [
            MockAgent(
                AgentConfig(name="busy", provider="claude"),
                load=10,
            ),
            MockAgent(
                AgentConfig(name="idle", provider="openai"),
                load=0,
            ),
            MockAgent(
                AgentConfig(name="medium", provider="local"),
                load=5,
            ),
        ]

    @pytest.fixture
    def router(self, agents) -> LoadBalancingRouter:
        """Create load balancing router."""
        return LoadBalancingRouter(agents=agents)

    @pytest.mark.asyncio
    async def test_route_to_least_loaded(self, router):
        """Test routing prefers least loaded agent."""
        task = Task(prompt="Any task")
        decision = await router.route(task)

        # Should select the idle agent
        assert "idle" in decision.selected_agents[0]

    @pytest.mark.asyncio
    async def test_round_robin_fallback(self, router):
        """Test round-robin when loads are equal."""
        # Set all agents to same load
        for agent in router._agents:
            agent._load = 5

        decisions = []
        for _ in range(3):
            task = Task(prompt="Task")
            decision = await router.route(task)
            decisions.append(decision.selected_agents[0])

        # Should distribute across agents
        unique_agents = set(decisions)
        assert len(unique_agents) >= 2


class TestLearnedRouter:
    """Test learned routing using historical performance."""

    @pytest.fixture
    def agents(self) -> list[MockAgent]:
        """Create test agents."""
        return [
            MockAgent(AgentConfig(
                name="fast-agent",
                provider="claude",
                capabilities=[AgentCapability(name="code", description="Code")],
            )),
            MockAgent(AgentConfig(
                name="accurate-agent",
                provider="openai",
                capabilities=[AgentCapability(name="code", description="Code")],
            )),
        ]

    @pytest.fixture
    def router(self, agents) -> LearnedRouter:
        """Create learned router."""
        return LearnedRouter(agents=agents)

    @pytest.mark.asyncio
    async def test_route_with_no_history(self, router):
        """Test routing with no historical data falls back to capability."""
        task = Task(prompt="Code task", required_capabilities=["code"])
        decision = await router.route(task)

        assert len(decision.selected_agents) >= 1

    def test_record_outcome(self, router):
        """Test recording task outcomes."""
        router.record_outcome(
            agent_id="fast-agent-123",
            task_domain="code",
            success=True,
            latency_ms=500.0,
        )

        stats = router.get_agent_stats("fast-agent-123")
        assert stats["total_tasks"] == 1
        assert stats["success_rate"] == 1.0

    def test_learned_preference(self, router):
        """Test router learns from outcomes."""
        # Record good outcomes for fast-agent
        for _ in range(10):
            router.record_outcome(
                agent_id="fast-agent-123",
                task_domain="code",
                success=True,
                latency_ms=100.0,
            )

        # Record poor outcomes for accurate-agent
        for _ in range(10):
            router.record_outcome(
                agent_id="accurate-agent-456",
                task_domain="code",
                success=False,
                latency_ms=1000.0,
            )

        # Fast agent should score higher for code tasks
        fast_score = router._get_learned_score("fast-agent-123", "code")
        accurate_score = router._get_learned_score("accurate-agent-456", "code")

        assert fast_score > accurate_score


class TestRouterFactory:
    """Test router factory function."""

    @pytest.fixture
    def agents(self) -> list[MockAgent]:
        """Create test agents."""
        return [
            MockAgent(AgentConfig(name="agent1", provider="claude")),
        ]

    def test_create_capability_router(self, agents):
        """Test factory creates capability router."""
        router = create_router("capability", agents)
        assert isinstance(router, CapabilityRouter)

    def test_create_load_balancing_router(self, agents):
        """Test factory creates load balancing router."""
        router = create_router("load_balancing", agents)
        assert isinstance(router, LoadBalancingRouter)

    def test_create_learned_router(self, agents):
        """Test factory creates learned router."""
        router = create_router("learned", agents)
        assert isinstance(router, LearnedRouter)

    def test_create_unknown_raises(self, agents):
        """Test factory raises for unknown strategy."""
        with pytest.raises(ValueError, match="Unknown routing strategy"):
            create_router("unknown", agents)
