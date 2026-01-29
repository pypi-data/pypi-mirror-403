# Description: Classical exact solver for QUBO problems.
# Description: Fallback when D-Wave is unavailable, uses brute-force enumeration.
"""Classical exact solver backend for QUBO problems."""

from __future__ import annotations

from itertools import product
from typing import TYPE_CHECKING

import numpy as np
import structlog

from quantum_mcp.backends.annealing import AnnealingResult, AnnealingSample
from quantum_mcp.backends.protocol import (
    BackendCapabilities,
    BackendParadigm,
    BackendStatus,
    BaseQuantumBackend,
)

if TYPE_CHECKING:
    pass

logger = structlog.get_logger()


class ExactSolverBackend(BaseQuantumBackend):
    """Classical exact solver backend.

    Uses brute-force enumeration to find optimal QUBO solutions.
    Suitable for small problems (up to ~20 variables) or as a
    fallback when quantum hardware is unavailable.
    """

    def __init__(self, max_variables: int = 20) -> None:
        """Initialize exact solver.

        Args:
            max_variables: Maximum variables before falling back to greedy
        """
        super().__init__()
        self._max_variables = max_variables
        self._logger = logger.bind(backend="ExactSolver")

    @property
    def backend_id(self) -> str:
        """Unique identifier for this backend."""
        return "classical.exact_solver"

    @property
    def capabilities(self) -> BackendCapabilities:
        """Backend capabilities."""
        return BackendCapabilities(
            paradigm=BackendParadigm.ANNEALING,
            max_qubits=self._max_variables,
            supports_async=False,
            is_simulator=True,
            provider="classical",
            native_operations=["qubo", "bqm"],
        )

    async def connect(self) -> None:
        """Connect to backend (no-op for classical)."""
        self._connected = True
        self._logger.debug("ExactSolver backend ready")

    async def health_check(self) -> BackendStatus:
        """Check backend health."""
        return BackendStatus.AVAILABLE

    async def solve_qubo(
        self,
        Q: dict[tuple[int, int], float],
        num_reads: int = 100,
        **kwargs: object,
    ) -> AnnealingResult:
        """Solve QUBO via brute-force enumeration.

        Args:
            Q: QUBO matrix as dict {(i, j): weight}
            num_reads: Ignored for exact solver (returns all optimal)
            **kwargs: Ignored

        Returns:
            AnnealingResult with optimal solution(s)
        """
        if not Q:
            return AnnealingResult(
                samples=[AnnealingSample(bitstring={}, energy=0.0)],
                timing_info={"solver_time_ms": 0},
                metadata={"solver": "exact", "method": "empty"},
            )

        # Get all variables
        variables = sorted(set(i for pair in Q.keys() for i in pair))
        n = len(variables)
        var_to_idx = {v: i for i, v in enumerate(variables)}
        idx_to_var = {i: v for v, i in var_to_idx.items()}

        self._logger.debug("Solving QUBO", num_variables=n, num_terms=len(Q))

        if n > self._max_variables:
            self._logger.warning(
                "Problem too large for exact solver, using greedy",
                num_variables=n,
                max_variables=self._max_variables,
            )
            return await self._solve_greedy(Q, variables, var_to_idx, idx_to_var)

        # Build matrix representation
        Q_matrix = np.zeros((n, n))
        for (i, j), val in Q.items():
            Q_matrix[var_to_idx[i], var_to_idx[j]] = val

        # Make symmetric for consistent energy calculation
        Q_matrix = (Q_matrix + Q_matrix.T) / 2

        # Enumerate all solutions
        best_energy = float("inf")
        best_solutions: list[tuple[int, ...]] = []

        for bits in product([0, 1], repeat=n):
            x = np.array(bits)
            energy = float(x @ Q_matrix @ x)

            if energy < best_energy - 1e-10:
                best_energy = energy
                best_solutions = [bits]
            elif abs(energy - best_energy) < 1e-10:
                best_solutions.append(bits)

        # Convert to AnnealingSamples
        samples = []
        for bits in best_solutions:
            bitstring = {idx_to_var[i]: int(bits[i]) for i in range(n)}
            samples.append(
                AnnealingSample(
                    bitstring=bitstring,
                    energy=best_energy,
                    num_occurrences=1,
                )
            )

        self._logger.debug(
            "Exact solution found",
            best_energy=best_energy,
            num_optimal=len(samples),
        )

        return AnnealingResult(
            samples=samples,
            timing_info={"solver_time_ms": 0},
            metadata={
                "solver": "exact",
                "method": "brute_force",
                "num_variables": n,
                "search_space": 2**n,
            },
        )

    async def _solve_greedy(
        self,
        Q: dict[tuple[int, int], float],
        variables: list[int],
        var_to_idx: dict[int, int],
        idx_to_var: dict[int, int],
    ) -> AnnealingResult:
        """Greedy solver for large problems.

        Args:
            Q: QUBO matrix
            variables: Sorted variable list
            var_to_idx: Variable to index mapping
            idx_to_var: Index to variable mapping

        Returns:
            AnnealingResult with greedy solution
        """
        n = len(variables)
        Q_matrix = np.zeros((n, n))
        for (i, j), val in Q.items():
            Q_matrix[var_to_idx[i], var_to_idx[j]] = val
        Q_matrix = (Q_matrix + Q_matrix.T) / 2

        # Greedy: start with all zeros, flip bits that reduce energy
        current = np.zeros(n, dtype=int)
        current_energy = 0.0

        improved = True
        iterations = 0
        max_iterations = n * 10

        while improved and iterations < max_iterations:
            improved = False
            iterations += 1

            for i in range(n):
                # Try flipping bit i
                new_state = current.copy()
                new_state[i] = 1 - new_state[i]
                new_energy = float(new_state @ Q_matrix @ new_state)

                if new_energy < current_energy - 1e-10:
                    current = new_state
                    current_energy = new_energy
                    improved = True

        bitstring = {idx_to_var[i]: int(current[i]) for i in range(n)}

        return AnnealingResult(
            samples=[
                AnnealingSample(
                    bitstring=bitstring,
                    energy=current_energy,
                    num_occurrences=1,
                )
            ],
            timing_info={"solver_time_ms": 0, "iterations": iterations},
            metadata={
                "solver": "exact",
                "method": "greedy",
                "num_variables": n,
            },
        )

    async def solve_bqm(
        self,
        linear: dict[int, float],
        quadratic: dict[tuple[int, int], float],
        offset: float = 0.0,
        num_reads: int = 100,
        **kwargs: object,
    ) -> AnnealingResult:
        """Solve BQM by converting to QUBO.

        Args:
            linear: Linear biases
            quadratic: Quadratic biases
            offset: Constant offset (added to energy)
            num_reads: Ignored
            **kwargs: Ignored

        Returns:
            AnnealingResult with solution
        """
        # Convert BQM to QUBO format
        Q: dict[tuple[int, int], float] = {}

        # Add linear terms as diagonal
        for var, bias in linear.items():
            Q[(var, var)] = bias

        # Add quadratic terms
        for (i, j), bias in quadratic.items():
            if i > j:
                i, j = j, i
            Q[(i, j)] = Q.get((i, j), 0.0) + bias

        result = await self.solve_qubo(Q, num_reads, **kwargs)

        # Add offset to energies
        if offset != 0.0:
            for sample in result.samples:
                sample.energy += offset

        return result
