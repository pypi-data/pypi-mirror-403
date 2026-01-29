# Description: QUBO formulation for quantum-enhanced agent routing.
# Description: Encodes routing as optimization problem for QAOA execution.
"""QUBO formulation for quantum-enhanced agent routing."""

from __future__ import annotations

from itertools import product
from typing import TYPE_CHECKING

import numpy as np
import structlog
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    pass

from quantum_mcp.agents.base import BaseAgent
from quantum_mcp.orchestration.router import Router, RoutingDecision
from quantum_mcp.orchestration.task import Task

logger = structlog.get_logger()


class QUBOFormulation:
    """Quadratic Unconstrained Binary Optimization formulation.

    Represents an optimization problem of the form:
        minimize x^T Q x

    where x is a binary vector and Q is the QUBO matrix.
    """

    def __init__(self, n_agents: int) -> None:
        """Initialize QUBO formulation.

        Args:
            n_agents: Number of binary variables (agents)
        """
        self.n_agents = n_agents
        self._Q = np.zeros((n_agents, n_agents), dtype=np.float64)

    def set_linear_terms(self, scores: list[float]) -> None:
        """Set linear (diagonal) terms from agent scores.

        For maximization, we negate the scores since QUBO minimizes.

        Args:
            scores: Score for each agent (higher is better)
        """
        for i, score in enumerate(scores):
            self._Q[i, i] = -score  # Negate for minimization

    def add_selection_constraint(
        self,
        target: int,
        penalty: float = 10.0,
    ) -> None:
        """Add constraint for number of selected agents.

        Encodes (sum(x_i) - target)^2 as penalty term.
        Expanding: sum(x_i^2) + 2*sum_{i<j}(x_i*x_j) - 2*target*sum(x_i) + target^2

        Since x_i is binary, x_i^2 = x_i, so this becomes:
        - Linear terms: (1 - 2*target) * sum(x_i)
        - Quadratic terms: 2 * sum_{i<j}(x_i*x_j)
        - Constant: target^2 (ignored, doesn't affect optimization)

        Args:
            target: Target number of agents to select
            penalty: Penalty weight for constraint violation
        """
        # Linear terms: coefficient is (1 - 2*target) for each x_i
        for i in range(self.n_agents):
            self._Q[i, i] += penalty * (1 - 2 * target)

        # Quadratic terms: coefficient is 2 for each x_i*x_j pair
        # In x^T Q x with symmetric Q, off-diagonal (i,j) contributes 2*Q[i,j]*x_i*x_j
        # So we need Q[i,j] = penalty to get 2*penalty contribution
        for i in range(self.n_agents):
            for j in range(i + 1, self.n_agents):
                self._Q[i, j] += penalty
                self._Q[j, i] += penalty

    def add_range_constraint(
        self,
        min_agents: int,
        max_agents: int,
        penalty: float = 10.0,
    ) -> None:
        """Add constraint for range of selected agents.

        For exact target (min == max), use equality constraint.
        For range, we encode the average as target.

        Args:
            min_agents: Minimum agents to select
            max_agents: Maximum agents to select
            penalty: Penalty weight
        """
        if min_agents == max_agents:
            self.add_selection_constraint(min_agents, penalty)
        else:
            # Use target at ceiling of average to prefer selecting more
            target = (min_agents + max_agents + 1) // 2
            self.add_selection_constraint(target, penalty)

    def get_qubo_matrix(self) -> np.ndarray:
        """Get the QUBO matrix Q.

        Returns:
            Symmetric QUBO matrix
        """
        # Ensure symmetry
        return (self._Q + self._Q.T) / 2

    def calculate_energy(self, x: np.ndarray) -> float:
        """Calculate energy (objective value) for a binary vector.

        Args:
            x: Binary selection vector

        Returns:
            Energy value (lower is better)
        """
        Q = self.get_qubo_matrix()
        return float(x @ Q @ x)


