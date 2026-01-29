# Description: Local quantum simulation tools.
# Description: Provides MCP tools for running quantum circuits locally.
"""Local quantum simulation MCP tools."""

from __future__ import annotations

import json
from typing import Optional

from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator


def _create_bell_circuit(num_qubits: int = 2) -> QuantumCircuit:
    """Create a Bell state circuit.

    Args:
        num_qubits: Number of qubits (minimum 2)

    Returns:
        Bell state circuit
    """
    n = max(2, num_qubits)
    qc = QuantumCircuit(n, n)
    qc.h(0)
    qc.cx(0, 1)
    qc.measure_all(add_bits=False)
    return qc


def _create_ghz_circuit(num_qubits: int = 3) -> QuantumCircuit:
    """Create a GHZ state circuit.

    Args:
        num_qubits: Number of qubits (minimum 3)

    Returns:
        GHZ state circuit
    """
    n = max(3, num_qubits)
    qc = QuantumCircuit(n, n)
    qc.h(0)
    for i in range(n - 1):
        qc.cx(i, i + 1)
    qc.measure_all(add_bits=False)
    return qc


def _create_hadamard_circuit(num_qubits: int = 1) -> QuantumCircuit:
    """Create a Hadamard superposition circuit.

    Args:
        num_qubits: Number of qubits

    Returns:
        Hadamard circuit
    """
    qc = QuantumCircuit(num_qubits, num_qubits)
    for i in range(num_qubits):
        qc.h(i)
    qc.measure_all(add_bits=False)
    return qc


def _parse_qasm(qasm_string: str) -> QuantumCircuit:
    """Parse QASM string to QuantumCircuit.

    Args:
        qasm_string: OpenQASM 2.0 string

    Returns:
        Parsed QuantumCircuit
    """
    return QuantumCircuit.from_qasm_str(qasm_string)


async def simulate_circuit(
    circuit_type: str,
    num_qubits: int = 2,
    shots: int = 1000,
    qasm_string: Optional[str] = None,
) -> str:
    """Simulate a quantum circuit locally.

    Args:
        circuit_type: Type of circuit ("bell", "ghz", "hadamard", "qasm")
        num_qubits: Number of qubits for built-in circuits
        shots: Number of measurement shots
        qasm_string: OpenQASM string for "qasm" circuit type

    Returns:
        JSON formatted simulation results
    """
    try:
        # Create circuit based on type
        if circuit_type == "bell":
            circuit = _create_bell_circuit(num_qubits)
        elif circuit_type == "ghz":
            circuit = _create_ghz_circuit(num_qubits)
        elif circuit_type == "hadamard":
            circuit = _create_hadamard_circuit(num_qubits)
        elif circuit_type == "qasm":
            if not qasm_string:
                return json.dumps({
                    "error": "qasm_string is required for circuit_type='qasm'",
                })
            circuit = _parse_qasm(qasm_string)
        else:
            return json.dumps({
                "error": f"Invalid circuit_type: {circuit_type}",
                "valid_types": ["bell", "ghz", "hadamard", "qasm"],
            })

        # Run simulation
        simulator = AerSimulator()
        job = simulator.run(circuit, shots=shots)
        result = job.result()
        counts = result.get_counts(circuit)

        # Calculate probabilities
        total = sum(counts.values())
        probabilities = {k: v / total for k, v in counts.items()}

        response = {
            "circuit_type": circuit_type,
            "num_qubits": circuit.num_qubits,
            "shots": shots,
            "counts": counts,
            "probabilities": probabilities,
            "most_likely": max(counts, key=counts.get),
        }

        return json.dumps(response, indent=2)

    except Exception as e:
        return json.dumps({
            "error": f"Simulation failed: {str(e)}",
        })
