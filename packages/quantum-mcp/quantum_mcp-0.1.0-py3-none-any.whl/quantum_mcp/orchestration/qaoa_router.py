# Description: QAOA-based quantum router for agent selection.
# Description: Converts QUBO to Ising Hamiltonian and executes QAOA circuit.
"""QAOA-based quantum router for agent selection."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import structlog
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from qiskit_aer import AerSimulator
from scipy.optimize import minimize

if TYPE_CHECKING:
    pass

from quantum_mcp.agents.base import BaseAgent
from quantum_mcp.circuits.qaoa import QAOACostFunction
from quantum_mcp.orchestration.qubo import QUBORouter, RouteQUBO
from quantum_mcp.orchestration.router import RoutingDecision
from quantum_mcp.orchestration.task import Task

logger = structlog.get_logger()


def qubo_to_ising(Q: np.ndarray) -> tuple[dict[tuple[int, int], float], dict[int, float], float]:
    """Convert QUBO matrix to Ising Hamiltonian.

    QUBO: minimize x^T Q x where x in {0,1}^n
    Ising: E = offset + sum_i h_i s_i + sum_ij J_ij s_i s_j where s in {-1,+1}^n

    Mapping: x = (1 - s) / 2
    This ensures that:
    - s = +1 (|0> state, Z=+1) corresponds to x = 0 (not selected)
    - s = -1 (|1> state, Z=-1) corresponds to x = 1 (selected)

    This matches quantum convention where measurement bit '1' means selected.

    Args:
        Q: Symmetric QUBO matrix

    Returns:
        Tuple of (J coupling dict, h field dict, constant offset)
    """
    n = Q.shape[0]

    # Ensure symmetry
    Q = (Q + Q.T) / 2

    J: dict[tuple[int, int], float] = {}
    h: dict[int, float] = {}
    offset = 0.0

    # With x = (1-s)/2:
    # Q[i,i] * x_i = Q[i,i] * (1-s_i)/2 = Q[i,i]/2 - Q[i,i]*s_i/2
    for i in range(n):
        h[i] = -Q[i, i] / 2  # Note negative sign
        offset += Q[i, i] / 2

    # Off-diagonal: 2*Q[i,j] * x_i * x_j = Q[i,j] * (1-s_i)(1-s_j)/2
    # = Q[i,j]/2 * (1 - s_i - s_j + s_i*s_j)
    for i in range(n):
        for j in range(i + 1, n):
            if abs(Q[i, j]) > 1e-10:
                # Constant term
                offset += Q[i, j] / 2

                # Linear terms (negative signs)
                h[i] = h.get(i, 0) - Q[i, j] / 2
                h[j] = h.get(j, 0) - Q[i, j] / 2

                # Quadratic term
                J[(i, j)] = Q[i, j] / 2

    return J, h, offset


def ising_to_qaoa_cost(
    J: dict[tuple[int, int], float],
    h: dict[int, float],
    n_qubits: int,
) -> QAOACostFunction:
    """Convert Ising Hamiltonian to QAOA cost function.

    The QAOA cost function uses edges and weights to encode
    ZZ interactions. For h (single-qubit) terms, we create
    auxiliary handling in the circuit builder.

    Args:
        J: Coupling terms {(i,j): J_ij}
        h: Field terms {i: h_i}
        n_qubits: Number of qubits

    Returns:
        QAOACostFunction compatible with QAOA circuit builder
    """
    edges = list(J.keys())
    weights = [J[e] for e in edges]

    return QAOACostFunction(
        edges=edges,
        num_qubits=n_qubits,
        weights=weights if weights else None,
        description=f"QUBO-derived Ising on {n_qubits} qubits",
    )


def build_qubo_qaoa_circuit(
    J: dict[tuple[int, int], float],
    h: dict[int, float],
    n_qubits: int,
    layers: int = 1,
) -> QuantumCircuit:
    """Build QAOA circuit for QUBO-derived Ising Hamiltonian.

    Creates parameterized circuit with:
    - Initial superposition
    - Cost unitary from ZZ (J terms) and Z (h terms)
    - Mixer unitary from X rotations

    Args:
        J: Coupling terms
        h: Field terms
        n_qubits: Number of qubits
        layers: Number of QAOA layers

    Returns:
        Parameterized QuantumCircuit
    """
    qc = QuantumCircuit(n_qubits)

    # Initial superposition
    for i in range(n_qubits):
        qc.h(i)

    for layer in range(layers):
        gamma = Parameter(f"gamma_{layer}")
        beta = Parameter(f"beta_{layer}")

        # Cost unitary: exp(-i * gamma * H_C)
        # H_C = sum_ij J_ij Z_i Z_j + sum_i h_i Z_i

        # ZZ interactions from J terms
        for (i, j), Jij in J.items():
            if abs(Jij) > 1e-10:
                qc.cx(i, j)
                qc.rz(2 * gamma * Jij, j)
                qc.cx(i, j)

        # Z terms from h
        for i, hi in h.items():
            if abs(hi) > 1e-10:
                qc.rz(2 * gamma * hi, i)

        # Mixer unitary: exp(-i * beta * sum_i X_i)
        for i in range(n_qubits):
            qc.rx(2 * beta, i)

    return qc


class QAOARouter(QUBORouter):
    """Router that uses QAOA for quantum-enhanced agent selection.

    Extends QUBORouter to solve the QUBO via QAOA instead of
    classical brute-force enumeration.
    """

    def __init__(
        self,
        agents: list[BaseAgent],
        penalty: float = 10.0,
        layers: int = 1,
        shots: int = 1000,
        optimizer: str = "COBYLA",
        max_iterations: int = 50,
    ) -> None:
        """Initialize QAOA router.

        Args:
            agents: Available agents
            penalty: Constraint penalty weight
            layers: Number of QAOA layers (p parameter)
            shots: Number of measurement shots
            optimizer: Classical optimizer name
            max_iterations: Max optimization iterations
        """
        super().__init__(agents, penalty)
        self.layers = layers
        self.shots = shots
        self.optimizer = optimizer
        self.max_iterations = max_iterations
        self._logger = logger.bind(router="QAOARouter")

    async def route(self, task: Task) -> RoutingDecision:
        """Route task using QAOA optimization.

        Args:
            task: Task to route

        Returns:
            RoutingDecision with selected agents
        """
        # Get QUBO formulation
        qubo = self.get_qubo(task)
        Q = qubo.formulation.get_qubo_matrix()

        # Convert to Ising
        J, h, offset = qubo_to_ising(Q)

        # Build QAOA circuit
        circuit = build_qubo_qaoa_circuit(
            J, h, n_qubits=qubo.n_agents, layers=self.layers
        )

        # Run QAOA optimization
        optimal_params, optimal_cost, final_counts = await self._run_qaoa(
            circuit, J, h, offset, qubo.n_agents
        )

        # Decode best bitstring (reverse because qiskit returns qubit n-1 first)
        best_bitstring = max(final_counts, key=lambda k: final_counts[k])
        # Convert bitstring to selection vector (reversed to match qubit ordering)
        solution = np.array([int(b) for b in reversed(best_bitstring)], dtype=float)
        selected = qubo.decode_solution(solution)

        # Get scores for post-processing
        scores = self._calculate_scores(task)
        agent_ids = [a.agent_id for a in self._agents]

        # Enforce constraints via post-processing (QAOA is approximate)
        selected = self._enforce_constraints(
            selected=selected,
            scores=scores,
            agent_ids=agent_ids,
            min_agents=task.min_agents,
            max_agents=task.max_agents,
        )

        self._logger.debug(
            "QAOA routing decision",
            task_id=task.task_id,
            selected=selected,
            best_bitstring=best_bitstring,
            optimal_cost=optimal_cost,
            layers=self.layers,
        )

        return RoutingDecision(
            task_id=task.task_id,
            selected_agents=selected,
            strategy="qaoa",
            scores=scores,
            reasoning=f"QAOA optimization (p={self.layers}) with cost={optimal_cost:.4f}",
        )

    async def _run_qaoa(
        self,
        circuit: QuantumCircuit,
        J: dict[tuple[int, int], float],
        h: dict[int, float],
        offset: float,
        n_qubits: int,
    ) -> tuple[list[float], float, dict[str, int]]:
        """Run QAOA optimization loop.

        Args:
            circuit: Parameterized QAOA circuit
            J: Ising coupling terms
            h: Ising field terms
            offset: Energy offset
            n_qubits: Number of qubits

        Returns:
            Tuple of (optimal parameters, optimal cost, final counts)
        """
        simulator = AerSimulator()

        def evaluate_cost(bitstring: str) -> float:
            """Evaluate Ising cost for a bitstring."""
            # Convert bitstring to spins
            # Quantum convention: bit '1' -> |1> -> Z eigenvalue -1
            # Our mapping: x = (1-s)/2, so bit '1' (s=-1) -> x=1 (selected)
            # Note: bitstring is in reverse order (qubit 0 is last char)
            spins = [-1 if b == "1" else 1 for b in reversed(bitstring)]

            # Ising energy: E = offset + sum h_i s_i + sum J_ij s_i s_j
            cost = offset
            for i, hi in h.items():
                cost += hi * spins[i]
            for (i, j), Jij in J.items():
                cost += Jij * spins[i] * spins[j]

            return cost

        def objective(params: np.ndarray) -> float:
            """Compute expected cost for given parameters."""
            param_dict = dict(zip(circuit.parameters, list(params)))
            bound_circuit = circuit.assign_parameters(param_dict)
            bound_circuit.measure_all()

            job = simulator.run(bound_circuit, shots=self.shots)
            counts = job.result().get_counts()

            # Compute expectation
            expectation = 0.0
            for bitstring, count in counts.items():
                cost = evaluate_cost(bitstring)
                expectation += cost * count / self.shots

            return expectation

        # Initialize parameters
        initial_params = []
        for _ in range(self.layers):
            initial_params.append(np.random.uniform(0, np.pi))  # gamma
            initial_params.append(np.random.uniform(0, np.pi / 2))  # beta

        # Optimize
        result = minimize(
            objective,
            initial_params,
            method=self.optimizer,
            options={"maxiter": self.max_iterations},
        )

        optimal_params = list(result.x)
        optimal_cost = result.fun

        # Get final counts
        param_dict = dict(zip(circuit.parameters, optimal_params))
        final_circuit = circuit.assign_parameters(param_dict)
        final_circuit.measure_all()
        final_job = simulator.run(final_circuit, shots=self.shots)
        final_counts = final_job.result().get_counts()

        return optimal_params, optimal_cost, final_counts

    def _enforce_constraints(
        self,
        selected: list[str],
        scores: dict[str, float],
        agent_ids: list[str],
        min_agents: int,
        max_agents: int,
    ) -> list[str]:
        """Enforce min/max agent constraints via post-processing.

        QAOA is an approximate algorithm that may return solutions
        violating soft constraints. This method ensures the final
        selection satisfies the hard constraints.

        Args:
            selected: Agents selected by QAOA
            scores: Score for each agent
            agent_ids: All available agent IDs
            min_agents: Minimum agents required
            max_agents: Maximum agents allowed

        Returns:
            Adjusted selection satisfying constraints
        """
        # Enforce max_agents: keep only top-scoring agents
        if len(selected) > max_agents:
            selected = sorted(selected, key=lambda x: scores.get(x, 0), reverse=True)
            selected = selected[:max_agents]
            self._logger.debug(
                "Enforced max_agents constraint",
                max_agents=max_agents,
                trimmed_to=len(selected),
            )

        # Enforce min_agents: add highest-scoring unselected agents
        if len(selected) < min_agents:
            unselected = [a for a in agent_ids if a not in selected]
            unselected = sorted(unselected, key=lambda x: scores.get(x, 0), reverse=True)
            needed = min_agents - len(selected)
            selected.extend(unselected[:needed])
            self._logger.debug(
                "Enforced min_agents constraint",
                min_agents=min_agents,
                added=needed,
            )

        return selected

    def get_qaoa_circuit(self, task: Task) -> QuantumCircuit:
        """Get the QAOA circuit for a task.

        Args:
            task: Task to build circuit for

        Returns:
            Parameterized QAOA QuantumCircuit
        """
        qubo = self.get_qubo(task)
        Q = qubo.formulation.get_qubo_matrix()
        J, h, _ = qubo_to_ising(Q)

        return build_qubo_qaoa_circuit(
            J, h, n_qubits=qubo.n_agents, layers=self.layers
        )
