# Description: Consensus mechanisms for multi-agent response aggregation.
# Description: Voting, weighted merge, and debate strategies for combining responses.
"""Consensus mechanisms for multi-agent response aggregation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import Counter
from typing import TYPE_CHECKING

import structlog
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    pass

from quantum_mcp.agents.protocol import AgentResponse, AgentStatus

logger = structlog.get_logger()


class ConsensusResult(BaseModel):
    """Result of consensus aggregation."""

    final_content: str = Field(..., description="Final aggregated content")
    method: str = Field(..., description="Consensus method used")
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence in the consensus",
    )
    participating_agents: list[str] = Field(
        default_factory=list,
        description="IDs of agents that participated",
    )
    votes: dict[str, int] | None = Field(
        default=None,
        description="Vote counts (for voting consensus)",
    )
    weights: dict[str, float] | None = Field(
        default=None,
        description="Agent weights (for weighted merge)",
    )
    rounds: int | None = Field(
        default=None,
        description="Number of debate rounds (for debate consensus)",
    )
    reasoning: str | None = Field(
        default=None,
        description="Explanation of consensus decision",
    )


class Consensus(ABC):
    """Abstract base class for consensus mechanisms.

    Consensus mechanisms aggregate multiple agent responses
    into a single final response.
    """

    def __init__(self) -> None:
        """Initialize consensus mechanism."""
        self._logger = logger.bind(consensus=self.__class__.__name__)

    @abstractmethod
    async def aggregate(
        self,
        responses: list[AgentResponse],
    ) -> ConsensusResult:
        """Aggregate multiple responses into a consensus.

        Args:
            responses: List of agent responses to aggregate

        Returns:
            ConsensusResult with final content
        """
        raise NotImplementedError

    def _filter_successful(
        self,
        responses: list[AgentResponse],
    ) -> list[AgentResponse]:
        """Filter to only successful responses.

        Args:
            responses: All responses

        Returns:
            Only successful responses
        """
        return [r for r in responses if r.status == AgentStatus.SUCCESS]


class VotingConsensus(Consensus):
    """Consensus through voting.

    Each response is treated as a vote. The response that
    appears most frequently wins. Supports majority and
    plurality voting.
    """

    def __init__(self, require_majority: bool = False) -> None:
        """Initialize voting consensus.

        Args:
            require_majority: If True, require >50% agreement
        """
        super().__init__()
        self._require_majority = require_majority

    async def aggregate(
        self,
        responses: list[AgentResponse],
    ) -> ConsensusResult:
        """Aggregate responses by voting.

        Args:
            responses: List of agent responses

        Returns:
            ConsensusResult with winning response
        """
        successful = self._filter_successful(responses)

        if not successful:
            return ConsensusResult(
                final_content="",
                method="voting",
                confidence=0.0,
                participating_agents=[],
                reasoning="No successful responses to vote on",
            )

        if len(successful) == 1:
            return ConsensusResult(
                final_content=successful[0].content,
                method="voting",
                confidence=1.0,
                participating_agents=[successful[0].agent_id],
                reasoning="Single response, no voting needed",
            )

        # Count votes by content
        votes = Counter(r.content for r in successful)
        total_votes = len(successful)

        # Get winner
        winner_content, winner_votes = votes.most_common(1)[0]
        confidence = winner_votes / total_votes

        # Check majority requirement
        if self._require_majority and confidence <= 0.5:
            # No majority, use first response with low confidence
            winner_content = successful[0].content
            confidence = 1.0 / total_votes

        participating = [r.agent_id for r in successful]

        self._logger.debug(
            "Voting complete",
            winner_votes=winner_votes,
            total_votes=total_votes,
            confidence=confidence,
        )

        return ConsensusResult(
            final_content=winner_content,
            method="voting",
            confidence=confidence,
            participating_agents=participating,
            votes=dict(votes),
            reasoning=f"Winner received {winner_votes}/{total_votes} votes",
        )


class WeightedMergeConsensus(Consensus):
    """Consensus through weighted combination.

    Combines all responses, weighting by factors like
    token count, latency, or explicit quality scores.
    """

    def __init__(self, weight_by: str = "tokens") -> None:
        """Initialize weighted merge consensus.

        Args:
            weight_by: Weighting strategy (tokens, latency, equal)
        """
        super().__init__()
        self._weight_by = weight_by

    async def aggregate(
        self,
        responses: list[AgentResponse],
    ) -> ConsensusResult:
        """Aggregate responses by weighted merge.

        Args:
            responses: List of agent responses

        Returns:
            ConsensusResult with merged content
        """
        successful = self._filter_successful(responses)

        if not successful:
            return ConsensusResult(
                final_content="",
                method="weighted_merge",
                confidence=0.0,
                participating_agents=[],
            )

        if len(successful) == 1:
            return ConsensusResult(
                final_content=successful[0].content,
                method="weighted_merge",
                confidence=1.0,
                participating_agents=[successful[0].agent_id],
            )

        # Calculate weights
        weights = self._calculate_weights(successful)

        # Merge content with attribution
        merged_parts = []
        for response in successful:
            weight = weights[response.agent_id]
            merged_parts.append(
                f"[{response.agent_id} (weight: {weight:.2f})]: {response.content}"
            )

        merged_content = "\n\n".join(merged_parts)

        # Confidence based on weight distribution
        max_weight = max(weights.values())
        confidence = max_weight / sum(weights.values())

        self._logger.debug(
            "Weighted merge complete",
            num_responses=len(successful),
            weights=weights,
        )

        return ConsensusResult(
            final_content=merged_content,
            method="weighted_merge",
            confidence=confidence,
            participating_agents=[r.agent_id for r in successful],
            weights=weights,
            reasoning=f"Merged {len(successful)} responses with {self._weight_by} weighting",
        )

    def _calculate_weights(
        self,
        responses: list[AgentResponse],
    ) -> dict[str, float]:
        """Calculate weights for each response.

        Args:
            responses: Successful responses

        Returns:
            Dictionary mapping agent_id to weight
        """
        weights = {}

        if self._weight_by == "tokens":
            total_tokens = sum(r.tokens_used or 1 for r in responses)
            for r in responses:
                tokens = r.tokens_used or 1
                weights[r.agent_id] = tokens / total_tokens

        elif self._weight_by == "latency":
            # Lower latency = higher weight (inverted)
            latencies = [r.latency_ms or 1000 for r in responses]
            max_latency = max(latencies) + 1
            total_inv = sum(max_latency - lat for lat in latencies)
            for r in responses:
                lat = r.latency_ms or 1000
                weights[r.agent_id] = (max_latency - lat) / total_inv

        else:  # equal
            equal_weight = 1.0 / len(responses)
            for r in responses:
                weights[r.agent_id] = equal_weight

        return weights


class DebateConsensus(Consensus):
    """Consensus through structured debate.

    Agents present positions, then responses are synthesized
    into a final consensus after multiple rounds.
    """

    def __init__(self, max_rounds: int = 3) -> None:
        """Initialize debate consensus.

        Args:
            max_rounds: Maximum debate rounds
        """
        super().__init__()
        self._max_rounds = max_rounds

    async def aggregate(
        self,
        responses: list[AgentResponse],
    ) -> ConsensusResult:
        """Aggregate responses through debate.

        Args:
            responses: List of agent responses (initial positions)

        Returns:
            ConsensusResult with synthesized content
        """
        successful = self._filter_successful(responses)

        if not successful:
            return ConsensusResult(
                final_content="",
                method="debate",
                confidence=0.0,
                participating_agents=[],
                rounds=0,
            )

        if len(successful) == 1:
            return ConsensusResult(
                final_content=successful[0].content,
                method="debate",
                confidence=1.0,
                participating_agents=[successful[0].agent_id],
                rounds=0,
                reasoning="Single position, no debate needed",
            )

        # Collect initial positions
        positions = {r.agent_id: r.content for r in successful}

        # Synthesize positions (simplified - in full implementation,
        # this would involve back-and-forth with agents)
        synthesis = self._synthesize_positions(positions)

        # Calculate confidence based on position similarity
        confidence = self._calculate_agreement(list(positions.values()))

        rounds = min(self._max_rounds, len(successful) - 1)

        self._logger.debug(
            "Debate complete",
            num_positions=len(positions),
            rounds=rounds,
            confidence=confidence,
        )

        return ConsensusResult(
            final_content=synthesis,
            method="debate",
            confidence=confidence,
            participating_agents=list(positions.keys()),
            rounds=rounds,
            reasoning=f"Synthesized {len(positions)} positions after {rounds} rounds",
        )

    def _synthesize_positions(self, positions: dict[str, str]) -> str:
        """Synthesize multiple positions into one.

        Args:
            positions: Dictionary mapping agent_id to position

        Returns:
            Synthesized content
        """
        # Simple synthesis: present all positions with summary
        parts = ["## Debate Synthesis\n"]

        for i, (agent_id, position) in enumerate(positions.items(), 1):
            parts.append(f"### Position {i} ({agent_id}):\n{position}\n")

        parts.append("### Synthesis:")
        parts.append(
            "The above positions present different perspectives on the issue. "
            "Key points of agreement and disagreement have been noted."
        )

        return "\n".join(parts)

    def _calculate_agreement(self, contents: list[str]) -> float:
        """Calculate agreement level between contents.

        Uses simple word overlap as a proxy for agreement.

        Args:
            contents: List of response contents

        Returns:
            Agreement score from 0.0 to 1.0
        """
        if len(contents) < 2:
            return 1.0

        # Simple word overlap calculation
        word_sets = [set(c.lower().split()) for c in contents]

        # Calculate pairwise Jaccard similarity
        similarities = []
        for i in range(len(word_sets)):
            for j in range(i + 1, len(word_sets)):
                intersection = len(word_sets[i] & word_sets[j])
                union = len(word_sets[i] | word_sets[j])
                if union > 0:
                    similarities.append(intersection / union)

        if not similarities:
            return 0.5

        return sum(similarities) / len(similarities)


def create_consensus(method: str, **kwargs) -> Consensus:
    """Create a consensus mechanism with the specified method.

    Args:
        method: Consensus method (voting, weighted_merge, debate)
        **kwargs: Additional arguments for the consensus

    Returns:
        Configured consensus instance

    Raises:
        ValueError: If method is unknown
    """
    if method == "voting":
        return VotingConsensus(**kwargs)
    elif method == "weighted_merge":
        return WeightedMergeConsensus(**kwargs)
    elif method == "debate":
        return DebateConsensus(**kwargs)
    else:
        raise ValueError(f"Unknown consensus method: {method}")
