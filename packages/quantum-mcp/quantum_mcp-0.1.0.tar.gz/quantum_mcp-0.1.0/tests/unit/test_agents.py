# Description: Tests for concrete agent implementations.
# Description: Validates Claude, OpenAI, Local, and Tool agents.
"""Tests for concrete agent implementations."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from quantum_mcp.agents import (
    AgentCapability,
    AgentConfig,
    AgentResponse,
    AgentStatus,
)
from quantum_mcp.agents.claude import ClaudeAgent
from quantum_mcp.agents.openai import OpenAIAgent
from quantum_mcp.agents.local import LocalAgent
from quantum_mcp.agents.tool import ToolAgent


class TestClaudeAgent:
    """Test Claude agent implementation."""

    @pytest.fixture
    def claude_config(self) -> AgentConfig:
        """Create Claude agent config."""
        return AgentConfig(
            name="claude-agent",
            provider="claude",
            model="claude-3-5-sonnet-20241022",
            capabilities=[
                AgentCapability(name="reasoning", description="Complex reasoning"),
                AgentCapability(name="code", description="Code generation"),
            ],
        )

    def test_claude_agent_creation(self, claude_config):
        """Test creating Claude agent."""
        agent = ClaudeAgent(config=claude_config)
        assert agent.provider == "claude"
        assert agent.model == "claude-3-5-sonnet-20241022"

    def test_claude_agent_default_model(self):
        """Test Claude agent uses default model when not specified."""
        config = AgentConfig(name="claude", provider="claude")
        agent = ClaudeAgent(config=config)
        assert agent.model == "claude-3-5-sonnet-20241022"

    @pytest.mark.asyncio
    async def test_claude_execute_mocked(self, claude_config):
        """Test Claude agent execution with mocked API."""
        agent = ClaudeAgent(config=claude_config)

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Test response")]
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 5

        with patch.object(agent, "_client") as mock_client:
            mock_client.messages.create = AsyncMock(return_value=mock_response)

            response = await agent.execute("Test prompt")

            assert response.status == AgentStatus.SUCCESS
            assert response.content == "Test response"
            assert response.tokens_used == 15

    @pytest.mark.asyncio
    async def test_claude_health_check(self, claude_config):
        """Test Claude agent health check."""
        agent = ClaudeAgent(config=claude_config)
        # Health check should work even without real API
        result = await agent.health_check()
        assert isinstance(result, bool)


class TestOpenAIAgent:
    """Test OpenAI agent implementation."""

    @pytest.fixture
    def openai_config(self) -> AgentConfig:
        """Create OpenAI agent config."""
        return AgentConfig(
            name="openai-agent",
            provider="openai",
            model="gpt-4-turbo",
            capabilities=[
                AgentCapability(name="chat", description="Chat completion"),
            ],
        )

    def test_openai_agent_creation(self, openai_config):
        """Test creating OpenAI agent."""
        agent = OpenAIAgent(config=openai_config)
        assert agent.provider == "openai"
        assert agent.model == "gpt-4-turbo"

    def test_openai_agent_default_model(self):
        """Test OpenAI agent uses default model when not specified."""
        config = AgentConfig(name="openai", provider="openai")
        agent = OpenAIAgent(config=config)
        assert agent.model == "gpt-4-turbo"

    @pytest.mark.asyncio
    async def test_openai_execute_mocked(self, openai_config):
        """Test OpenAI agent execution with mocked API."""
        agent = OpenAIAgent(config=openai_config)

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Test response"))]
        mock_response.usage.total_tokens = 20

        with patch.object(agent, "_client") as mock_client:
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

            response = await agent.execute("Test prompt")

            assert response.status == AgentStatus.SUCCESS
            assert response.content == "Test response"
            assert response.tokens_used == 20

    @pytest.mark.asyncio
    async def test_openai_health_check(self, openai_config):
        """Test OpenAI agent health check."""
        agent = OpenAIAgent(config=openai_config)
        result = await agent.health_check()
        assert isinstance(result, bool)


class TestLocalAgent:
    """Test Local/Ollama agent implementation."""

    @pytest.fixture
    def local_config(self) -> AgentConfig:
        """Create Local agent config."""
        return AgentConfig(
            name="local-agent",
            provider="local",
            model="llama3.2",
            capabilities=[
                AgentCapability(name="general", description="General tasks"),
            ],
            metadata={"base_url": "http://localhost:11434"},
        )

    def test_local_agent_creation(self, local_config):
        """Test creating Local agent."""
        agent = LocalAgent(config=local_config)
        assert agent.provider == "local"
        assert agent.model == "llama3.2"

    def test_local_agent_default_model(self):
        """Test Local agent uses default model when not specified."""
        config = AgentConfig(name="local", provider="local")
        agent = LocalAgent(config=config)
        assert agent.model == "llama3.2"

    def test_local_agent_base_url(self, local_config):
        """Test Local agent uses configured base URL."""
        agent = LocalAgent(config=local_config)
        assert agent.base_url == "http://localhost:11434"

    @pytest.mark.asyncio
    async def test_local_execute_mocked(self, local_config):
        """Test Local agent execution with mocked API."""
        agent = LocalAgent(config=local_config)

        mock_response = {"message": {"content": "Test response"}}

        with patch.object(agent, "_make_request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = mock_response

            response = await agent.execute("Test prompt")

            assert response.status == AgentStatus.SUCCESS
            assert response.content == "Test response"

    @pytest.mark.asyncio
    async def test_local_health_check_mocked(self, local_config):
        """Test Local agent health check with mocked endpoint."""
        agent = LocalAgent(config=local_config)

        with patch.object(agent, "_check_server", new_callable=AsyncMock) as mock_check:
            mock_check.return_value = True
            result = await agent.health_check()
            assert result is True


class TestToolAgent:
    """Test Tool agent wrapper implementation."""

    @pytest.fixture
    def tool_config(self) -> AgentConfig:
        """Create Tool agent config."""
        return AgentConfig(
            name="tool-agent",
            provider="tool",
            capabilities=[
                AgentCapability(name="quantum_vqe", description="Run VQE algorithm"),
            ],
            metadata={"tool_name": "quantum_vqe"},
        )

    def test_tool_agent_creation(self, tool_config):
        """Test creating Tool agent."""
        mock_server = MagicMock()
        agent = ToolAgent(config=tool_config, server=mock_server)
        assert agent.provider == "tool"
        assert agent.tool_name == "quantum_vqe"

    @pytest.mark.asyncio
    async def test_tool_execute(self, tool_config):
        """Test Tool agent execution."""
        mock_server = MagicMock()
        mock_server.call_tool = AsyncMock(return_value='{"energy": -1.137}')

        agent = ToolAgent(config=tool_config, server=mock_server)
        response = await agent.execute('{"num_qubits": 2}')

        assert response.status == AgentStatus.SUCCESS
        assert "energy" in response.content.lower() or "-1.137" in response.content

    @pytest.mark.asyncio
    async def test_tool_health_check(self, tool_config):
        """Test Tool agent health check."""
        mock_tool = MagicMock()
        mock_tool.name = "quantum_vqe"

        mock_server = MagicMock()
        mock_server.list_tools.return_value = [mock_tool]

        agent = ToolAgent(config=tool_config, server=mock_server)
        result = await agent.health_check()
        assert result is True

    @pytest.mark.asyncio
    async def test_tool_health_check_missing_tool(self, tool_config):
        """Test Tool agent health check when tool not available."""
        mock_server = MagicMock()
        mock_server.list_tools.return_value = []

        agent = ToolAgent(config=tool_config, server=mock_server)
        result = await agent.health_check()
        assert result is False


class TestAgentFactory:
    """Test agent factory function."""

    def test_create_claude_agent(self):
        """Test factory creates Claude agent."""
        from quantum_mcp.agents.factory import create_agent

        config = AgentConfig(name="test", provider="claude")
        agent = create_agent(config)
        assert isinstance(agent, ClaudeAgent)

    def test_create_openai_agent(self):
        """Test factory creates OpenAI agent."""
        from quantum_mcp.agents.factory import create_agent

        config = AgentConfig(name="test", provider="openai")
        agent = create_agent(config)
        assert isinstance(agent, OpenAIAgent)

    def test_create_local_agent(self):
        """Test factory creates Local agent."""
        from quantum_mcp.agents.factory import create_agent

        config = AgentConfig(name="test", provider="local")
        agent = create_agent(config)
        assert isinstance(agent, LocalAgent)

    def test_create_unknown_provider_raises(self):
        """Test factory raises for unknown provider."""
        from quantum_mcp.agents.factory import create_agent

        config = AgentConfig(name="test", provider="unknown")
        with pytest.raises(ValueError, match="Unknown provider"):
            create_agent(config)
