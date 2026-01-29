# Description: Factory functions for creating quantum backends.
# Description: Provides unified interface for backend instantiation.
"""Backend factory functions."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Optional

import structlog

from quantum_mcp.backends.annealing import AnnealingBackend
from quantum_mcp.backends.exact_solver import ExactSolverBackend

if TYPE_CHECKING:
    from quantum_mcp.config import Settings

logger = structlog.get_logger()


def has_dwave_credentials() -> bool:
    """Check if D-Wave credentials are available.

    Returns:
        True if DWAVE_API_TOKEN is set
    """
    return bool(os.environ.get("DWAVE_API_TOKEN"))


def create_annealing_backend(
    backend_type: str = "auto",
    settings: Optional["Settings"] = None,
    **kwargs: object,
) -> AnnealingBackend:
    """Create an annealing backend.

    Args:
        backend_type: One of:
            - "dwave": D-Wave quantum annealer
            - "exact": Classical exact solver (brute-force)
            - "auto": Try D-Wave, fall back to exact solver
        settings: Optional settings with D-Wave credentials
        **kwargs: Backend-specific parameters

    Returns:
        Configured AnnealingBackend instance

    Raises:
        ValueError: If backend_type is unknown
        ImportError: If D-Wave SDK not installed when requesting "dwave"

    Example:
        >>> backend = create_annealing_backend("auto")
        >>> await backend.connect()
        >>> result = await backend.solve_qubo({(0, 1): -1})
    """
    log = logger.bind(backend_type=backend_type)

    # Get D-Wave token from settings or environment
    dwave_token: Optional[str] = None
    dwave_solver: str = "Advantage_system6.4"

    if settings is not None:
        dwave_token = getattr(settings, "dwave_api_token", None) or None
        dwave_solver = getattr(settings, "dwave_solver", dwave_solver)

    if not dwave_token:
        dwave_token = os.environ.get("DWAVE_API_TOKEN")

    if backend_type == "dwave":
        log.info("Creating D-Wave backend")
        from quantum_mcp.backends.dwave import DWaveBackend

        return DWaveBackend(
            token=dwave_token,
            solver=kwargs.get("solver", dwave_solver),  # type: ignore
            use_embedding=kwargs.get("use_embedding", True),  # type: ignore
        )

    elif backend_type == "exact":
        log.info("Creating ExactSolver backend")
        max_vars = kwargs.get("max_variables", 20)
        return ExactSolverBackend(max_variables=max_vars)  # type: ignore

    elif backend_type == "auto":
        # Try D-Wave if credentials available and SDK installed
        if dwave_token:
            try:
                from quantum_mcp.backends.dwave import DWaveBackend

                log.info("Auto-selected D-Wave backend (credentials found)")
                return DWaveBackend(
                    token=dwave_token,
                    solver=kwargs.get("solver", dwave_solver),  # type: ignore
                    use_embedding=kwargs.get("use_embedding", True),  # type: ignore
                )
            except ImportError:
                log.warning(
                    "D-Wave SDK not installed, falling back to ExactSolver. "
                    "Install with: uv sync --extra dwave"
                )

        # Fall back to exact solver
        log.info("Auto-selected ExactSolver backend (no D-Wave credentials)")
        max_vars = kwargs.get("max_variables", 20)
        return ExactSolverBackend(max_variables=max_vars)  # type: ignore

    else:
        raise ValueError(
            f"Unknown annealing backend type: {backend_type}. "
            f"Valid options: 'dwave', 'exact', 'auto'"
        )


async def get_available_annealing_backends() -> list[dict[str, object]]:
    """Get list of available annealing backends.

    Returns:
        List of backend info dicts with id, provider, available status
    """
    backends = []

    # ExactSolver is always available
    backends.append(
        {
            "id": "classical.exact_solver",
            "provider": "classical",
            "type": "exact_solver",
            "available": True,
            "is_simulator": True,
        }
    )

    # Check D-Wave availability
    dwave_available = False
    if has_dwave_credentials():
        try:
            from quantum_mcp.backends.dwave import DWaveBackend

            backend = DWaveBackend()
            try:
                await backend.connect()
                dwave_available = True
                await backend.disconnect()
            except Exception:
                pass
        except ImportError:
            pass

    backends.append(
        {
            "id": "dwave.Advantage_system6.4",
            "provider": "dwave",
            "type": "quantum_annealer",
            "available": dwave_available,
            "is_simulator": False,
        }
    )

    return backends