class RouteQUBO:
    """QUBO formulation specifically for routing problems.

    Wraps QUBOFormulation with agent-specific semantics.
    """

    def __init__(
        self,
        formulation: QUBOFormulation,
        agent_ids: list[str],
    ) -> None:
        """Initialize route QUBO.

        Args:
            formulation: Underlying QUBO formulation
            agent_ids: List of agent IDs in order
        """
        self.formulation = formulation
        self.agent_ids = agent_ids

    @property
    def n_agents(self) -> int:
        """Number of agents in the problem."""
        return self.formulation.n_agents

    @classmethod
    def from_scores(
        cls,
        agent_ids: list[str],
        scores: dict[str, float],
        min_agents: int = 1,
        max_agents: int = 1,
        penalty: float = 10.0,
    ) -> "RouteQUBO":
        """Create RouteQUBO from agent scores.

        Args:
            agent_ids: Ordered list of agent IDs
            scores: Score for each agent (by ID)
            min_agents: Minimum agents to select
            max_agents: Maximum agents to select
            penalty: Constraint penalty weight

        Returns:
            Configured RouteQUBO
        """
        n = len(agent_ids)
        formulation = QUBOFormulation(n_agents=n)

        # Set linear terms from scores
        score_list = [scores.get(aid, 0.0) for aid in agent_ids]
        formulation.set_linear_terms(score_list)

        # Add selection constraint
        if min_agents == max_agents:
            formulation.add_selection_constraint(min_agents, penalty)
        else:
            formulation.add_range_constraint(min_agents, max_agents, penalty)

        return cls(formulation, agent_ids)

    def decode_solution(self, solution: np.ndarray) -> list[str]:
        """Decode binary solution to agent IDs.

        Args:
            solution: Binary vector of selections

        Returns:
            List of selected agent IDs
        """
        selected = []
        for i, x in enumerate(solution):
            if x > 0.5:  # Handle float solutions
                selected.append(self.agent_ids[i])
        return selected

    def solve_classical(self) -> tuple[np.ndarray, float]:
        """Solve QUBO via classical brute-force enumeration.

        For small problems (< 20 agents), enumerate all solutions.

        Returns:
            Tuple of (best solution vector, best energy)
        """
        n = self.n_agents

        if n > 20:
            # Too large for brute force, use greedy
            return self._solve_greedy()

        best_solution = None
        best_energy = float("inf")

        # Enumerate all 2^n binary vectors
        for bits in product([0, 1], repeat=n):
            x = np.array(bits, dtype=np.float64)
            energy = self.formulation.calculate_energy(x)

            if energy < best_energy:
                best_energy = energy
                best_solution = x

        return best_solution, best_energy

    def _solve_greedy(self) -> tuple[np.ndarray, float]:
        """Greedy solver for larger problems.

        Returns:
            Tuple of (solution vector, energy)
        """
        Q = self.formulation.get_qubo_matrix()
        n = self.n_agents

        # Start with diagonal (linear) terms
        diag = np.diag(Q)

        # Greedy: select agents with most negative diagonal
        x = np.zeros(n)
        selected_count = 0
        target = n // 2  # Rough target

        for _ in range(target):
            # Find best unselected agent
            best_idx = -1
            best_delta = float("inf")

            for i in range(n):
                if x[i] == 0:
                    # Calculate energy delta of selecting i
                    delta = Q[i, i]
                    for j in range(n):
                        if x[j] == 1:
                            delta += 2 * Q[i, j]

                    if delta < best_delta:
                        best_delta = delta
                        best_idx = i

            if best_idx >= 0:
                x[best_idx] = 1
                selected_count += 1

        energy = self.formulation.calculate_energy(x)
        return x, energy


class QUBORouter(Router):
    """Router that uses QUBO formulation for agent selection.

    Encodes the routing problem as a QUBO and solves it
    classically (with future support for QAOA).
    """

    def __init__(
        self,
        agents: list[BaseAgent],
        penalty: float = 10.0,
    ) -> None:
        """Initialize QUBO router.

        Args:
            agents: Available agents
            penalty: Constraint penalty weight
        """
        super().__init__(agents)
        self._penalty = penalty
        self._logger = logger.bind(router="QUBORouter")

    async def route(self, task: Task) -> RoutingDecision:
        """Route task using QUBO optimization.

        Args:
            task: Task to route

        Returns:
            RoutingDecision with selected agents
        """
        # Calculate scores for each agent
        scores = self._calculate_scores(task)

        # Build QUBO
        agent_ids = [a.agent_id for a in self._agents]
        qubo = RouteQUBO.from_scores(
            agent_ids=agent_ids,
            scores=scores,
            min_agents=task.min_agents,
            max_agents=task.max_agents,
            penalty=self._penalty,
        )

        # Solve (classically for now, QAOA in future)
        solution, energy = qubo.solve_classical()
        selected = qubo.decode_solution(solution)

        self._logger.debug(
            "QUBO routing decision",
            task_id=task.task_id,
            selected=selected,
            energy=energy,
        )

        return RoutingDecision(
            task_id=task.task_id,
            selected_agents=selected,
            strategy="qubo",
            scores=scores,
            reasoning=f"QUBO optimization with energy={energy:.4f}",
        )

    def _calculate_scores(self, task: Task) -> dict[str, float]:
        """Calculate capability scores for each agent.

        Args:
            task: Task with requirements

        Returns:
            Dictionary mapping agent IDs to scores
        """
        scores = {}

        for agent in self._agents:
            score = 0.0

            # Base score
            if agent.get_capabilities():
                score += 0.1

            # Capability matching
            if task.required_capabilities:
                matches = sum(
                    1
                    for cap in task.required_capabilities
                    if agent.has_capability(cap)
                )
                score += matches / len(task.required_capabilities) * 0.5

            # Provider preference
            if task.preferred_providers:
                if agent.provider in task.preferred_providers:
                    score += 0.3

            # Capability confidence
            for cap in agent.get_capabilities():
                if cap.name in (task.required_capabilities or []):
                    score += cap.confidence * 0.1

            scores[agent.agent_id] = min(score, 1.0)

        return scores

    def get_qubo(self, task: Task) -> RouteQUBO:
        """Get the QUBO formulation for a task.

        Args:
            task: Task to formulate

        Returns:
            RouteQUBO ready for solving
        """
        scores = self._calculate_scores(task)
        agent_ids = [a.agent_id for a in self._agents]

        return RouteQUBO.from_scores(
            agent_ids=agent_ids,
            scores=scores,
            min_agents=task.min_agents,
            max_agents=task.max_agents,
            penalty=self._penalty,
        )
