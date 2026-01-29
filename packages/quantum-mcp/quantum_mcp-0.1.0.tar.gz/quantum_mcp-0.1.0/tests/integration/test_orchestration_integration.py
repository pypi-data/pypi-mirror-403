# Description: Integration tests for the multi-agent orchestration layer.
# Description: Validates end-to-end flow from agents through routing to consensus.
"""Integration tests for the multi-agent orchestration layer."""

import pytest

from quantum_mcp.agents import (
    AgentCapability,
    AgentConfig,
    AgentResponse,
    AgentStatus,
    BaseAgent,
)
from quantum_mcp.orchestration import (
    BenchmarkConfig,
    BenchmarkSuite,
    Collective,
    CollectiveConfig,
    ExecutionMode,
    MetricsCollector,
    Task,
    TaskPriority,
    Tracer,
    create_consensus,
    create_decomposer,
    create_router,
)


class IntegrationTestAgent(BaseAgent):
    """Test agent for integration testing."""

    def __init__(
        self,
        config: AgentConfig,
        response_prefix: str = "Response",
        latency_ms: float = 10.0,
    ):
        super().__init__(config)
        self._response_prefix = response_prefix
        self._latency_ms = latency_ms

    async def execute(self, prompt: str) -> AgentResponse:
        return AgentResponse(
            agent_id=self.agent_id,
            content=f"{self._response_prefix} from {self.name}: {prompt[:100]}",
            status=AgentStatus.SUCCESS,
            tokens_used=len(prompt.split()) * 2,
            latency_ms=self._latency_ms,
        )

    async def stream(self, prompt: str):
        yield f"{self._response_prefix} from {self.name}: {prompt[:100]}"

    async def health_check(self) -> bool:
        return True


@pytest.fixture
def code_agent() -> IntegrationTestAgent:
    """Create a code-specialized agent."""
    return IntegrationTestAgent(
        AgentConfig(
            name="code-specialist",
            provider="claude",
            capabilities=[
                AgentCapability(name="code", description="Code generation"),
                AgentCapability(name="python", description="Python expertise"),
            ],
        ),
        response_prefix="Code solution",
    )


@pytest.fixture
def analysis_agent() -> IntegrationTestAgent:
    """Create an analysis-specialized agent."""
    return IntegrationTestAgent(
        AgentConfig(
            name="analysis-specialist",
            provider="openai",
            capabilities=[
                AgentCapability(name="analysis", description="Data analysis"),
                AgentCapability(name="reasoning", description="Complex reasoning"),
            ],
        ),
        response_prefix="Analysis result",
    )


@pytest.fixture
def general_agent() -> IntegrationTestAgent:
    """Create a general-purpose agent."""
    return IntegrationTestAgent(
        AgentConfig(
            name="generalist",
            provider="local",
            capabilities=[
                AgentCapability(name="general", description="General tasks"),
            ],
        ),
        response_prefix="General response",
    )


@pytest.fixture
def all_agents(code_agent, analysis_agent, general_agent) -> list[IntegrationTestAgent]:
    """All test agents."""
    return [code_agent, analysis_agent, general_agent]


class TestAgentToRouterIntegration:
    """Test agents integrate correctly with routers."""

    @pytest.mark.asyncio
    async def test_capability_router_selects_matching_agent(self, all_agents):
        """Test capability router selects agent with matching capabilities."""
        router = create_router("capability", all_agents)

        task = Task(
            prompt="Write a Python function to sort a list",
            required_capabilities=["code", "python"],
        )

        decision = await router.route(task)

        assert "code-specialist" in decision.selected_agents[0]
        assert decision.strategy == "capability"

    @pytest.mark.asyncio
    async def test_load_balancing_router_distributes(self, all_agents):
        """Test load balancing router distributes across agents."""
        router = create_router("load_balancing", all_agents)

        selected_agents = set()
        for i in range(10):
            task = Task(prompt=f"Task {i}")
            decision = await router.route(task)
            selected_agents.add(decision.selected_agents[0])

        # Should have distributed to multiple agents
        assert len(selected_agents) >= 2

    @pytest.mark.asyncio
    async def test_learned_router_tracks_performance(self, all_agents):
        """Test learned router tracks and uses performance data."""
        router = create_router("learned", all_agents)

        # Record some outcomes
        router.record_outcome(
            agent_id=all_agents[0].agent_id,
            task_domain="code",
            success=True,
            latency_ms=50.0,
        )

        stats = router.get_agent_stats(all_agents[0].agent_id)
        assert stats["total_tasks"] == 1
        assert stats["success_rate"] == 1.0


