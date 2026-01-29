# Description: Router implementations for agent selection.
# Description: Capability matching, load balancing, and learned routing strategies.
"""Router implementations for agent selection."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import structlog

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    pass

from quantum_mcp.agents.base import BaseAgent
from quantum_mcp.orchestration.task import Task

logger = structlog.get_logger()


class RoutingDecision(BaseModel):
    """Result of a routing decision."""

    task_id: str = Field(..., description="ID of the task being routed")
    selected_agents: list[str] = Field(
        ...,
        description="IDs of selected agents",
    )
    strategy: str = Field(..., description="Routing strategy used")
    scores: dict[str, float] = Field(
        default_factory=dict,
        description="Scores for each considered agent",
    )
    reasoning: str | None = Field(
        default=None,
        description="Human-readable routing reasoning",
    )


class Router(ABC):
    """Abstract base class for agent routers.

    Routers select which agent(s) should handle a given task.
    """

    def __init__(self, agents: list[BaseAgent]) -> None:
        """Initialize router with available agents.

        Args:
            agents: List of available agents
        """
        self._agents = agents
        self._logger = logger.bind(router=self.__class__.__name__)

    @property
    def agents(self) -> list[BaseAgent]:
        """Get available agents."""
        return self._agents

    @abstractmethod
    async def route(self, task: Task) -> RoutingDecision:
        """Select agent(s) for a task.

        Args:
            task: Task to route

        Returns:
            RoutingDecision with selected agents
        """
        raise NotImplementedError


class CapabilityRouter(Router):
    """Routes tasks based on agent capabilities.

    Matches task requirements against agent capabilities and
    selects agents with the best capability overlap.
    """

    async def route(self, task: Task) -> RoutingDecision:
        """Select agents based on capability matching.

        Args:
            task: Task with required capabilities

        Returns:
            RoutingDecision with best-matching agents
        """
        scores: dict[str, float] = {}

        for agent in self._agents:
            score = self._score_agent(agent, task)
            scores[agent.agent_id] = score

        # Sort by score descending
        sorted_agents = sorted(
            self._agents,
            key=lambda a: scores[a.agent_id],
            reverse=True,
        )

        # Select required number of agents
        num_agents = min(task.max_agents, len(sorted_agents))
        num_agents = max(num_agents, task.min_agents)

        selected = sorted_agents[:num_agents]
        selected_ids = [a.agent_id for a in selected]

        reasoning = self._build_reasoning(task, selected, scores)

        self._logger.debug(
            "Routing decision",
            task_id=task.task_id,
            selected=selected_ids,
            scores=scores,
        )

        return RoutingDecision(
            task_id=task.task_id,
            selected_agents=selected_ids,
            strategy="capability",
            scores=scores,
            reasoning=reasoning,
        )

    def _score_agent(self, agent: BaseAgent, task: Task) -> float:
        """Score an agent for a task based on capabilities.

        Args:
            agent: Agent to score
            task: Task requirements

        Returns:
            Score from 0.0 to 1.0
        """
        score = 0.0

        # Base score for having any capabilities
        if agent.get_capabilities():
            score += 0.1

        # Score for matching required capabilities
        if task.required_capabilities:
            matches = sum(
                1 for cap in task.required_capabilities
                if agent.has_capability(cap)
            )
            score += matches / len(task.required_capabilities) * 0.5

        # Bonus for preferred provider
        if task.preferred_providers:
            if agent.provider in task.preferred_providers:
                score += 0.3

        # Score based on capability confidence
        for cap in agent.get_capabilities():
            if cap.name in task.required_capabilities:
                score += cap.confidence * 0.1

        return min(score, 1.0)

    def _build_reasoning(
        self,
        task: Task,
        selected: list[BaseAgent],
        scores: dict[str, float],
    ) -> str:
        """Build human-readable reasoning for the decision."""
        parts = []
        parts.append(f"Task requires: {task.required_capabilities or 'no specific capabilities'}")

        for agent in selected:
            caps = [c.name for c in agent.get_capabilities()]
            parts.append(
                f"Selected {agent.name} (score: {scores[agent.agent_id]:.2f}, "
                f"capabilities: {caps})"
            )

        return "; ".join(parts)


class LoadBalancingRouter(Router):
    """Routes tasks based on agent load.

    Distributes tasks to agents with lowest current load.
    """

    def __init__(self, agents: list[BaseAgent]) -> None:
        """Initialize load balancing router."""
        super().__init__(agents)
        self._round_robin_index = 0
        self._agent_loads: dict[str, int] = {a.agent_id: 0 for a in agents}

    async def route(self, task: Task) -> RoutingDecision:
        """Select agents based on current load.

        Args:
            task: Task to route

        Returns:
            RoutingDecision with least-loaded agents
        """
        # Get current loads
        loads = {}
        for agent in self._agents:
            if hasattr(agent, "current_load"):
                loads[agent.agent_id] = agent.current_load
            else:
                loads[agent.agent_id] = self._agent_loads.get(agent.agent_id, 0)

        # Sort by load ascending
        sorted_agents = sorted(
            self._agents,
            key=lambda a: loads[a.agent_id],
        )

        # Check if all loads are equal (use round-robin)
        unique_loads = set(loads.values())
        if len(unique_loads) == 1:
            # Round-robin selection
            selected = []
            for i in range(min(task.max_agents, len(self._agents))):
                idx = (self._round_robin_index + i) % len(self._agents)
                selected.append(self._agents[idx])
            self._round_robin_index = (
                self._round_robin_index + len(selected)
            ) % len(self._agents)
        else:
            # Select least loaded
            num_agents = min(task.max_agents, len(sorted_agents))
            selected = sorted_agents[:num_agents]

        selected_ids = [a.agent_id for a in selected]

        # Update tracked loads
        for agent_id in selected_ids:
            self._agent_loads[agent_id] = self._agent_loads.get(agent_id, 0) + 1

        # Convert loads to scores (inverted)
        max_load = max(loads.values()) + 1
        scores = {
            agent_id: 1.0 - (load / max_load)
            for agent_id, load in loads.items()
        }

        return RoutingDecision(
            task_id=task.task_id,
            selected_agents=selected_ids,
            strategy="load_balancing",
            scores=scores,
            reasoning=f"Selected agents with loads: {[loads[a] for a in selected_ids]}",
        )

    def report_completion(self, agent_id: str) -> None:
        """Report that an agent completed a task.

        Args:
            agent_id: ID of the agent that completed
        """
        if agent_id in self._agent_loads:
            self._agent_loads[agent_id] = max(0, self._agent_loads[agent_id] - 1)


@dataclass
class AgentPerformanceStats:
    """Performance statistics for an agent."""

    total_tasks: int = 0
    successful_tasks: int = 0
    total_latency_ms: float = 0.0
    domain_stats: dict[str, dict[str, float]] = field(default_factory=dict)

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_tasks == 0:
            return 0.0
        return self.successful_tasks / self.total_tasks

    @property
    def avg_latency_ms(self) -> float:
        """Calculate average latency."""
        if self.total_tasks == 0:
            return 0.0
        return self.total_latency_ms / self.total_tasks


class LearnedRouter(Router):
    """Routes tasks based on learned agent performance.

    Tracks historical performance and learns which agents
    perform best for different task types.
    """

    def __init__(self, agents: list[BaseAgent]) -> None:
        """Initialize learned router."""
        super().__init__(agents)
        self._stats: dict[str, AgentPerformanceStats] = defaultdict(
            AgentPerformanceStats
        )
        self._capability_router = CapabilityRouter(agents)

    async def route(self, task: Task) -> RoutingDecision:
        """Select agents based on learned performance.

        Falls back to capability routing if no historical data.

        Args:
            task: Task to route

        Returns:
            RoutingDecision with best-performing agents
        """
        # Get domain from task metadata
        domain = task.metadata.domain or "general"

        # Calculate scores combining capability and learned performance
        scores: dict[str, float] = {}

        for agent in self._agents:
            # Base capability score
            cap_score = self._capability_router._score_agent(agent, task)

            # Learned performance score
            learned_score = self._get_learned_score(agent.agent_id, domain)

            # Combine scores (weighted average)
            if learned_score > 0:
                scores[agent.agent_id] = 0.4 * cap_score + 0.6 * learned_score
            else:
                scores[agent.agent_id] = cap_score

        # Sort by combined score
        sorted_agents = sorted(
            self._agents,
            key=lambda a: scores[a.agent_id],
            reverse=True,
        )

        num_agents = min(task.max_agents, len(sorted_agents))
        selected = sorted_agents[:num_agents]
        selected_ids = [a.agent_id for a in selected]

        return RoutingDecision(
            task_id=task.task_id,
            selected_agents=selected_ids,
            strategy="learned",
            scores=scores,
            reasoning=f"Selected based on learned performance for domain: {domain}",
        )

    def _get_learned_score(self, agent_id: str, domain: str) -> float:
        """Get learned performance score for agent in domain.

        Args:
            agent_id: Agent identifier
            domain: Task domain

        Returns:
            Performance score from 0.0 to 1.0
        """
        stats = self._stats.get(agent_id)
        if not stats or stats.total_tasks == 0:
            return 0.0

        # Check domain-specific stats
        domain_stats = stats.domain_stats.get(domain, {})
        if domain_stats:
            domain_success = domain_stats.get("success_rate", 0.0)
            return domain_success

        # Fall back to overall success rate
        return stats.success_rate

    def record_outcome(
        self,
        agent_id: str,
        task_domain: str,
        success: bool,
        latency_ms: float,
    ) -> None:
        """Record the outcome of a task execution.

        Args:
            agent_id: ID of the agent that executed
            task_domain: Domain of the task
            success: Whether execution succeeded
            latency_ms: Execution latency
        """
        stats = self._stats[agent_id]
        stats.total_tasks += 1
        if success:
            stats.successful_tasks += 1
        stats.total_latency_ms += latency_ms

        # Update domain-specific stats
        if task_domain not in stats.domain_stats:
            stats.domain_stats[task_domain] = {
                "total": 0,
                "successful": 0,
                "success_rate": 0.0,
            }

        domain = stats.domain_stats[task_domain]
        domain["total"] += 1
        if success:
            domain["successful"] += 1
        domain["success_rate"] = domain["successful"] / domain["total"]

        self._logger.debug(
            "Recorded outcome",
            agent_id=agent_id,
            domain=task_domain,
            success=success,
        )

    def get_agent_stats(self, agent_id: str) -> dict:
        """Get performance statistics for an agent.

        Args:
            agent_id: Agent identifier

        Returns:
            Dictionary with performance stats
        """
        stats = self._stats.get(agent_id)
        if not stats:
            return {"total_tasks": 0, "success_rate": 0.0}

        return {
            "total_tasks": stats.total_tasks,
            "successful_tasks": stats.successful_tasks,
            "success_rate": stats.success_rate,
            "avg_latency_ms": stats.avg_latency_ms,
            "domain_stats": dict(stats.domain_stats),
        }


def create_router(strategy: str, agents: list[BaseAgent]) -> Router:
    """Create a router with the specified strategy.

    Args:
        strategy: Routing strategy name. Options:
            - "capability": Match task requirements to agent capabilities
            - "load_balancing": Distribute to least-loaded agents
            - "learned": Use historical performance data
            - "qubo": QUBO optimization (classical solver)
            - "qaoa": Quantum Approximate Optimization Algorithm
            - "dwave": D-Wave quantum annealing
        agents: List of available agents

    Returns:
        Configured router instance

    Raises:
        ValueError: If strategy is unknown
    """
    if strategy == "capability":
        return CapabilityRouter(agents)
    elif strategy == "load_balancing":
        return LoadBalancingRouter(agents)
    elif strategy == "learned":
        return LearnedRouter(agents)
    elif strategy == "qubo":
        from quantum_mcp.orchestration.qubo import QUBORouter

        return QUBORouter(agents)
    elif strategy == "qaoa":
        from quantum_mcp.orchestration.qaoa_router import QAOARouter

        return QAOARouter(agents)
    elif strategy == "dwave":
        from quantum_mcp.orchestration.dwave_router import DWaveRouter

        return DWaveRouter(agents)
    else:
        raise ValueError(f"Unknown routing strategy: {strategy}")
