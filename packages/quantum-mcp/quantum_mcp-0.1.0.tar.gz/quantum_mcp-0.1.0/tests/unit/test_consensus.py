# Description: Tests for consensus mechanisms.
# Description: Validates voting, merge, and debate consensus strategies.
"""Tests for consensus mechanisms."""

import pytest

from quantum_mcp.agents import AgentResponse, AgentStatus
from quantum_mcp.orchestration.consensus import (
    Consensus,
    VotingConsensus,
    WeightedMergeConsensus,
    DebateConsensus,
    ConsensusResult,
    create_consensus,
)


class TestConsensusResult:
    """Test ConsensusResult model."""

    def test_result_creation(self):
        """Test creating a consensus result."""
        result = ConsensusResult(
            final_content="Agreed upon answer",
            method="voting",
            confidence=0.85,
            participating_agents=["agent-1", "agent-2"],
        )
        assert result.final_content == "Agreed upon answer"
        assert result.method == "voting"
        assert result.confidence == 0.85

    def test_result_with_votes(self):
        """Test result with vote breakdown."""
        result = ConsensusResult(
            final_content="Option A",
            method="voting",
            votes={"Option A": 2, "Option B": 1},
            participating_agents=["a1", "a2", "a3"],
        )
        assert result.votes["Option A"] == 2


class TestVotingConsensus:
    """Test voting-based consensus."""

    @pytest.fixture
    def consensus(self) -> VotingConsensus:
        """Create voting consensus."""
        return VotingConsensus()

    @pytest.fixture
    def agreeing_responses(self) -> list[AgentResponse]:
        """Create responses that mostly agree."""
        return [
            AgentResponse(
                agent_id="agent-1",
                content="The answer is 42",
                status=AgentStatus.SUCCESS,
            ),
            AgentResponse(
                agent_id="agent-2",
                content="The answer is 42",
                status=AgentStatus.SUCCESS,
            ),
            AgentResponse(
                agent_id="agent-3",
                content="The answer is 43",
                status=AgentStatus.SUCCESS,
            ),
        ]

    @pytest.fixture
    def disagreeing_responses(self) -> list[AgentResponse]:
        """Create responses that all disagree."""
        return [
            AgentResponse(
                agent_id="agent-1",
                content="Answer A",
                status=AgentStatus.SUCCESS,
            ),
            AgentResponse(
                agent_id="agent-2",
                content="Answer B",
                status=AgentStatus.SUCCESS,
            ),
            AgentResponse(
                agent_id="agent-3",
                content="Answer C",
                status=AgentStatus.SUCCESS,
            ),
        ]

    @pytest.mark.asyncio
    async def test_majority_wins(self, consensus, agreeing_responses):
        """Test majority vote wins."""
        result = await consensus.aggregate(agreeing_responses)

        assert result.final_content == "The answer is 42"
        assert result.confidence >= 0.66

    @pytest.mark.asyncio
    async def test_no_majority_selects_first(self, consensus, disagreeing_responses):
        """Test no majority falls back to first response."""
        result = await consensus.aggregate(disagreeing_responses)

        # Should still produce a result
        assert result.final_content is not None
        assert result.confidence < 0.5

    @pytest.mark.asyncio
    async def test_single_response(self, consensus):
        """Test consensus with single response."""
        responses = [
            AgentResponse(
                agent_id="agent-1",
                content="Only answer",
                status=AgentStatus.SUCCESS,
            ),
        ]
        result = await consensus.aggregate(responses)

        assert result.final_content == "Only answer"
        assert result.confidence == 1.0

    @pytest.mark.asyncio
    async def test_empty_responses(self, consensus):
        """Test consensus with no responses."""
        result = await consensus.aggregate([])

        assert result.final_content == ""
        assert result.confidence == 0.0

    @pytest.mark.asyncio
    async def test_filters_failed_responses(self, consensus):
        """Test that failed responses are filtered out."""
        responses = [
            AgentResponse(
                agent_id="agent-1",
                content="Good answer",
                status=AgentStatus.SUCCESS,
            ),
            AgentResponse(
                agent_id="agent-2",
                content="",
                status=AgentStatus.ERROR,
                error="Failed",
            ),
        ]
        result = await consensus.aggregate(responses)

        assert result.final_content == "Good answer"
        assert len(result.participating_agents) == 1


