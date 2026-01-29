# Description: Tests for the Collective MCP interface.
# Description: Validates orchestration of agents, routing, consensus, and decomposition.
"""Tests for the Collective MCP interface."""

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
from quantum_mcp.orchestration.collective import (
    Collective,
    CollectiveConfig,
    CollectiveResult,
    ExecutionMode,
)


class MockAgent(BaseAgent):
    """Mock agent for collective testing."""

    def __init__(self, config: AgentConfig, response_content: str = "Mock response"):
        super().__init__(config)
        self._response_content = response_content

    async def execute(self, prompt: str) -> AgentResponse:
        return AgentResponse(
            agent_id=self.agent_id,
            content=f"{self._response_content}: {prompt[:50]}",
            status=AgentStatus.SUCCESS,
            tokens_used=100,
            latency_ms=50.0,
        )

    async def stream(self, prompt: str):
        yield f"{self._response_content}: {prompt[:50]}"

    async def health_check(self) -> bool:
        return True


class TestCollectiveConfig:
    """Test CollectiveConfig model."""

    def test_default_config(self):
        """Test default configuration values."""
        config = CollectiveConfig()
        assert config.routing_strategy == "capability"
        assert config.consensus_method == "voting"
        assert config.decomposition_strategy == "simple"

    def test_custom_config(self):
        """Test custom configuration."""
        config = CollectiveConfig(
            routing_strategy="learned",
            consensus_method="debate",
            decomposition_strategy="recursive",
            max_agents_per_task=5,
        )
        assert config.routing_strategy == "learned"
        assert config.max_agents_per_task == 5


class TestCollectiveResult:
    """Test CollectiveResult model."""

    def test_result_creation(self):
        """Test creating a collective result."""
        result = CollectiveResult(
            task_id="task-123",
            final_content="Aggregated answer",
            success=True,
            agents_used=["agent-1", "agent-2"],
        )
        assert result.final_content == "Aggregated answer"
        assert result.success is True
        assert len(result.agents_used) == 2

    def test_result_with_metrics(self):
        """Test result includes execution metrics."""
        result = CollectiveResult(
            task_id="task-123",
            final_content="Answer",
            success=True,
            agents_used=["a1"],
            total_tokens=500,
            total_latency_ms=250.0,
        )
        assert result.total_tokens == 500
        assert result.total_latency_ms == 250.0


