# Description: Quantum Approximate Optimization Algorithm (QAOA) circuits.
# Description: Provides MaxCut encoding and QAOA circuit construction.
"""QAOA circuit builders and algorithm implementation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from qiskit_aer import AerSimulator
from scipy.optimize import minimize


@dataclass
class QAOACostFunction:
    """Cost function for QAOA encoded as graph edges.

    Represents a combinatorial optimization problem (MaxCut) as
    a graph with edges and optional weights.
    """

    edges: list[tuple[int, int]]
    num_qubits: int
    weights: Optional[list[float]] = None
    description: str = ""

    def __post_init__(self) -> None:
        """Set default weights if not provided."""
        if self.weights is None:
            self.weights = [1.0] * len(self.edges)

    def evaluate(self, bitstring: str) -> float:
        """Evaluate the cost function for a given bitstring.

        For MaxCut, returns the negative of the cut value
        (negative because we minimize in optimization).

        Args:
            bitstring: Binary string representing partition

        Returns:
            Negative of cut value (for minimization)
        """
        cut_value = 0.0
        weights = self.weights or [1.0] * len(self.edges)

        for (i, j), w in zip(self.edges, weights):
            # Extract bits (bitstring is reversed from qubit ordering)
            bi = int(bitstring[-(i + 1)]) if i < len(bitstring) else 0
            bj = int(bitstring[-(j + 1)]) if j < len(bitstring) else 0

            # Edge is cut if bits differ
            if bi != bj:
                cut_value += w

        return -cut_value  # Negative for minimization


@dataclass
class QAOAResult:
    """Result of a QAOA optimization."""

    optimal_cost: float
    optimal_parameters: list[float]
    optimal_bitstring: str
    num_iterations: int
    optimizer: str
    convergence_history: list[float] = field(default_factory=list)
    final_counts: Optional[dict[str, int]] = None


def encode_maxcut_problem(
    edges: list[tuple[int, int]],
    weights: Optional[list[float]] = None,
) -> QAOACostFunction:
    """Encode a MaxCut problem as a QAOA cost function.

    Args:
        edges: List of (i, j) tuples representing graph edges
        weights: Optional edge weights (default: all 1.0)

    Returns:
        QAOACostFunction for the MaxCut problem
    """
    # Find number of qubits from max vertex index
    num_qubits = max(max(i, j) for i, j in edges) + 1

    return QAOACostFunction(
        edges=edges,
        num_qubits=num_qubits,
        weights=weights,
        description=f"MaxCut on {num_qubits}-vertex graph with {len(edges)} edges",
    )


def build_qaoa_circuit(
    cost: QAOACostFunction,
    layers: int = 1,
) -> QuantumCircuit:
    """Build a QAOA circuit for the given cost function.

    Creates a parameterized circuit with:
    - Initial superposition (Hadamard on all qubits)
    - Alternating cost and mixer layers
    - Parameters: gamma_i for cost, beta_i for mixer

    Args:
        cost: Cost function (MaxCut problem)
        layers: Number of QAOA layers (p parameter)

    Returns:
        Parameterized QuantumCircuit
    """
    n = cost.num_qubits
    qc = QuantumCircuit(n)

    # Initial superposition
    for i in range(n):
        qc.h(i)

    weights = cost.weights or [1.0] * len(cost.edges)

    # QAOA layers
    for layer in range(layers):
        gamma = Parameter(f"gamma_{layer}")
        beta = Parameter(f"beta_{layer}")

        # Cost unitary: exp(-i * gamma * C)
        # For MaxCut: C = sum over edges (1 - Z_i Z_j) / 2
        # This gives: exp(-i * gamma * (1 - Z_i Z_j) / 2)
        for (i, j), w in zip(cost.edges, weights):
            # ZZ interaction
            qc.cx(i, j)
            qc.rz(gamma * w, j)
            qc.cx(i, j)

        # Mixer unitary: exp(-i * beta * B) where B = sum X_i
        for i in range(n):
            qc.rx(2 * beta, i)

    return qc


def _compute_expectation(
    counts: dict[str, int],
    cost: QAOACostFunction,
    shots: int,
) -> float:
    """Compute expectation value of cost function from measurement counts.

    Args:
        counts: Measurement counts from circuit execution
        cost: Cost function to evaluate
        shots: Total number of shots

    Returns:
        Expected cost value
    """
    expectation = 0.0

    for bitstring, count in counts.items():
        cost_val = cost.evaluate(bitstring)
        expectation += cost_val * count / shots

    return expectation


async def run_qaoa(
    edges: list[tuple[int, int]],
    weights: Optional[list[float]] = None,
    layers: int = 1,
    optimizer: str = "COBYLA",
    max_iterations: int = 100,
    shots: int = 1000,
    initial_parameters: Optional[list[float]] = None,
) -> QAOAResult:
    """Run the QAOA algorithm.

    Args:
        edges: Graph edges as (i, j) tuples
        weights: Optional edge weights
        layers: Number of QAOA layers (p parameter)
        optimizer: Classical optimizer ("COBYLA", "SPSA", "SLSQP")
        max_iterations: Maximum optimization iterations
        shots: Number of measurement shots per evaluation
        initial_parameters: Initial parameter values (random if None)

    Returns:
        QAOAResult with optimal cost and bitstring
    """
    # Encode problem
    cost = encode_maxcut_problem(edges, weights)

    # Build circuit
    circuit = build_qaoa_circuit(cost, layers)

    # Initialize parameters (2 per layer: gamma and beta)
    if initial_parameters is None:
        # Initialize gamma in [0, pi], beta in [0, pi/2]
        initial_parameters = []
        for _ in range(layers):
            initial_parameters.append(np.random.uniform(0, np.pi))  # gamma
            initial_parameters.append(np.random.uniform(0, np.pi / 2))  # beta

    # Set up simulator
    simulator = AerSimulator()
    convergence_history: list[float] = []

    def objective(params: np.ndarray) -> float:
        """Objective function for optimization."""
        param_list = list(params)

        # Bind parameters
        param_dict = dict(zip(circuit.parameters, param_list))
        bound_circuit = circuit.assign_parameters(param_dict)
        bound_circuit.measure_all()

        # Run simulation
        job = simulator.run(bound_circuit, shots=shots)
        result = job.result()
        counts = result.get_counts()

        # Compute expectation
        expectation = _compute_expectation(counts, cost, shots)
        convergence_history.append(expectation)

        return expectation

    # Run optimization
    if optimizer == "SPSA":
        # Simple SPSA implementation
        params = np.array(initial_parameters)
        a, c = 0.1, 0.1
        for k in range(max_iterations):
            ak = a / (k + 1) ** 0.602
            ck = c / (k + 1) ** 0.101
            delta = np.random.choice([-1, 1], size=len(params))
            y_plus = objective(params + ck * delta)
            y_minus = objective(params - ck * delta)
            gradient = (y_plus - y_minus) / (2 * ck * delta)
            params = params - ak * gradient

        optimal_params = list(params)
        optimal_cost = convergence_history[-1] if convergence_history else objective(
            params
        )
        num_iters = max_iterations
    else:
        # Use scipy optimizer
        result = minimize(
            objective,
            initial_parameters,
            method=optimizer,
            options={"maxiter": max_iterations},
        )
        optimal_params = list(result.x)
        optimal_cost = result.fun
        num_iters = result.nit if hasattr(result, "nit") else len(convergence_history)

    # Get final counts to find optimal bitstring
    param_dict = dict(zip(circuit.parameters, optimal_params))
    final_circuit = circuit.assign_parameters(param_dict)
    final_circuit.measure_all()
    final_job = simulator.run(final_circuit, shots=shots)
    final_counts = final_job.result().get_counts()

    # Find most frequent bitstring
    optimal_bitstring = max(final_counts, key=lambda k: final_counts[k])

    return QAOAResult(
        optimal_cost=optimal_cost,
        optimal_parameters=optimal_params,
        optimal_bitstring=optimal_bitstring,
        num_iterations=num_iters,
        optimizer=optimizer,
        convergence_history=convergence_history,
        final_counts=final_counts,
    )
