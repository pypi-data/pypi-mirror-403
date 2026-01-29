# Description: Variational Quantum Eigensolver (VQE) circuit builders.
# Description: Provides ansatz construction, Hamiltonian encoding, and optimization.
"""VQE circuit builders and algorithm implementation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from qiskit_aer import AerSimulator
from scipy.optimize import minimize


@dataclass
class HamiltonianTerm:
    """A term in a Hamiltonian as a Pauli string with coefficient."""

    coefficient: float
    pauli_string: str  # e.g., "IZZI", "XXXX"


@dataclass
class MolecularHamiltonian:
    """Molecular Hamiltonian represented as sum of Pauli terms."""

    terms: list[HamiltonianTerm]
    num_qubits: int
    description: str = ""

    def evaluate(self, counts: dict[str, int], shots: int) -> float:
        """Evaluate expectation value from measurement counts.

        Args:
            counts: Measurement counts from circuit execution
            shots: Total number of shots

        Returns:
            Expectation value of the Hamiltonian
        """
        energy = 0.0

        for term in self.terms:
            if all(p == "I" for p in term.pauli_string):
                # Identity term contributes directly
                energy += term.coefficient
            else:
                # Compute expectation value for this Pauli string
                exp_val = self._pauli_expectation(term.pauli_string, counts, shots)
                energy += term.coefficient * exp_val

        return energy

    def _pauli_expectation(
        self, pauli_string: str, counts: dict[str, int], shots: int
    ) -> float:
        """Compute expectation value for a Pauli string."""
        expectation = 0.0

        for bitstring, count in counts.items():
            # Compute parity for non-identity positions
            parity = 1
            for i, pauli in enumerate(reversed(pauli_string)):
                if pauli in ("Z", "X", "Y"):
                    bit = int(bitstring[-(i + 1)]) if i < len(bitstring) else 0
                    parity *= (-1) ** bit

            expectation += parity * count / shots

        return expectation


@dataclass
class VQEResult:
    """Result of a VQE optimization."""

    optimal_energy: float
    optimal_parameters: list[float]
    num_iterations: int
    optimizer: str
    convergence_history: list[float] = field(default_factory=list)
    final_counts: Optional[dict[str, int]] = None


def build_ry_ansatz(num_qubits: int, depth: int = 1) -> QuantumCircuit:
    """Build a simple RY rotation ansatz.

    Creates a parameterized circuit with RY rotations on each qubit
    followed by a linear entanglement pattern.

    Args:
        num_qubits: Number of qubits
        depth: Number of ansatz layers

    Returns:
        Parameterized QuantumCircuit
    """
    qc = QuantumCircuit(num_qubits)
    param_idx = 0

    for layer in range(depth):
        # RY rotation layer
        for qubit in range(num_qubits):
            theta = Parameter(f"θ_{layer}_{qubit}")
            qc.ry(theta, qubit)
            param_idx += 1

        # Entanglement layer (linear)
        for qubit in range(num_qubits - 1):
            qc.cx(qubit, qubit + 1)

    # Final rotation layer
    for qubit in range(num_qubits):
        theta = Parameter(f"θ_{depth}_{qubit}")
        qc.ry(theta, qubit)

    return qc


def build_hardware_efficient_ansatz(
    num_qubits: int,
    depth: int = 2,
    entanglement: str = "linear",
) -> QuantumCircuit:
    """Build a hardware-efficient ansatz.

    Creates a parameterized circuit with alternating rotation and
    entanglement layers suitable for NISQ devices.

    Args:
        num_qubits: Number of qubits
        depth: Number of ansatz layers
        entanglement: Entanglement pattern ("linear", "full", "circular")

    Returns:
        Parameterized QuantumCircuit
    """
    qc = QuantumCircuit(num_qubits)

    for layer in range(depth):
        # Rotation layer: RY and RZ on each qubit
        for qubit in range(num_qubits):
            qc.ry(Parameter(f"ry_{layer}_{qubit}"), qubit)
            qc.rz(Parameter(f"rz_{layer}_{qubit}"), qubit)

        # Entanglement layer
        if entanglement == "linear":
            for qubit in range(num_qubits - 1):
                qc.cx(qubit, qubit + 1)
        elif entanglement == "full":
            for i in range(num_qubits):
                for j in range(i + 1, num_qubits):
                    qc.cx(i, j)
        elif entanglement == "circular":
            for qubit in range(num_qubits - 1):
                qc.cx(qubit, qubit + 1)
            if num_qubits > 2:
                qc.cx(num_qubits - 1, 0)

    # Final rotation layer
    for qubit in range(num_qubits):
        qc.ry(Parameter(f"ry_{depth}_{qubit}"), qubit)

    return qc


def encode_h2_hamiltonian(bond_distance: float = 0.735) -> MolecularHamiltonian:
    """Encode the H2 molecule Hamiltonian.

    Uses a simplified 2-qubit encoding of the H2 molecule at
    the given bond distance. Coefficients are pre-computed for
    common bond distances.

    Args:
        bond_distance: H-H bond distance in Angstroms

    Returns:
        MolecularHamiltonian for H2
    """
    # Pre-computed coefficients for H2 at various bond distances
    # These are from Jordan-Wigner transformation of the molecular Hamiltonian
    h2_coefficients = {
        0.5: {"II": -0.4804, "IZ": 0.3435, "ZI": -0.4347, "ZZ": 0.5716, "XX": 0.0910},
        0.735: {"II": -0.8105, "IZ": 0.1721, "ZI": -0.2257, "ZZ": 0.1716, "XX": 0.0453},
        1.0: {"II": -0.9374, "IZ": 0.0934, "ZI": -0.0934, "ZZ": 0.0934, "XX": 0.0334},
        1.5: {"II": -0.9981, "IZ": 0.0364, "ZI": -0.0364, "ZZ": 0.0364, "XX": 0.0242},
    }

    # Find closest pre-computed distance
    distances = list(h2_coefficients.keys())
    closest = min(distances, key=lambda d: abs(d - bond_distance))
    coeffs = h2_coefficients[closest]

    terms = [
        HamiltonianTerm(coefficient=coeffs["II"], pauli_string="II"),
        HamiltonianTerm(coefficient=coeffs["IZ"], pauli_string="IZ"),
        HamiltonianTerm(coefficient=coeffs["ZI"], pauli_string="ZI"),
        HamiltonianTerm(coefficient=coeffs["ZZ"], pauli_string="ZZ"),
        HamiltonianTerm(coefficient=coeffs["XX"], pauli_string="XX"),
    ]

    return MolecularHamiltonian(
        terms=terms,
        num_qubits=2,
        description=f"H2 molecule at {closest} Angstrom bond distance",
    )


def _create_measurement_circuit(
    ansatz: QuantumCircuit,
    parameters: list[float],
    pauli_string: str,
) -> QuantumCircuit:
    """Create measurement circuit for a Pauli string.

    Args:
        ansatz: Parameterized ansatz circuit
        parameters: Parameter values to bind
        pauli_string: Pauli string to measure

    Returns:
        Circuit with basis rotations and measurements
    """
    # Bind parameters
    param_dict = dict(zip(ansatz.parameters, parameters))
    qc = ansatz.assign_parameters(param_dict)

    # Add classical register
    qc.add_register(qc._create_creg(qc.num_qubits, "meas"))

    # Add basis rotations for X and Y measurements
    for i, pauli in enumerate(reversed(pauli_string)):
        if pauli == "X":
            qc.h(i)
        elif pauli == "Y":
            qc.sdg(i)
            qc.h(i)

    # Measure all qubits
    qc.measure_all(add_bits=False)

    return qc


async def run_vqe(
    num_qubits: int = 2,
    ansatz_type: str = "ry",
    depth: int = 1,
    hamiltonian_type: str = "h2",
    optimizer: str = "COBYLA",
    max_iterations: int = 100,
    shots: int = 1000,
    initial_parameters: Optional[list[float]] = None,
) -> VQEResult:
    """Run the VQE algorithm.

    Args:
        num_qubits: Number of qubits
        ansatz_type: Type of ansatz ("ry", "hardware_efficient")
        depth: Ansatz circuit depth
        hamiltonian_type: Type of Hamiltonian ("h2", "custom")
        optimizer: Classical optimizer ("COBYLA", "SPSA", "SLSQP")
        max_iterations: Maximum optimization iterations
        shots: Number of measurement shots per evaluation
        initial_parameters: Initial parameter values (random if None)

    Returns:
        VQEResult with optimal energy and parameters
    """
    # Build ansatz
    if ansatz_type == "ry":
        ansatz = build_ry_ansatz(num_qubits, depth)
    elif ansatz_type == "hardware_efficient":
        ansatz = build_hardware_efficient_ansatz(num_qubits, depth)
    else:
        raise ValueError(f"Unknown ansatz type: {ansatz_type}")

    # Build Hamiltonian
    if hamiltonian_type == "h2":
        hamiltonian = encode_h2_hamiltonian()
    else:
        # Default to simple ZZ Hamiltonian
        hamiltonian = MolecularHamiltonian(
            terms=[
                HamiltonianTerm(coefficient=-1.0, pauli_string="Z" * num_qubits),
                HamiltonianTerm(coefficient=0.5, pauli_string="I" * num_qubits),
            ],
            num_qubits=num_qubits,
        )

    # Initialize parameters
    num_params = len(ansatz.parameters)
    if initial_parameters is None:
        initial_parameters = list(np.random.uniform(0, 2 * np.pi, num_params))

    # Set up simulator
    simulator = AerSimulator()
    convergence_history: list[float] = []

    def objective(params: np.ndarray) -> float:
        """Objective function for optimization."""
        param_list = list(params)

        # Create measurement circuit
        param_dict = dict(zip(ansatz.parameters, param_list))
        bound_circuit = ansatz.assign_parameters(param_dict)
        bound_circuit.measure_all()

        # Run simulation
        job = simulator.run(bound_circuit, shots=shots)
        result = job.result()
        counts = result.get_counts()

        # Evaluate energy
        energy = hamiltonian.evaluate(counts, shots)
        convergence_history.append(energy)

        return energy

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
        optimal_energy = convergence_history[-1] if convergence_history else objective(params)
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
        optimal_energy = result.fun
        num_iters = result.nit if hasattr(result, "nit") else len(convergence_history)

    # Get final counts
    param_dict = dict(zip(ansatz.parameters, optimal_params))
    final_circuit = ansatz.assign_parameters(param_dict)
    final_circuit.measure_all()
    final_job = simulator.run(final_circuit, shots=shots)
    final_counts = final_job.result().get_counts()

    return VQEResult(
        optimal_energy=optimal_energy,
        optimal_parameters=optimal_params,
        num_iterations=num_iters,
        optimizer=optimizer,
        convergence_history=convergence_history,
        final_counts=final_counts,
    )
