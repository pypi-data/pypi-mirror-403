# Description: Annealing backend protocol and result models.
# Description: Defines interface for D-Wave and classical fallback solvers.
"""Quantum annealing protocol and data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    pass


@dataclass
class AnnealingSample:
    """A single sample from an annealing solver.

    Attributes:
        bitstring: Mapping of variable index to binary value (0 or 1)
        energy: Energy of this solution (lower is better)
        num_occurrences: Number of times this solution was sampled
    """

    bitstring: dict[int, int]
    energy: float
    num_occurrences: int = 1

    def get_selected_indices(self) -> list[int]:
        """Get indices of variables set to 1."""
        return [idx for idx, val in self.bitstring.items() if val == 1]

    def to_binary_string(self, num_vars: int | None = None) -> str:
        """Convert bitstring to binary string representation.

        Args:
            num_vars: Total number of variables (for padding)

        Returns:
            Binary string like "01101"
        """
        if num_vars is None:
            num_vars = max(self.bitstring.keys()) + 1 if self.bitstring else 0

        return "".join(str(self.bitstring.get(i, 0)) for i in range(num_vars))


@dataclass
class AnnealingResult:
    """Result from an annealing solve operation.

    Attributes:
        samples: List of samples ordered by energy (best first)
        timing_info: Timing information from the solver
        metadata: Additional solver-specific metadata
    """

    samples: list[AnnealingSample]
    timing_info: dict[str, float] = field(default_factory=dict)
    metadata: dict[str, object] = field(default_factory=dict)

    @property
    def best_sample(self) -> AnnealingSample:
        """Get the sample with lowest energy."""
        if not self.samples:
            raise ValueError("No samples in result")
        return min(self.samples, key=lambda s: s.energy)

    @property
    def best_energy(self) -> float:
        """Get the lowest energy found."""
        return self.best_sample.energy

    @property
    def num_samples(self) -> int:
        """Total number of unique samples."""
        return len(self.samples)

    @property
    def total_occurrences(self) -> int:
        """Total number of samples including occurrences."""
        return sum(s.num_occurrences for s in self.samples)

    def get_samples_below_energy(self, threshold: float) -> list[AnnealingSample]:
        """Get all samples with energy below threshold."""
        return [s for s in self.samples if s.energy < threshold]


@runtime_checkable
class AnnealingBackend(Protocol):
    """Protocol for quantum annealing backends.

    Implementations include D-Wave hardware and classical exact solvers.
    """

    @property
    def backend_id(self) -> str:
        """Unique identifier for this backend."""
        ...

    @property
    def is_connected(self) -> bool:
        """Check if backend is connected."""
        ...

    async def connect(self) -> None:
        """Establish connection to the backend."""
        ...

    async def disconnect(self) -> None:
        """Close connection to the backend."""
        ...

    async def solve_qubo(
        self,
        Q: dict[tuple[int, int], float],
        num_reads: int = 100,
        **kwargs: object,
    ) -> AnnealingResult:
        """Solve a QUBO (Quadratic Unconstrained Binary Optimization) problem.

        Args:
            Q: QUBO matrix as dict {(i, j): weight} where i <= j
            num_reads: Number of samples to return
            **kwargs: Backend-specific parameters

        Returns:
            AnnealingResult with samples
        """
        ...

    async def solve_bqm(
        self,
        linear: dict[int, float],
        quadratic: dict[tuple[int, int], float],
        offset: float = 0.0,
        num_reads: int = 100,
        **kwargs: object,
    ) -> AnnealingResult:
        """Solve a BQM (Binary Quadratic Model) problem.

        Args:
            linear: Linear biases {variable: bias}
            quadratic: Quadratic biases {(i, j): bias}
            offset: Constant energy offset
            num_reads: Number of samples to return
            **kwargs: Backend-specific parameters

        Returns:
            AnnealingResult with samples
        """
        ...
