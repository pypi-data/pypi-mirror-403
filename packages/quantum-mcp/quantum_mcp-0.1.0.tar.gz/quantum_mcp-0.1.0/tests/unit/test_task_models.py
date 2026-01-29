# Description: Tests for task and response models.
# Description: Validates task lifecycle, priorities, and result aggregation.
"""Tests for task and response models."""

import pytest
from datetime import datetime, timedelta

from quantum_mcp.agents import AgentResponse, AgentStatus
from quantum_mcp.orchestration.task import (
    Task,
    TaskResult,
    TaskPriority,
    TaskStatus,
    TaskMetadata,
)


class TestTaskPriority:
    """Test TaskPriority enum."""

    def test_priority_ordering(self):
        """Test priorities have correct ordering."""
        assert TaskPriority.LOW.value < TaskPriority.NORMAL.value
        assert TaskPriority.NORMAL.value < TaskPriority.HIGH.value
        assert TaskPriority.HIGH.value < TaskPriority.CRITICAL.value

    def test_all_priorities_exist(self):
        """Test all priority levels exist."""
        assert TaskPriority.LOW
        assert TaskPriority.NORMAL
        assert TaskPriority.HIGH
        assert TaskPriority.CRITICAL


class TestTaskStatus:
    """Test TaskStatus enum."""

    def test_all_statuses_exist(self):
        """Test all status values exist."""
        assert TaskStatus.PENDING
        assert TaskStatus.QUEUED
        assert TaskStatus.ROUTING
        assert TaskStatus.EXECUTING
        assert TaskStatus.AGGREGATING
        assert TaskStatus.COMPLETED
        assert TaskStatus.FAILED
        assert TaskStatus.TIMEOUT
        assert TaskStatus.CANCELLED


class TestTaskMetadata:
    """Test TaskMetadata model."""

    def test_metadata_creation(self):
        """Test creating task metadata."""
        meta = TaskMetadata(
            source="user",
            domain="code_review",
            tags=["python", "security"],
        )
        assert meta.source == "user"
        assert meta.domain == "code_review"
        assert "python" in meta.tags

    def test_metadata_defaults(self):
        """Test metadata default values."""
        meta = TaskMetadata()
        assert meta.source is None
        assert meta.domain is None
        assert meta.tags == []
        assert meta.context == {}


class TestTask:
    """Test Task model."""

    def test_task_creation(self):
        """Test creating a task."""
        task = Task(
            prompt="Review this code for security issues",
            priority=TaskPriority.HIGH,
        )
        assert task.prompt == "Review this code for security issues"
        assert task.priority == TaskPriority.HIGH
        assert task.status == TaskStatus.PENDING
        assert len(task.task_id) > 0

    def test_task_with_required_capabilities(self):
        """Test task with required capabilities."""
        task = Task(
            prompt="Generate Python code",
            required_capabilities=["code_generation", "python"],
        )
        assert "code_generation" in task.required_capabilities
        assert "python" in task.required_capabilities

    def test_task_defaults(self):
        """Test task default values."""
        task = Task(prompt="Simple task")
        assert task.priority == TaskPriority.NORMAL
        assert task.status == TaskStatus.PENDING
        assert task.required_capabilities == []
        assert task.min_agents == 1
        assert task.max_agents == 1
        assert task.timeout_seconds == 60.0

    def test_task_multi_agent(self):
        """Test task requesting multiple agents."""
        task = Task(
            prompt="Complex reasoning task",
            min_agents=2,
            max_agents=5,
        )
        assert task.min_agents == 2
        assert task.max_agents == 5

    def test_task_unique_ids(self):
        """Test tasks have unique IDs."""
        task1 = Task(prompt="Task 1")
        task2 = Task(prompt="Task 2")
        assert task1.task_id != task2.task_id

    def test_task_with_metadata(self):
        """Test task with metadata."""
        meta = TaskMetadata(source="api", domain="ml")
        task = Task(
            prompt="Train model",
            metadata=meta,
        )
        assert task.metadata.source == "api"
        assert task.metadata.domain == "ml"

    def test_task_with_parent(self):
        """Test task with parent task (subtask)."""
        parent = Task(prompt="Parent task")
        child = Task(
            prompt="Child subtask",
            parent_task_id=parent.task_id,
        )
        assert child.parent_task_id == parent.task_id

    def test_task_created_at(self):
        """Test task has creation timestamp."""
        before = datetime.utcnow()
        task = Task(prompt="Test")
        after = datetime.utcnow()
        assert before <= task.created_at <= after


