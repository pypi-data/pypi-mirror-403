# Description: Data models for quantum client.
# Description: Defines BackendInfo, JobInfo, and related structures.
"""Data models for quantum client."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class JobStatus(Enum):
    """Status of a quantum job."""

    WAITING = "waiting"
    EXECUTING = "executing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class JobInfo:
    """Information about a quantum job."""

    id: str
    name: str
    status: JobStatus
    backend: str
    shots: int
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    cost_estimate: Optional[float] = None

    @property
    def is_terminal(self) -> bool:
        """Check if job is in a terminal state."""
        return self.status in (JobStatus.SUCCEEDED, JobStatus.FAILED, JobStatus.CANCELLED)

    @property
    def is_success(self) -> bool:
        """Check if job succeeded."""
        return self.status == JobStatus.SUCCEEDED


@dataclass
class JobResult:
    """Result of a quantum job execution."""

    job_id: str
    counts: dict[str, int]
    shots: int
    backend: str
    execution_time_ms: Optional[float] = None
    raw_result: Optional[Any] = None

    @property
    def probabilities(self) -> dict[str, float]:
        """Get measurement probabilities from counts."""
        total = sum(self.counts.values())
        if total == 0:
            return {}
        return {k: v / total for k, v in self.counts.items()}


@dataclass
class CostEstimate:
    """Cost estimate for a quantum job."""

    backend: str
    shots: int
    estimated_cost_usd: float
    currency: str = "USD"
    notes: Optional[str] = None


@dataclass
class BackendInfo:
    """Information about a quantum backend."""

    id: str
    provider: str
    backend_type: str  # "simulator" or "hardware"
    num_qubits: int
    status: str  # "online", "offline", "maintenance"
    gate_set: list[str] = field(default_factory=list)
    queue_depth: Optional[int] = None
    cost_per_shot: Optional[float] = None
    description: Optional[str] = None

    @property
    def is_simulator(self) -> bool:
        """Check if this is a simulator backend."""
        return self.backend_type == "simulator" or "simulator" in self.id.lower()

    @property
    def is_available(self) -> bool:
        """Check if backend is available for jobs."""
        return self.status == "online"
