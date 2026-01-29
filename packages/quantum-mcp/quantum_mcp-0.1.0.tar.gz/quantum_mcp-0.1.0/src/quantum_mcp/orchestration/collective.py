# Description: Collective MCP interface for multi-agent orchestration.
# Description: Coordinates agents, routing, consensus, and decomposition.
"""Collective MCP interface for multi-agent orchestration."""

from __future__ import annotations

import asyncio
from enum import Enum
from typing import TYPE_CHECKING

import structlog
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    pass

from quantum_mcp.agents.base import BaseAgent
from quantum_mcp.agents.protocol import AgentResponse, AgentStatus
from quantum_mcp.orchestration.consensus import (
    Consensus,
    ConsensusResult,
    create_consensus,
)
from quantum_mcp.orchestration.decomposer import (
    Decomposer,
    DecompositionResult,
    create_decomposer,
)
from quantum_mcp.orchestration.router import Router, RoutingDecision, create_router
from quantum_mcp.orchestration.task import Task

logger = structlog.get_logger()


class ExecutionMode(str, Enum):
    """Execution mode for multi-agent tasks."""

    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    ADAPTIVE = "adaptive"


class CollectiveConfig(BaseModel):
    """Configuration for the Collective orchestrator."""

    routing_strategy: str = Field(
        default="capability",
        description="Routing strategy: capability, load_balancing, learned",
    )
    consensus_method: str = Field(
        default="voting",
        description="Consensus method: voting, weighted_merge, debate",
    )
    decomposition_strategy: str = Field(
        default="simple",
        description="Decomposition strategy: simple, recursive, domain",
    )
    execution_mode: ExecutionMode = Field(
        default=ExecutionMode.SEQUENTIAL,
        description="Execution mode for multi-agent tasks",
    )
    max_agents_per_task: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum agents per task",
    )
    auto_decompose: bool = Field(
        default=False,
        description="Automatically decompose complex tasks",
    )
    decompose_threshold: int = Field(
        default=2,
        ge=1,
        description="Minimum sentences to trigger auto-decomposition",
    )
    timeout_seconds: float = Field(
        default=300.0,
        ge=1.0,
        description="Timeout for task execution",
    )


class CollectiveHealthStatus(BaseModel):
    """Health status of the collective."""

    healthy: bool = Field(..., description="Overall health status")
    agents_total: int = Field(..., description="Total registered agents")
    agents_healthy: int = Field(..., description="Number of healthy agents")
    agents_unhealthy: list[str] = Field(
        default_factory=list,
        description="IDs of unhealthy agents",
    )


class CollectiveResult(BaseModel):
    """Result of collective task execution."""

    task_id: str = Field(..., description="ID of the executed task")
    final_content: str = Field(..., description="Final aggregated content")
    success: bool = Field(..., description="Whether execution succeeded")
    agents_used: list[str] = Field(
        default_factory=list,
        description="IDs of agents that participated",
    )
    consensus_method: str | None = Field(
        default=None,
        description="Consensus method used",
    )
    consensus_confidence: float | None = Field(
        default=None,
        description="Confidence in consensus result",
    )
    subtasks_completed: int | None = Field(
        default=None,
        description="Number of subtasks completed (if decomposed)",
    )
    total_tokens: int | None = Field(
        default=None,
        description="Total tokens used across all agents",
    )
    total_latency_ms: float | None = Field(
        default=None,
        description="Total latency in milliseconds",
    )
    error: str | None = Field(
        default=None,
        description="Error message if execution failed",
    )