class TestTaskResult:
    """Test TaskResult model."""

    @pytest.fixture
    def sample_responses(self) -> list[AgentResponse]:
        """Create sample agent responses."""
        return [
            AgentResponse(
                agent_id="agent-1",
                content="Response from agent 1",
                status=AgentStatus.SUCCESS,
                tokens_used=100,
                latency_ms=500.0,
            ),
            AgentResponse(
                agent_id="agent-2",
                content="Response from agent 2",
                status=AgentStatus.SUCCESS,
                tokens_used=150,
                latency_ms=750.0,
            ),
        ]

    def test_result_creation(self, sample_responses):
        """Test creating a task result."""
        task = Task(prompt="Test task")
        result = TaskResult(
            task_id=task.task_id,
            status=TaskStatus.COMPLETED,
            responses=sample_responses,
            final_content="Merged response",
        )
        assert result.task_id == task.task_id
        assert result.status == TaskStatus.COMPLETED
        assert len(result.responses) == 2
        assert result.final_content == "Merged response"

    def test_result_total_tokens(self, sample_responses):
        """Test total tokens calculation."""
        result = TaskResult(
            task_id="test",
            status=TaskStatus.COMPLETED,
            responses=sample_responses,
            final_content="Result",
        )
        assert result.total_tokens == 250

    def test_result_total_latency(self, sample_responses):
        """Test total latency calculation."""
        result = TaskResult(
            task_id="test",
            status=TaskStatus.COMPLETED,
            responses=sample_responses,
            final_content="Result",
        )
        assert result.total_latency_ms == 1250.0

    def test_result_success_rate(self, sample_responses):
        """Test success rate calculation."""
        result = TaskResult(
            task_id="test",
            status=TaskStatus.COMPLETED,
            responses=sample_responses,
            final_content="Result",
        )
        assert result.success_rate == 1.0

    def test_result_with_failures(self):
        """Test result with some failed responses."""
        responses = [
            AgentResponse(
                agent_id="agent-1",
                content="Success",
                status=AgentStatus.SUCCESS,
            ),
            AgentResponse(
                agent_id="agent-2",
                content="",
                status=AgentStatus.ERROR,
                error="Connection failed",
            ),
        ]
        result = TaskResult(
            task_id="test",
            status=TaskStatus.COMPLETED,
            responses=responses,
            final_content="Partial result",
        )
        assert result.success_rate == 0.5

    def test_result_failed_task(self):
        """Test result for completely failed task."""
        result = TaskResult(
            task_id="test",
            status=TaskStatus.FAILED,
            responses=[],
            error="All agents failed",
        )
        assert result.status == TaskStatus.FAILED
        assert result.error == "All agents failed"
        assert result.success_rate == 0.0

    def test_result_timestamps(self, sample_responses):
        """Test result has timestamps."""
        result = TaskResult(
            task_id="test",
            status=TaskStatus.COMPLETED,
            responses=sample_responses,
            final_content="Result",
        )
        assert result.started_at is not None
        assert result.completed_at is not None

    def test_result_duration(self, sample_responses):
        """Test result duration calculation."""
        started = datetime.utcnow()
        completed = started + timedelta(seconds=2)
        result = TaskResult(
            task_id="test",
            status=TaskStatus.COMPLETED,
            responses=sample_responses,
            final_content="Result",
            started_at=started,
            completed_at=completed,
        )
        assert result.duration_seconds == pytest.approx(2.0, abs=0.1)


class TestTaskLifecycle:
    """Test task lifecycle transitions."""

    def test_task_status_progression(self):
        """Test valid status progression."""
        task = Task(prompt="Test")
        assert task.status == TaskStatus.PENDING

        task.status = TaskStatus.QUEUED
        assert task.status == TaskStatus.QUEUED

        task.status = TaskStatus.ROUTING
        task.status = TaskStatus.EXECUTING
        task.status = TaskStatus.AGGREGATING
        task.status = TaskStatus.COMPLETED
        assert task.status == TaskStatus.COMPLETED