class TestWeightedMergeConsensus:
    """Test weighted merge consensus."""

    @pytest.fixture
    def consensus(self) -> WeightedMergeConsensus:
        """Create weighted merge consensus."""
        return WeightedMergeConsensus()

    @pytest.fixture
    def diverse_responses(self) -> list[AgentResponse]:
        """Create diverse responses for merging."""
        return [
            AgentResponse(
                agent_id="agent-1",
                content="Point A is important. The key insight is X.",
                status=AgentStatus.SUCCESS,
                tokens_used=50,
            ),
            AgentResponse(
                agent_id="agent-2",
                content="Point B matters. We should consider Y.",
                status=AgentStatus.SUCCESS,
                tokens_used=100,
            ),
            AgentResponse(
                agent_id="agent-3",
                content="Point C is crucial. Z is the answer.",
                status=AgentStatus.SUCCESS,
                tokens_used=75,
            ),
        ]

    @pytest.mark.asyncio
    async def test_merge_combines_content(self, consensus, diverse_responses):
        """Test merge combines all responses."""
        result = await consensus.aggregate(diverse_responses)

        # Should contain content from all responses
        assert "Point A" in result.final_content or "agent-1" in result.final_content
        assert result.method == "weighted_merge"

    @pytest.mark.asyncio
    async def test_merge_weights_by_tokens(self, consensus, diverse_responses):
        """Test merge weights by token count."""
        result = await consensus.aggregate(diverse_responses)

        # Higher token responses should be weighted more
        assert result.weights is not None
        assert result.weights.get("agent-2", 0) >= result.weights.get("agent-1", 0)

    @pytest.mark.asyncio
    async def test_single_response_passthrough(self, consensus):
        """Test single response passes through unchanged."""
        responses = [
            AgentResponse(
                agent_id="agent-1",
                content="Only content",
                status=AgentStatus.SUCCESS,
            ),
        ]
        result = await consensus.aggregate(responses)

        assert result.final_content == "Only content"


class TestDebateConsensus:
    """Test debate-based consensus."""

    @pytest.fixture
    def consensus(self) -> DebateConsensus:
        """Create debate consensus."""
        return DebateConsensus(max_rounds=2)

    @pytest.fixture
    def opposing_responses(self) -> list[AgentResponse]:
        """Create opposing viewpoints."""
        return [
            AgentResponse(
                agent_id="agent-1",
                content="Position A: The solution should use approach X because of efficiency.",
                status=AgentStatus.SUCCESS,
            ),
            AgentResponse(
                agent_id="agent-2",
                content="Position B: The solution should use approach Y because of simplicity.",
                status=AgentStatus.SUCCESS,
            ),
        ]

    @pytest.mark.asyncio
    async def test_debate_produces_synthesis(self, consensus, opposing_responses):
        """Test debate produces synthesized result."""
        result = await consensus.aggregate(opposing_responses)

        assert result.final_content is not None
        assert result.method == "debate"
        assert result.rounds is not None

    @pytest.mark.asyncio
    async def test_debate_records_rounds(self, consensus, opposing_responses):
        """Test debate records discussion rounds."""
        result = await consensus.aggregate(opposing_responses)

        # Should have round information
        assert result.rounds >= 1

    @pytest.mark.asyncio
    async def test_single_position_no_debate(self, consensus):
        """Test single response needs no debate."""
        responses = [
            AgentResponse(
                agent_id="agent-1",
                content="Uncontested position",
                status=AgentStatus.SUCCESS,
            ),
        ]
        result = await consensus.aggregate(responses)

        assert result.final_content == "Uncontested position"
        assert result.rounds == 0


class TestConsensusFactory:
    """Test consensus factory function."""

    def test_create_voting_consensus(self):
        """Test factory creates voting consensus."""
        consensus = create_consensus("voting")
        assert isinstance(consensus, VotingConsensus)

    def test_create_weighted_merge_consensus(self):
        """Test factory creates weighted merge consensus."""
        consensus = create_consensus("weighted_merge")
        assert isinstance(consensus, WeightedMergeConsensus)

    def test_create_debate_consensus(self):
        """Test factory creates debate consensus."""
        consensus = create_consensus("debate")
        assert isinstance(consensus, DebateConsensus)

    def test_create_unknown_raises(self):
        """Test factory raises for unknown method."""
        with pytest.raises(ValueError, match="Unknown consensus method"):
            create_consensus("unknown")