class Collective:
    """Orchestrator for multi-agent task execution.

    The Collective coordinates multiple agents to solve tasks through:
    - Task decomposition (breaking complex tasks into subtasks)
    - Routing (selecting appropriate agents for each task)
    - Execution (running tasks on selected agents)
    - Consensus (aggregating responses into final result)
    """

    def __init__(
        self,
        agents: list[BaseAgent],
        config: CollectiveConfig | None = None,
    ) -> None:
        """Initialize the Collective.

        Args:
            agents: List of available agents
            config: Collective configuration
        """
        self._agents = list(agents)
        self._config = config or CollectiveConfig()
        self._logger = logger.bind(component="Collective")

        # Initialize components
        self._router: Router = create_router(
            self._config.routing_strategy,
            self._agents,
        )
        self._consensus: Consensus = create_consensus(self._config.consensus_method)
        self._decomposer: Decomposer = create_decomposer(
            self._config.decomposition_strategy
        )

    @property
    def agents(self) -> list[BaseAgent]:
        """Get registered agents."""
        return self._agents

    @property
    def config(self) -> CollectiveConfig:
        """Get collective configuration."""
        return self._config

    def add_agent(self, agent: BaseAgent) -> None:
        """Add an agent to the collective.

        Args:
            agent: Agent to add
        """
        self._agents.append(agent)
        # Rebuild router with updated agent list
        self._router = create_router(
            self._config.routing_strategy,
            self._agents,
        )
        self._logger.info("Agent added", agent_id=agent.agent_id, name=agent.name)

    def remove_agent(self, agent_id: str) -> bool:
        """Remove an agent from the collective.

        Args:
            agent_id: ID of agent to remove

        Returns:
            True if agent was removed
        """
        for i, agent in enumerate(self._agents):
            if agent.agent_id == agent_id:
                self._agents.pop(i)
                # Rebuild router
                self._router = create_router(
                    self._config.routing_strategy,
                    self._agents,
                )
                self._logger.info("Agent removed", agent_id=agent_id)
                return True
        return False

    async def execute(self, task: Task) -> CollectiveResult:
        """Execute a task using the collective.

        Args:
            task: Task to execute

        Returns:
            CollectiveResult with aggregated response
        """
        self._logger.info(
            "Executing task",
            task_id=task.task_id,
            prompt_length=len(task.prompt),
        )

        try:
            # Decompose if configured and appropriate
            decomposition: DecompositionResult | None = None
            if self._config.auto_decompose:
                decomposition = await self._decomposer.decompose(task)
                if len(decomposition.subtasks) <= 1:
                    decomposition = None

            if decomposition and len(decomposition.subtasks) > 1:
                return await self._execute_decomposed(task, decomposition)
            else:
                return await self._execute_single(task)

        except asyncio.TimeoutError:
            return CollectiveResult(
                task_id=task.task_id,
                final_content="",
                success=False,
                error=f"Execution timed out after {self._config.timeout_seconds}s",
            )
        except Exception as e:
            self._logger.exception("Task execution failed", task_id=task.task_id)
            return CollectiveResult(
                task_id=task.task_id,
                final_content="",
                success=False,
                error=str(e),
            )

    async def _execute_single(self, task: Task) -> CollectiveResult:
        """Execute a single (non-decomposed) task.

        Args:
            task: Task to execute

        Returns:
            CollectiveResult
        """
        # Route task to agents
        decision: RoutingDecision = await self._router.route(task)

        if not decision.selected_agents:
            return CollectiveResult(
                task_id=task.task_id,
                final_content="",
                success=False,
                error="No agents available for task",
            )

        # Get selected agents
        selected = self._get_agents_by_ids(decision.selected_agents)

        # Execute on selected agents
        responses = await self._execute_on_agents(selected, task.prompt)

        # Filter successful responses
        successful = [r for r in responses if r.status == AgentStatus.SUCCESS]

        if not successful:
            # Return error from first failed response
            failed = [r for r in responses if r.status == AgentStatus.ERROR]
            error_msg = failed[0].error if failed else "All agents failed"
            return CollectiveResult(
                task_id=task.task_id,
                final_content="",
                success=False,
                agents_used=decision.selected_agents,
                error=error_msg,
            )

        # Apply consensus if multiple responses
        if len(successful) > 1:
            consensus_result: ConsensusResult = await self._consensus.aggregate(
                successful
            )
            return CollectiveResult(
                task_id=task.task_id,
                final_content=consensus_result.final_content,
                success=True,
                agents_used=[r.agent_id for r in successful],
                consensus_method=consensus_result.method,
                consensus_confidence=consensus_result.confidence,
                total_tokens=sum(r.tokens_used or 0 for r in successful),
                total_latency_ms=sum(r.latency_ms or 0 for r in successful),
            )
        else:
            # Single response, no consensus needed
            response = successful[0]
            return CollectiveResult(
                task_id=task.task_id,
                final_content=response.content,
                success=True,
                agents_used=[response.agent_id],
                total_tokens=response.tokens_used,
                total_latency_ms=response.latency_ms,
            )

    async def _execute_decomposed(
        self,
        task: Task,
        decomposition: DecompositionResult,
    ) -> CollectiveResult:
        """Execute a decomposed task.

        Args:
            task: Original task
            decomposition: Decomposition result with subtasks

        Returns:
            CollectiveResult with aggregated subtask results
        """
        self._logger.debug(
            "Executing decomposed task",
            task_id=task.task_id,
            num_subtasks=len(decomposition.subtasks),
            parallel=decomposition.is_parallelizable,
        )

        subtask_results = []
        agents_used = set()
        total_tokens = 0
        total_latency = 0.0

        if (
            decomposition.is_parallelizable
            and self._config.execution_mode != ExecutionMode.SEQUENTIAL
        ):
            # Execute subtasks in parallel
            subtask_tasks = []
            for subtask in decomposition.subtasks:
                sub_task = Task(
                    prompt=subtask.content,
                    required_capabilities=subtask.required_capabilities,
                )
                subtask_tasks.append(self._execute_single(sub_task))

            results = await asyncio.gather(*subtask_tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, Exception):
                    continue
                if result.success:
                    subtask_results.append(result.final_content)
                    agents_used.update(result.agents_used)
                    total_tokens += result.total_tokens or 0
                    total_latency += result.total_latency_ms or 0
        else:
            # Execute subtasks sequentially
            for subtask in decomposition.subtasks:
                sub_task = Task(
                    prompt=subtask.content,
                    required_capabilities=subtask.required_capabilities,
                )
                result = await self._execute_single(sub_task)
                if result.success:
                    subtask_results.append(result.final_content)
                    agents_used.update(result.agents_used)
                    total_tokens += result.total_tokens or 0
                    total_latency += result.total_latency_ms or 0

        if not subtask_results:
            return CollectiveResult(
                task_id=task.task_id,
                final_content="",
                success=False,
                error="All subtasks failed",
            )

        # Combine subtask results
        combined = "\n\n".join(subtask_results)

        return CollectiveResult(
            task_id=task.task_id,
            final_content=combined,
            success=True,
            agents_used=list(agents_used),
            subtasks_completed=len(subtask_results),
            total_tokens=total_tokens,
            total_latency_ms=total_latency,
        )

    async def _execute_on_agents(
        self,
        agents: list[BaseAgent],
        prompt: str,
    ) -> list[AgentResponse]:
        """Execute prompt on multiple agents.

        Args:
            agents: Agents to execute on
            prompt: Prompt to execute

        Returns:
            List of agent responses
        """
        if self._config.execution_mode == ExecutionMode.PARALLEL:
            # Execute in parallel
            tasks = [agent.execute(prompt) for agent in agents]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            responses = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    responses.append(
                        AgentResponse(
                            agent_id=agents[i].agent_id,
                            content="",
                            status=AgentStatus.ERROR,
                            error=str(result),
                        )
                    )
                else:
                    responses.append(result)
            return responses
        else:
            # Execute sequentially
            responses = []
            for agent in agents:
                try:
                    response = await agent.execute(prompt)
                    responses.append(response)
                except Exception as e:
                    responses.append(
                        AgentResponse(
                            agent_id=agent.agent_id,
                            content="",
                            status=AgentStatus.ERROR,
                            error=str(e),
                        )
                    )
            return responses

    def _get_agents_by_ids(self, agent_ids: list[str]) -> list[BaseAgent]:
        """Get agents by their IDs.

        Args:
            agent_ids: List of agent IDs

        Returns:
            List of matching agents
        """
        id_set = set(agent_ids)
        return [a for a in self._agents if a.agent_id in id_set]

    async def health_check(self) -> CollectiveHealthStatus:
        """Check health of all agents in the collective.

        Returns:
            CollectiveHealthStatus with agent health info
        """
        healthy_count = 0
        unhealthy = []

        for agent in self._agents:
            try:
                is_healthy = await agent.health_check()
                if is_healthy:
                    healthy_count += 1
                else:
                    unhealthy.append(agent.agent_id)
            except Exception:
                unhealthy.append(agent.agent_id)

        return CollectiveHealthStatus(
            healthy=healthy_count > 0,
            agents_total=len(self._agents),
            agents_healthy=healthy_count,
            agents_unhealthy=unhealthy,
        )
