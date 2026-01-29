# Description: Tests for agent protocol and base classes.
# Description: Validates agent abstraction layer for multi-agent system.
"""Tests for agent protocol and base classes."""

import pytest
from typing import AsyncIterator

from quantum_mcp.agents.protocol import (
    AgentProtocol,
    AgentCapability,
    AgentConfig,
    AgentResponse,
    AgentStatus,
)
from quantum_mcp.agents.base import BaseAgent


class TestAgentCapability:
    """Test AgentCapability model."""

    def test_capability_creation(self):
        """Test creating a capability."""
        cap = AgentCapability(
            name="code_generation",
            description="Generate code from specifications",
            domains=["python", "javascript"],
        )
        assert cap.name == "code_generation"
        assert "python" in cap.domains

    def test_capability_with_confidence(self):
        """Test capability with confidence score."""
        cap = AgentCapability(
            name="reasoning",
            description="Complex reasoning tasks",
            confidence=0.95,
        )
        assert cap.confidence == 0.95

    def test_capability_defaults(self):
        """Test capability default values."""
        cap = AgentCapability(
            name="general",
            description="General purpose",
        )
        assert cap.domains == []
        assert cap.confidence == 1.0


class TestAgentConfig:
    """Test AgentConfig model."""

    def test_config_creation(self):
        """Test creating agent config."""
        config = AgentConfig(
            name="test-agent",
            provider="claude",
            model="claude-3-opus",
        )
        assert config.name == "test-agent"
        assert config.provider == "claude"

    def test_config_with_capabilities(self):
        """Test config with capabilities."""
        cap = AgentCapability(name="code", description="Code tasks")
        config = AgentConfig(
            name="coder",
            provider="openai",
            model="gpt-4",
            capabilities=[cap],
        )
        assert len(config.capabilities) == 1

    def test_config_defaults(self):
        """Test config default values."""
        config = AgentConfig(
            name="default-agent",
            provider="local",
        )
        assert config.model is None
        assert config.capabilities == []
        assert config.max_tokens == 4096
        assert config.temperature == 0.7


class TestAgentResponse:
    """Test AgentResponse model."""

    def test_response_creation(self):
        """Test creating a response."""
        response = AgentResponse(
            agent_id="agent-1",
            content="Hello, world!",
            status=AgentStatus.SUCCESS,
        )
        assert response.content == "Hello, world!"
        assert response.status == AgentStatus.SUCCESS

    def test_response_with_metadata(self):
        """Test response with metadata."""
        response = AgentResponse(
            agent_id="agent-1",
            content="Result",
            status=AgentStatus.SUCCESS,
            tokens_used=150,
            latency_ms=1200.5,
            metadata={"model": "gpt-4"},
        )
        assert response.tokens_used == 150
        assert response.latency_ms == 1200.5
        assert response.metadata["model"] == "gpt-4"

    def test_response_error_status(self):
        """Test response with error status."""
        response = AgentResponse(
            agent_id="agent-1",
            content="",
            status=AgentStatus.ERROR,
            error="Connection timeout",
        )
        assert response.status == AgentStatus.ERROR
        assert response.error == "Connection timeout"


class TestAgentStatus:
    """Test AgentStatus enum."""

    def test_status_values(self):
        """Test all status values exist."""
        assert AgentStatus.PENDING
        assert AgentStatus.RUNNING
        assert AgentStatus.SUCCESS
        assert AgentStatus.ERROR
        assert AgentStatus.TIMEOUT


class MockAgent(BaseAgent):
    """Mock agent for testing base class."""

    async def execute(self, prompt: str) -> AgentResponse:
        """Execute prompt and return response."""
        return AgentResponse(
            agent_id=self.agent_id,
            content=f"Mock response to: {prompt}",
            status=AgentStatus.SUCCESS,
        )

    async def stream(self, prompt: str) -> AsyncIterator[str]:
        """Stream response tokens."""
        for word in f"Mock response to: {prompt}".split():
            yield word + " "

    async def health_check(self) -> bool:
        """Check agent health."""
        return True


class TestBaseAgent:
    """Test BaseAgent class."""

    @pytest.fixture
    def agent_config(self) -> AgentConfig:
        """Create test config."""
        return AgentConfig(
            name="mock-agent",
            provider="mock",
            model="mock-v1",
            capabilities=[
                AgentCapability(name="testing", description="Test capability"),
            ],
        )

    def test_agent_creation(self, agent_config):
        """Test creating an agent."""
        agent = MockAgent(config=agent_config)
        assert agent.name == "mock-agent"
        assert agent.provider == "mock"
        assert len(agent.agent_id) > 0

    def test_agent_has_capability(self, agent_config):
        """Test capability checking."""
        agent = MockAgent(config=agent_config)
        assert agent.has_capability("testing") is True
        assert agent.has_capability("unknown") is False

    def test_agent_get_capabilities(self, agent_config):
        """Test getting capabilities."""
        agent = MockAgent(config=agent_config)
        caps = agent.get_capabilities()
        assert len(caps) == 1
        assert caps[0].name == "testing"

    @pytest.mark.asyncio
    async def test_agent_execute(self, agent_config):
        """Test agent execution."""
        agent = MockAgent(config=agent_config)
        response = await agent.execute("Test prompt")
        assert response.status == AgentStatus.SUCCESS
        assert "Test prompt" in response.content

    @pytest.mark.asyncio
    async def test_agent_stream(self, agent_config):
        """Test agent streaming."""
        agent = MockAgent(config=agent_config)
        chunks = []
        async for chunk in agent.stream("Test prompt"):
            chunks.append(chunk)
        assert len(chunks) > 0
        assert "Mock" in "".join(chunks)

    @pytest.mark.asyncio
    async def test_agent_health_check(self, agent_config):
        """Test agent health check."""
        agent = MockAgent(config=agent_config)
        is_healthy = await agent.health_check()
        assert is_healthy is True

    def test_agent_unique_ids(self, agent_config):
        """Test agents have unique IDs."""
        agent1 = MockAgent(config=agent_config)
        agent2 = MockAgent(config=agent_config)
        assert agent1.agent_id != agent2.agent_id


class TestAgentProtocol:
    """Test AgentProtocol interface."""

    def test_protocol_implementation(self, ):
        """Test that MockAgent implements AgentProtocol."""
        config = AgentConfig(name="test", provider="mock")
        agent = MockAgent(config=config)
        # Should not raise - agent implements protocol
        assert isinstance(agent, AgentProtocol)
