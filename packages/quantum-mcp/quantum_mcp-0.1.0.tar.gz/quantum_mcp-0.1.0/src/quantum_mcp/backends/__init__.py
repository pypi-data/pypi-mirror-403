# Description: Quantum backends module for multi-provider support.
# Description: Exports protocols, backends, and factory functions.
"""Quantum backends for Azure Quantum and D-Wave."""

from quantum_mcp.backends.annealing import (
    AnnealingBackend,
    AnnealingResult,
    AnnealingSample,
)
from quantum_mcp.backends.exact_solver import ExactSolverBackend
from quantum_mcp.backends.factory import (
    create_annealing_backend,
    get_available_annealing_backends,
    has_dwave_credentials,
)
from quantum_mcp.backends.protocol import (
    BackendCapabilities,
    BackendParadigm,
    BackendStatus,
    BaseQuantumBackend,
    QuantumBackend,
)

__all__ = [
    # Protocols and base classes
    "AnnealingBackend",
    "BackendCapabilities",
    "BackendParadigm",
    "BackendStatus",
    "BaseQuantumBackend",
    "QuantumBackend",
    # Result models
    "AnnealingResult",
    "AnnealingSample",
    # Concrete backends
    "ExactSolverBackend",
    # Factory functions
    "create_annealing_backend",
    "get_available_annealing_backends",
    "has_dwave_credentials",
]


def __getattr__(name: str) -> object:
    """Lazy import for D-Wave backend to avoid import errors when SDK not installed."""
    if name == "DWaveBackend":
        from quantum_mcp.backends.dwave import DWaveBackend

        return DWaveBackend
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
