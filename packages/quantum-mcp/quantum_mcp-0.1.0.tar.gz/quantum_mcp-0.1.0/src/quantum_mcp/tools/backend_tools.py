# Description: Backend discovery and cost estimation tools.
# Description: Provides MCP tools for listing backends and estimating costs.
"""Backend discovery and cost estimation MCP tools."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from quantum_mcp.client import QuantumClient


async def list_backends(
    client: "QuantumClient",
    simulators_only: bool = False,
    provider: Optional[str] = None,
) -> str:
    """List available quantum backends.

    Args:
        client: QuantumClient instance
        simulators_only: If True, only return simulator backends
        provider: Filter by provider name (e.g., "ionq", "quantinuum")

    Returns:
        JSON formatted string of available backends
    """
    if not client.is_connected:
        return json.dumps({
            "error": "Not connected to Azure Quantum",
            "suggestion": "Ensure Azure credentials are configured",
        })

    try:
        backends = await client.list_backends()

        # Apply filters
        if simulators_only:
            backends = [b for b in backends if b.is_simulator]
        if provider:
            backends = [b for b in backends if b.provider.lower() == provider.lower()]

        # Format response
        result = {
            "backends": [
                {
                    "id": b.id,
                    "provider": b.provider,
                    "type": b.backend_type,
                    "num_qubits": b.num_qubits,
                    "status": b.status,
                    "is_simulator": b.is_simulator,
                }
                for b in backends
            ],
            "total": len(backends),
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        return json.dumps({
            "error": f"Failed to list backends: {str(e)}",
        })


async def estimate_cost(
    client: "QuantumClient",
    backend: str,
    shots: int,
) -> str:
    """Estimate cost for running a job.

    Args:
        client: QuantumClient instance
        backend: Backend ID to estimate cost for
        shots: Number of shots to estimate

    Returns:
        JSON formatted cost estimate
    """
    if not client.is_connected:
        return json.dumps({
            "error": "Not connected to Azure Quantum",
        })

    try:
        estimate = await client.estimate_cost(backend, shots)

        result = {
            "backend": estimate.backend,
            "shots": estimate.shots,
            "estimated_cost_usd": f"${estimate.estimated_cost_usd:.4f}",
            "notes": estimate.notes,
            "is_free": estimate.estimated_cost_usd == 0.0,
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        return json.dumps({
            "error": f"Failed to estimate cost: {str(e)}",
        })
