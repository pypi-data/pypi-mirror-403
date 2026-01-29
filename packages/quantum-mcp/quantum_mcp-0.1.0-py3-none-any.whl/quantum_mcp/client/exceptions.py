# Description: Custom exceptions for quantum client.
# Description: Provides specific error types for quantum operations.
"""Custom exceptions for quantum client."""


class QuantumClientError(Exception):
    """Base exception for quantum client errors."""

    def __init__(self, message: str, details: dict[str, object] | None = None):
        super().__init__(message)
        self.details = details or {}


class ConnectionError(QuantumClientError):
    """Failed to connect to Azure Quantum."""

    pass


class BackendNotFoundError(QuantumClientError):
    """Requested backend does not exist."""

    pass


class AuthenticationError(QuantumClientError):
    """Azure authentication failed."""

    pass


class RateLimitError(QuantumClientError):
    """Rate limit exceeded."""

    pass


class JobSubmissionError(QuantumClientError):
    """Failed to submit job."""

    pass


class JobExecutionError(QuantumClientError):
    """Job execution failed."""

    pass


class BudgetExceededError(QuantumClientError):
    """Cost budget exceeded."""

    pass


class CircuitValidationError(QuantumClientError):
    """Circuit validation failed."""

    pass
