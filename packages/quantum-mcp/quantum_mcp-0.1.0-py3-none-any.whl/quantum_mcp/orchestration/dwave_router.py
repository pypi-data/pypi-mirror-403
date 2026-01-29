# Description: D-Wave annealing-based router for agent selection.
# Description: Directly solves QUBO on quantum annealer without gate compilation.
"""D-Wave quantum annealing router for agent selection."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import structlog

from quantum_mcp.backends.annealing import AnnealingBackend
from quantum_mcp.backends.factory import create_annealing_backend
from quantum_mcp.orchestration.qubo import QUBORouter, RouteQUBO
from quantum_mcp.orchestration.router import RoutingDecision
from quantum_mcp.orchestration.task import Task

if TYPE_CHECKING:
    from quantum_mcp.agents.base import BaseAgent

logger = structlog.get_logger()


class DWaveRouter(QUBORouter):
    """Router that uses D-Wave quantum annealing for agent selection.

    Extends QUBORouter to solve QUBO directly on D-Wave hardware
    instead of classical brute-force or QAOA gate-based simulation.

    Research shows quantum annealing outperforms QAOA for pure
    optimization problems, making this the preferred approach
    when D-Wave hardware is available.
    """

    def __init__(
        self,
        agents: list["BaseAgent"],
        penalty: float = 10.0,
        num_reads: int = 100,
        backend: Optional[AnnealingBackend] = None,
        backend_type: str = "auto",
    ) -> None:
        """Initialize D-Wave router.

        Args:
            agents: Available agents for routing
            penalty: Constraint penalty weight for QUBO
            num_reads: Number of annealing samples to collect
            backend: Pre-configured annealing backend (optional)
            backend_type: Backend type if not provided:
                - "dwave": Use D-Wave hardware
                - "exact": Use classical ExactSolver
                - "auto": Try D-Wave, fall back to exact
        """
        super().__init__(agents, penalty)
        self._num_reads = num_reads
        self._backend = backend
        self._backend_type = backend_type
        self._logger = logger.bind(router="DWaveRouter")

    async def _ensure_backend(self) -> AnnealingBackend:
        """Lazily initialize and connect to backend.

        Returns:
            Connected AnnealingBackend
        """
        if self._backend is None:
            self._logger.debug("Creating annealing backend", type=self._backend_type)
            self._backend = create_annealing_backend(self._backend_type)

        if not self._backend.is_connected:
            await self._backend.connect()

        return self._backend

    async def route(self, task: Task) -> RoutingDecision:
        """Route task using D-Wave quantum annealing.

        Args:
            task: Task to route

        Returns:
            RoutingDecision with selected agents
        """
        # Get QUBO formulation from parent class
        qubo = self.get_qubo(task)

        # Convert QUBO matrix to dict format for D-Wave
        Q_dict = self._matrix_to_qubo_dict(qubo)

        # Ensure backend is connected
        backend = await self._ensure_backend()

        self._logger.debug(
            "Submitting to annealing backend",
            backend=backend.backend_id,
            num_reads=self._num_reads,
            num_agents=qubo.n_agents,
        )

        # Solve on annealing backend
        result = await backend.solve_qubo(Q_dict, num_reads=self._num_reads)

        # Decode best solution
        best = result.best_sample
        selected = self._decode_bitstring(best.bitstring, qubo.agent_ids)

        # Calculate scores for response
        scores = self._calculate_scores(task)

        self._logger.debug(
            "D-Wave routing decision",
            task_id=task.task_id,
            selected=selected,
            energy=best.energy,
            num_reads=self._num_reads,
            backend=backend.backend_id,
            num_samples=result.num_samples,
        )

        return RoutingDecision(
            task_id=task.task_id,
            selected_agents=selected,
            strategy="dwave",
            scores=scores,
            reasoning=(
                f"D-Wave annealing ({backend.backend_id}) with "
                f"energy={best.energy:.4f}, "
                f"num_reads={self._num_reads}, "
                f"samples={result.num_samples}"
            ),
        )

    def _matrix_to_qubo_dict(
        self,
        qubo: RouteQUBO,
    ) -> dict[tuple[int, int], float]:
        """Convert QUBO matrix to dict format for D-Wave.

        D-Wave expects {(i, j): weight} where i <= j for upper triangle.

        Args:
            qubo: RouteQUBO with formulation

        Returns:
            QUBO as dict for D-Wave sampler
        """
        Q = qubo.formulation.get_qubo_matrix()
        Q_dict: dict[tuple[int, int], float] = {}
        n = Q.shape[0]

        for i in range(n):
            for j in range(i, n):
                weight = Q[i, j]
                if i != j:
                    # Off-diagonal: add symmetric part
                    weight += Q[j, i]

                if abs(weight) > 1e-10:
                    Q_dict[(i, j)] = weight

        return Q_dict

    def _decode_bitstring(
        self,
        bitstring: dict[int, int],
        agent_ids: list[str],
    ) -> list[str]:
        """Decode D-Wave bitstring to selected agent IDs.

        Args:
            bitstring: D-Wave solution {variable_idx: 0 or 1}
            agent_ids: List of agent IDs in variable order

        Returns:
            List of selected agent IDs
        """
        selected = []
        for i, agent_id in enumerate(agent_ids):
            if bitstring.get(i, 0) == 1:
                selected.append(agent_id)
        return selected

    async def close(self) -> None:
        """Close the backend connection."""
        if self._backend is not None and self._backend.is_connected:
            await self._backend.disconnect()
            self._logger.debug("Backend disconnected")
