# Description: Task and result models for multi-agent orchestration.
# Description: Defines task lifecycle, priorities, and result aggregation.
"""Task and result models for multi-agent orchestration."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import IntEnum, Enum
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field, computed_field

if TYPE_CHECKING:
    pass

from quantum_mcp.agents.protocol import AgentResponse, AgentStatus


class TaskPriority(IntEnum):
    """Priority levels for task scheduling.

    Higher values indicate higher priority.
    """

    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class TaskStatus(str, Enum):
    """Status of a task through its lifecycle."""

    PENDING = "pending"
    QUEUED = "queued"
    ROUTING = "routing"
    EXECUTING = "executing"
    AGGREGATING = "aggregating"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class TaskMetadata(BaseModel):
    """Additional metadata for task routing and tracking."""

    source: str | None = Field(
        default=None,
        description="Origin of the task (user, api, system, subtask)",
    )
    domain: str | None = Field(
        default=None,
        description="Problem domain (code, reasoning, data, etc.)",
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Tags for categorization and filtering",
    )
    context: dict[str, str] = Field(
        default_factory=dict,
        description="Additional context key-value pairs",
    )


class Task(BaseModel):
    """Represents a task to be executed by one or more agents.

    Tasks flow through the orchestration pipeline:
    PENDING -> QUEUED -> ROUTING -> EXECUTING -> AGGREGATING -> COMPLETED
    """

    task_id: str = Field(
        default_factory=lambda: f"task-{uuid.uuid4().hex[:12]}",
        description="Unique task identifier",
    )
    prompt: str = Field(
        ...,
        description="The prompt/instruction for agents",
    )
    priority: TaskPriority = Field(
        default=TaskPriority.NORMAL,
        description="Task priority for scheduling",
    )
    status: TaskStatus = Field(
        default=TaskStatus.PENDING,
        description="Current task status",
    )
    required_capabilities: list[str] = Field(
        default_factory=list,
        description="Capabilities required to handle this task",
    )
    preferred_providers: list[str] = Field(
        default_factory=list,
        description="Preferred agent providers (claude, openai, etc.)",
    )
    min_agents: int = Field(
        default=1,
        ge=1,
        description="Minimum number of agents to execute task",
    )
    max_agents: int = Field(
        default=1,
        ge=1,
        description="Maximum number of agents to execute task",
    )
    timeout_seconds: float = Field(
        default=60.0,
        ge=1.0,
        description="Timeout for task execution",
    )
    parent_task_id: str | None = Field(
        default=None,
        description="Parent task ID if this is a subtask",
    )
    metadata: TaskMetadata = Field(
        default_factory=TaskMetadata,
        description="Additional task metadata",
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Task creation timestamp",
    )

    def is_multi_agent(self) -> bool:
        """Check if task requires multiple agents."""
        return self.max_agents > 1

    def is_subtask(self) -> bool:
        """Check if this is a subtask of another task."""
        return self.parent_task_id is not None


class TaskResult(BaseModel):
    """Result of task execution, potentially from multiple agents.

    Aggregates responses from all participating agents and provides
    metrics about the execution.
    """

    task_id: str = Field(
        ...,
        description="ID of the task this result belongs to",
    )
    status: TaskStatus = Field(
        ...,
        description="Final task status",
    )
    responses: list[AgentResponse] = Field(
        default_factory=list,
        description="Responses from all participating agents",
    )
    final_content: str | None = Field(
        default=None,
        description="Final aggregated/consensus content",
    )
    error: str | None = Field(
        default=None,
        description="Error message if task failed",
    )
    started_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Execution start timestamp",
    )
    completed_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Execution completion timestamp",
    )
    routing_decision: dict[str, str] = Field(
        default_factory=dict,
        description="Information about routing decision",
    )
    consensus_method: str | None = Field(
        default=None,
        description="Consensus method used if multiple agents",
    )

    @computed_field
    @property
    def total_tokens(self) -> int:
        """Total tokens used across all responses."""
        return sum(
            r.tokens_used or 0
            for r in self.responses
        )

    @computed_field
    @property
    def total_latency_ms(self) -> float:
        """Total latency across all responses."""
        return sum(
            r.latency_ms or 0.0
            for r in self.responses
        )

    @computed_field
    @property
    def success_rate(self) -> float:
        """Proportion of successful responses."""
        if not self.responses:
            return 0.0
        successful = sum(
            1 for r in self.responses
            if r.status == AgentStatus.SUCCESS
        )
        return successful / len(self.responses)

    @computed_field
    @property
    def duration_seconds(self) -> float:
        """Task execution duration in seconds."""
        delta = self.completed_at - self.started_at
        return delta.total_seconds()

    def get_successful_responses(self) -> list[AgentResponse]:
        """Get only successful responses."""
        return [
            r for r in self.responses
            if r.status == AgentStatus.SUCCESS
        ]

    def get_failed_responses(self) -> list[AgentResponse]:
        """Get only failed responses."""
        return [
            r for r in self.responses
            if r.status != AgentStatus.SUCCESS
        ]
