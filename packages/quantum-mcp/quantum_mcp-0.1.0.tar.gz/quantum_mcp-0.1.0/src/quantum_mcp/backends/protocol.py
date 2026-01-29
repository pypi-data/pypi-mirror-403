# Description: Abstract protocol defining the interface for quantum backends.
# Description: Supports both gate-based and annealing paradigms.
"""Quantum backend protocols and shared types."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol, runtime_checkable


class BackendParadigm(str, Enum):
    """Quantum computing paradigm."""

    GATE_BASED = "gate_based"
    ANNEALING = "annealing"


class BackendStatus(str, Enum):
    """Backend availability status."""

    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    DEGRADED = "degraded"


@dataclass
class BackendCapabilities:
    """Capabilities and metadata for a quantum backend."""

    paradigm: BackendParadigm
    max_qubits: int
    supports_async: bool
    is_simulator: bool
    provider: str
    native_operations: list[str] = field(default_factory=list)

    def supports_operation(self, operation: str) -> bool:
        """Check if backend supports a specific operation."""
        return operation in self.native_operations


@runtime_checkable
class QuantumBackend(Protocol):
    """Protocol for all quantum backends.

    This is the base protocol that all quantum backends must implement,
    regardless of whether they are gate-based or annealing.
    """

    @property
    def backend_id(self) -> str:
        """Unique identifier for this backend."""
        ...

    @property
    def capabilities(self) -> BackendCapabilities:
        """Backend capabilities and metadata."""
        ...

    @property
    def is_connected(self) -> bool:
        """Check if backend is connected and ready."""
        ...

    async def connect(self) -> None:
        """Establish connection to the backend."""
        ...

    async def disconnect(self) -> None:
        """Close connection to the backend."""
        ...

    async def health_check(self) -> BackendStatus:
        """Check backend health and availability."""
        ...


class BaseQuantumBackend(ABC):
    """Abstract base class for quantum backends.

    Provides common functionality and enforces the QuantumBackend protocol.
    """

    def __init__(self) -> None:
        """Initialize backend state."""
        self._connected: bool = False

    @property
    @abstractmethod
    def backend_id(self) -> str:
        """Unique identifier for this backend."""
        ...

    @property
    @abstractmethod
    def capabilities(self) -> BackendCapabilities:
        """Backend capabilities and metadata."""
        ...

    @property
    def is_connected(self) -> bool:
        """Check if backend is connected and ready."""
        return self._connected

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to the backend."""
        ...

    async def disconnect(self) -> None:
        """Close connection to the backend."""
        self._connected = False

    async def health_check(self) -> BackendStatus:
        """Check backend health and availability."""
        if not self._connected:
            return BackendStatus.UNAVAILABLE
        return BackendStatus.AVAILABLE

    async def __aenter__(self) -> "BaseQuantumBackend":
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(
        self,
        exc_type: type | None,
        exc_val: BaseException | None,
        exc_tb: object | None,
    ) -> None:
        """Async context manager exit."""
        await self.disconnect()