class TestRouterToConsensusIntegration:
    """Test router decisions flow correctly to consensus."""

    @pytest.mark.asyncio
    async def test_multi_agent_routing_to_voting_consensus(self, all_agents):
        """Test multi-agent routing results feed into voting consensus."""
        router = create_router("capability", all_agents)
        consensus = create_consensus("voting")

        task = Task(
            prompt="Analyze and explain the data",
            min_agents=2,
            max_agents=3,
        )

        # Route to multiple agents
        decision = await router.route(task)
        assert len(decision.selected_agents) >= 2

        # Execute on selected agents
        responses = []
        for agent in all_agents:
            if agent.agent_id in decision.selected_agents:
                response = await agent.execute(task.prompt)
                responses.append(response)

        # Apply consensus
        result = await consensus.aggregate(responses)
        assert result.final_content is not None
        assert result.method == "voting"


class TestCollectiveEndToEnd:
    """Test complete Collective orchestration flow."""

    @pytest.mark.asyncio
    async def test_simple_task_execution(self, all_agents):
        """Test executing a simple task through the collective."""
        collective = Collective(agents=all_agents)

        task = Task(prompt="What is 2 + 2?")
        result = await collective.execute(task)

        assert result.success is True
        assert result.final_content is not None
        assert len(result.agents_used) >= 1

    @pytest.mark.asyncio
    async def test_capability_based_routing(self, all_agents):
        """Test collective routes to correct agent based on capabilities."""
        collective = Collective(
            agents=all_agents,
            config=CollectiveConfig(routing_strategy="capability"),
        )

        task = Task(
            prompt="Write Python code to calculate factorial",
            required_capabilities=["code", "python"],
        )
        result = await collective.execute(task)

        assert result.success is True
        # Should have used the code specialist
        assert any("code-specialist" in agent for agent in result.agents_used)

    @pytest.mark.asyncio
    async def test_multi_agent_with_consensus(self, all_agents):
        """Test multi-agent execution with consensus aggregation."""
        collective = Collective(
            agents=all_agents,
            config=CollectiveConfig(
                routing_strategy="capability",
                consensus_method="weighted_merge",
            ),
        )

        task = Task(
            prompt="Provide different perspectives on this problem",
            min_agents=2,
            max_agents=3,
        )
        result = await collective.execute(task)

        assert result.success is True
        assert len(result.agents_used) >= 2
        assert result.consensus_method == "weighted_merge"

    @pytest.mark.asyncio
    async def test_parallel_execution_mode(self, all_agents):
        """Test parallel execution mode."""
        collective = Collective(
            agents=all_agents,
            config=CollectiveConfig(
                execution_mode=ExecutionMode.PARALLEL,
            ),
        )

        task = Task(
            prompt="Execute this in parallel",
            min_agents=3,
            max_agents=3,
        )
        result = await collective.execute(task)

        assert result.success is True
        assert len(result.agents_used) == 3

    @pytest.mark.asyncio
    async def test_auto_decomposition(self, all_agents):
        """Test automatic task decomposition."""
        collective = Collective(
            agents=all_agents,
            config=CollectiveConfig(
                auto_decompose=True,
                decomposition_strategy="simple",
            ),
        )

        task = Task(
            prompt="First analyze the data. Then visualize the results. Finally write a report."
        )
        result = await collective.execute(task)

        assert result.success is True
        # Should have decomposed into subtasks
        assert result.subtasks_completed is not None
        assert result.subtasks_completed >= 1