class TestCollective:
    """Test Collective orchestrator."""

    @pytest.fixture
    def agents(self) -> list[MockAgent]:
        """Create test agents."""
        return [
            MockAgent(
                AgentConfig(
                    name="code-agent",
                    provider="claude",
                    capabilities=[
                        AgentCapability(name="code", description="Code generation"),
                    ],
                ),
                response_content="Code agent",
            ),
            MockAgent(
                AgentConfig(
                    name="analysis-agent",
                    provider="openai",
                    capabilities=[
                        AgentCapability(name="analysis", description="Data analysis"),
                    ],
                ),
                response_content="Analysis agent",
            ),
        ]

    @pytest.fixture
    def collective(self, agents) -> Collective:
        """Create collective with test agents."""
        return Collective(agents=agents)

    @pytest.mark.asyncio
    async def test_execute_simple_task(self, collective):
        """Test executing a simple task."""
        task = Task(prompt="Write a hello world function")
        result = await collective.execute(task)

        assert result.success is True
        assert result.final_content is not None
        assert len(result.agents_used) >= 1

    @pytest.mark.asyncio
    async def test_execute_with_capabilities(self, collective):
        """Test task routes to agent with matching capabilities."""
        task = Task(
            prompt="Analyze the data",
            required_capabilities=["analysis"],
        )
        result = await collective.execute(task)

        assert result.success is True
        # Should prefer analysis agent
        assert any("analysis" in agent for agent in result.agents_used)

    @pytest.mark.asyncio
    async def test_execute_multi_agent(self, collective):
        """Test multi-agent execution."""
        task = Task(
            prompt="Complex task requiring multiple perspectives",
            min_agents=2,
            max_agents=2,
        )
        result = await collective.execute(task)

        assert result.success is True
        assert len(result.agents_used) == 2

    @pytest.mark.asyncio
    async def test_execute_with_decomposition(self):
        """Test task decomposition during execution."""
        agents = [
            MockAgent(AgentConfig(name="agent-1", provider="claude")),
        ]
        collective = Collective(
            agents=agents,
            config=CollectiveConfig(
                decomposition_strategy="simple",
                auto_decompose=True,
            ),
        )

        task = Task(
            prompt="First do step A. Then do step B. Finally do step C."
        )
        result = await collective.execute(task)

        assert result.success is True
        # Should have processed decomposed subtasks
        assert result.subtasks_completed is not None
        assert result.subtasks_completed >= 1

    @pytest.mark.asyncio
    async def test_execute_parallel_mode(self):
        """Test parallel execution mode."""
        agents = [
            MockAgent(AgentConfig(name="agent-1", provider="claude")),
            MockAgent(AgentConfig(name="agent-2", provider="openai")),
        ]
        collective = Collective(
            agents=agents,
            config=CollectiveConfig(execution_mode=ExecutionMode.PARALLEL),
        )

        task = Task(
            prompt="Task for parallel execution",
            min_agents=2,
            max_agents=2,
        )
        result = await collective.execute(task)

        assert result.success is True
        assert len(result.agents_used) == 2

    @pytest.mark.asyncio
    async def test_handles_agent_failure(self):
        """Test collective handles agent failures gracefully."""
        class FailingAgent(MockAgent):
            async def execute(self, prompt: str) -> AgentResponse:
                return AgentResponse(
                    agent_id=self.agent_id,
                    content="",
                    status=AgentStatus.ERROR,
                    error="Simulated failure",
                )

        agents = [
            FailingAgent(AgentConfig(name="failing", provider="test")),
            MockAgent(AgentConfig(name="working", provider="test")),
        ]
        collective = Collective(agents=agents)

        # Request both agents - one fails, one succeeds
        task = Task(prompt="Test task", min_agents=2, max_agents=2)
        result = await collective.execute(task)

        # Should still succeed with working agent
        assert result.success is True
        assert any("working" in agent for agent in result.agents_used)

    @pytest.mark.asyncio
    async def test_all_agents_fail(self):
        """Test collective reports failure when all agents fail."""
        class FailingAgent(MockAgent):
            async def execute(self, prompt: str) -> AgentResponse:
                return AgentResponse(
                    agent_id=self.agent_id,
                    content="",
                    status=AgentStatus.ERROR,
                    error="Simulated failure",
                )

        agents = [
            FailingAgent(AgentConfig(name="failing-1", provider="test")),
            FailingAgent(AgentConfig(name="failing-2", provider="test")),
        ]
        collective = Collective(agents=agents)

        task = Task(prompt="Test task")
        result = await collective.execute(task)

        assert result.success is False
        assert result.error is not None

    def test_add_agent(self, collective):
        """Test adding agent to collective."""
        new_agent = MockAgent(AgentConfig(name="new-agent", provider="local"))
        collective.add_agent(new_agent)

        assert len(collective.agents) == 3

    def test_remove_agent(self, collective, agents):
        """Test removing agent from collective."""
        agent_id = agents[0].agent_id
        collective.remove_agent(agent_id)

        assert len(collective.agents) == 1

    @pytest.mark.asyncio
    async def test_health_check(self, collective):
        """Test collective health check."""
        status = await collective.health_check()

        assert status.healthy is True
        assert status.agents_healthy >= 1


class TestExecutionMode:
    """Test ExecutionMode enum."""

    def test_sequential_mode(self):
        """Test sequential execution mode."""
        assert ExecutionMode.SEQUENTIAL.value == "sequential"

    def test_parallel_mode(self):
        """Test parallel execution mode."""
        assert ExecutionMode.PARALLEL.value == "parallel"

    def test_adaptive_mode(self):
        """Test adaptive execution mode."""
        assert ExecutionMode.ADAPTIVE.value == "adaptive"
