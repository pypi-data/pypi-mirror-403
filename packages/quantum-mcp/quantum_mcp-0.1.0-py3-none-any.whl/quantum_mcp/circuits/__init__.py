# Description: Quantum circuit building and conversion module.
# Description: Provides circuit construction for VQE, QAOA, and kernel methods.
"""Quantum circuit building and conversion module."""

from quantum_mcp.circuits.converters import (
    CircuitConverter,
    CircuitInfo,
    CircuitValidationError,
    ValidationResult,
)
from quantum_mcp.circuits.kernels import (
    FeatureMapType,
    KernelResult,
    build_feature_map,
    compute_kernel_entry,
    compute_kernel_matrix,
)
from quantum_mcp.circuits.qaoa import (
    QAOACostFunction,
    QAOAResult,
    build_qaoa_circuit,
    encode_maxcut_problem,
    run_qaoa,
)
from quantum_mcp.circuits.qsharp import (
    QSharpResult,
    compile_qsharp,
    run_qsharp,
    validate_qsharp,
)
from quantum_mcp.circuits.vqe import (
    HamiltonianTerm,
    MolecularHamiltonian,
    VQEResult,
    build_hardware_efficient_ansatz,
    build_ry_ansatz,
    encode_h2_hamiltonian,
    run_vqe,
)

__all__ = [
    "CircuitConverter",
    "CircuitInfo",
    "CircuitValidationError",
    "FeatureMapType",
    "HamiltonianTerm",
    "KernelResult",
    "MolecularHamiltonian",
    "QAOACostFunction",
    "QAOAResult",
    "QSharpResult",
    "VQEResult",
    "ValidationResult",
    "build_feature_map",
    "build_hardware_efficient_ansatz",
    "build_qaoa_circuit",
    "build_ry_ansatz",
    "compile_qsharp",
    "compute_kernel_entry",
    "compute_kernel_matrix",
    "encode_h2_hamiltonian",
    "encode_maxcut_problem",
    "run_qaoa",
    "run_qsharp",
    "run_vqe",
    "validate_qsharp",
]
