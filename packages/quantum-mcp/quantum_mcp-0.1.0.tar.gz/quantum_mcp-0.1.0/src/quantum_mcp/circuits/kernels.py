# Description: Quantum kernel methods for machine learning.
# Description: Provides feature maps and kernel matrix computation.
"""Quantum kernel methods for machine learning."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from qiskit_aer import AerSimulator


class FeatureMapType(Enum):
    """Types of quantum feature maps."""

    Z = "Z"  # Z-rotation only (no entanglement)
    ZZ = "ZZ"  # ZZ feature map with entanglement
    ZZZ = "ZZZ"  # Higher-order feature map


@dataclass
class KernelResult:
    """Result of kernel matrix computation."""

    kernel_matrix: np.ndarray
    num_qubits: int
    feature_map_type: str
    shots: int
    data_points: Optional[int] = None


def build_feature_map(
    num_qubits: int,
    feature_dim: int,
    feature_map_type: FeatureMapType = FeatureMapType.ZZ,
    reps: int = 2,
) -> QuantumCircuit:
    """Build a quantum feature map for data encoding.

    Creates a parameterized circuit that encodes classical data
    into quantum states using rotation gates.

    Args:
        num_qubits: Number of qubits in the circuit
        feature_dim: Dimension of the input feature vector
        feature_map_type: Type of feature map (Z, ZZ, ZZZ)
        reps: Number of repetitions of the feature map

    Returns:
        Parameterized QuantumCircuit for feature encoding
    """
    qc = QuantumCircuit(num_qubits)

    # Create parameters for features
    params = [Parameter(f"x_{i}") for i in range(feature_dim)]

    for rep in range(reps):
        # Hadamard layer to create superposition
        for i in range(num_qubits):
            qc.h(i)

        # Encode features using Z rotations
        for i in range(num_qubits):
            param_idx = i % feature_dim
            qc.rz(2 * params[param_idx], i)

        # Add entanglement based on feature map type
        if feature_map_type in (FeatureMapType.ZZ, FeatureMapType.ZZZ):
            # ZZ entanglement: encode pairwise feature interactions
            for i in range(num_qubits - 1):
                param_i = params[i % feature_dim]
                param_j = params[(i + 1) % feature_dim]
                # ZZ interaction with product of features
                qc.cx(i, i + 1)
                qc.rz(2 * param_i * param_j, i + 1)
                qc.cx(i, i + 1)

        if feature_map_type == FeatureMapType.ZZZ:
            # Higher-order interactions for ZZZ
            if num_qubits >= 3:
                for i in range(num_qubits - 2):
                    param_i = params[i % feature_dim]
                    param_j = params[(i + 1) % feature_dim]
                    param_k = params[(i + 2) % feature_dim]
                    qc.cx(i, i + 2)
                    qc.rz(param_i * param_j * param_k, i + 2)
                    qc.cx(i, i + 2)

    return qc


def _bind_feature_map(
    feature_map: QuantumCircuit,
    data: list[float],
) -> QuantumCircuit:
    """Bind data values to a feature map.

    Args:
        feature_map: Parameterized feature map circuit
        data: Data values to encode

    Returns:
        Bound circuit with data encoded
    """
    param_dict = {}
    for i, param in enumerate(feature_map.parameters):
        # Extract parameter index from name (x_0, x_1, etc.)
        idx = int(param.name.split("_")[1])
        if idx < len(data):
            param_dict[param] = data[idx]
        else:
            param_dict[param] = 0.0

    return feature_map.assign_parameters(param_dict)


async def compute_kernel_entry(
    x1: list[float],
    x2: list[float],
    num_qubits: int = 2,
    feature_map_type: FeatureMapType = FeatureMapType.ZZ,
    shots: int = 1000,
    reps: int = 2,
) -> float:
    """Compute a single kernel matrix entry K(x1, x2).

    Uses the fidelity between quantum states:
    K(x1, x2) = |<phi(x1)|phi(x2)>|^2

    Computed via the swap test or direct measurement.

    Args:
        x1: First data point
        x2: Second data point
        num_qubits: Number of qubits
        feature_map_type: Type of feature map
        shots: Number of measurement shots
        reps: Feature map repetitions

    Returns:
        Kernel value between 0 and 1
    """
    feature_dim = max(len(x1), len(x2))

    # Build feature map
    feature_map = build_feature_map(
        num_qubits=num_qubits,
        feature_dim=feature_dim,
        feature_map_type=feature_map_type,
        reps=reps,
    )

    # Create circuit: |phi(x1)><phi(x2)|
    # Apply U(x1) then U(x2)^dagger
    qc = QuantumCircuit(num_qubits)

    # Encode x1
    bound_x1 = _bind_feature_map(feature_map, x1)
    qc.compose(bound_x1, inplace=True)

    # Apply inverse of x2 encoding
    bound_x2 = _bind_feature_map(feature_map, x2)
    qc.compose(bound_x2.inverse(), inplace=True)

    # Measure all qubits
    qc.measure_all()

    # Run simulation
    simulator = AerSimulator()
    job = simulator.run(qc, shots=shots)
    result = job.result()
    counts = result.get_counts()

    # Fidelity is probability of measuring all zeros
    all_zeros = "0" * num_qubits
    zero_count = counts.get(all_zeros, 0)

    return float(zero_count) / shots


async def compute_kernel_matrix(
    data: list[list[float]],
    num_qubits: int = 2,
    feature_map_type: FeatureMapType = FeatureMapType.ZZ,
    shots: int = 1000,
    reps: int = 2,
) -> KernelResult:
    """Compute the full quantum kernel matrix for a dataset.

    Args:
        data: List of data points (each a list of floats)
        num_qubits: Number of qubits
        feature_map_type: Type of feature map
        shots: Number of measurement shots per entry
        reps: Feature map repetitions

    Returns:
        KernelResult with kernel matrix and metadata
    """
    n = len(data)
    kernel_matrix = np.zeros((n, n))

    # Compute kernel matrix entries
    for i in range(n):
        for j in range(i, n):
            if i == j:
                # Diagonal is always 1 (self-overlap)
                kernel_matrix[i, j] = 1.0
            else:
                # Compute off-diagonal entry
                k_ij = await compute_kernel_entry(
                    data[i],
                    data[j],
                    num_qubits=num_qubits,
                    feature_map_type=feature_map_type,
                    shots=shots,
                    reps=reps,
                )
                kernel_matrix[i, j] = k_ij
                kernel_matrix[j, i] = k_ij  # Symmetric

    return KernelResult(
        kernel_matrix=kernel_matrix,
        num_qubits=num_qubits,
        feature_map_type=feature_map_type.value,
        shots=shots,
        data_points=n,
    )