class TestDecompositionIntegration:
    """Test task decomposition integrates with execution."""

    @pytest.mark.asyncio
    async def test_simple_decomposition_flow(self, all_agents):
        """Test simple decomposition creates executable subtasks."""
        decomposer = create_decomposer("simple")

        task = Task(
            prompt="Step one. Step two. Step three.",
            required_capabilities=["general"],
        )

        result = await decomposer.decompose(task)

        assert len(result.subtasks) == 3
        assert result.subtasks[0].order == 1
        assert result.subtasks[2].order == 3

    @pytest.mark.asyncio
    async def test_domain_decomposition_with_capabilities(self, all_agents):
        """Test domain decomposition preserves capabilities."""
        decomposer = create_decomposer("domain")

        task = Task(
            prompt="Write a function and add unit tests",
            required_capabilities=["code", "python"],
        )

        result = await decomposer.decompose(task)

        # Subtasks should inherit capabilities
        for subtask in result.subtasks:
            assert "code" in subtask.required_capabilities


class TestObservabilityIntegration:
    """Test observability integrates with orchestration."""

    @pytest.mark.asyncio
    async def test_tracing_spans_task_execution(self, all_agents):
        """Test tracer creates spans for operations."""
        tracer = Tracer(service_name="test-collective")
        collective = Collective(agents=all_agents)

        with tracer.span("collective_execute") as span:
            span.set_attribute("task.type", "test")
            task = Task(prompt="Test task for tracing")
            result = await collective.execute(task)
            span.set_attribute("result.success", result.success)

        assert span.duration_ms is not None
        assert span.attributes["result.success"] is True

    def test_metrics_collector_tracks_operations(self):
        """Test metrics collector tracks orchestration metrics."""
        metrics = MetricsCollector()

        # Simulate tracking operations
        metrics.counter("tasks.executed", 1, labels={"status": "success"})
        metrics.counter("tasks.executed", 1, labels={"status": "success"})
        metrics.counter("tasks.executed", 1, labels={"status": "error"})
        metrics.histogram("task.latency_ms", 150.0)
        metrics.histogram("task.latency_ms", 200.0)
        metrics.gauge("agents.active", 3)

        assert metrics.get_counter("tasks.executed", labels={"status": "success"}) == 2
        assert metrics.get_gauge("agents.active") == 3

        stats = metrics.get_histogram_stats("task.latency_ms")
        assert stats["count"] == 2
        assert stats["avg"] == 175.0


class TestBenchmarkIntegration:
    """Test benchmarking integrates with orchestration."""

    @pytest.mark.asyncio
    async def test_benchmark_suite_runs_collective(self, all_agents):
        """Test benchmark suite exercises the collective."""
        suite = BenchmarkSuite(
            name="integration_test",
            agents=all_agents,
            config=BenchmarkConfig(iterations=3, warmup_iterations=1),
        )

        tasks = [
            Task(prompt="Benchmark task 1"),
            Task(prompt="Benchmark task 2"),
        ]

        results = await suite.run(tasks)

        assert len(results) == 2
        for result in results:
            assert result.success_rate > 0
            assert result.latency_metrics.count == 3

    @pytest.mark.asyncio
    async def test_benchmark_generates_report(self, all_agents):
        """Test benchmark generates readable report."""
        suite = BenchmarkSuite(
            name="report_test",
            agents=all_agents,
            config=BenchmarkConfig(iterations=2, warmup_iterations=0),
        )

        tasks = [Task(prompt="Report test task")]
        results = await suite.run(tasks)
        report = suite.generate_report(results)

        assert "report_test" in report
        assert "Success Rate" in report
        assert "Latency" in report


class TestHealthCheckIntegration:
    """Test health check across components."""

    @pytest.mark.asyncio
    async def test_collective_health_check(self, all_agents):
        """Test collective reports agent health."""
        collective = Collective(agents=all_agents)

        status = await collective.health_check()

        assert status.healthy is True
        assert status.agents_total == 3
        assert status.agents_healthy == 3
        assert len(status.agents_unhealthy) == 0

    @pytest.mark.asyncio
    async def test_collective_with_unhealthy_agent(self, all_agents):
        """Test collective detects unhealthy agents."""
        # Create an agent that fails health check
        class UnhealthyAgent(IntegrationTestAgent):
            async def health_check(self) -> bool:
                return False

        unhealthy = UnhealthyAgent(
            AgentConfig(name="unhealthy", provider="test")
        )

        collective = Collective(agents=all_agents + [unhealthy])
        status = await collective.health_check()

        assert status.agents_total == 4
        assert status.agents_healthy == 3
        assert len(status.agents_unhealthy) == 1
