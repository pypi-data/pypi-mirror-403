# Description: MCP tools for quantum job lifecycle management.
# Description: Handles job submission, status polling, and result retrieval.
"""Job management MCP tools."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Optional

from qiskit import QuantumCircuit

if TYPE_CHECKING:
    from quantum_mcp.client import QuantumClient


def _create_circuit(
    circuit_type: str,
    num_qubits: int = 2,
    qasm_string: Optional[str] = None,
) -> QuantumCircuit:
    """Create a quantum circuit based on type.

    Args:
        circuit_type: Type of circuit ("bell", "ghz", "hadamard", "qasm")
        num_qubits: Number of qubits for built-in circuits
        qasm_string: OpenQASM string for "qasm" circuit type

    Returns:
        QuantumCircuit instance

    Raises:
        ValueError: If circuit type is invalid or qasm_string missing
    """
    if circuit_type == "bell":
        n = max(2, num_qubits)
        qc = QuantumCircuit(n, n)
        qc.h(0)
        qc.cx(0, 1)
        qc.measure_all(add_bits=False)
        return qc

    elif circuit_type == "ghz":
        n = max(3, num_qubits)
        qc = QuantumCircuit(n, n)
        qc.h(0)
        for i in range(n - 1):
            qc.cx(i, i + 1)
        qc.measure_all(add_bits=False)
        return qc

    elif circuit_type == "hadamard":
        qc = QuantumCircuit(num_qubits, num_qubits)
        for i in range(num_qubits):
            qc.h(i)
        qc.measure_all(add_bits=False)
        return qc

    elif circuit_type == "qasm":
        if not qasm_string:
            raise ValueError("qasm_string is required for circuit_type='qasm'")
        return QuantumCircuit.from_qasm_str(qasm_string)

    else:
        raise ValueError(f"Invalid circuit_type: {circuit_type}")


async def submit_job(
    client: "QuantumClient",
    circuit_type: str,
    backend: str = "ionq.simulator",
    shots: int = 1000,
    num_qubits: int = 2,
    qasm_string: Optional[str] = None,
    job_name: Optional[str] = None,
) -> str:
    """Submit a quantum job for execution.

    Args:
        client: QuantumClient instance
        circuit_type: Type of circuit ("bell", "ghz", "hadamard", "qasm")
        backend: Target backend ID
        shots: Number of measurement shots
        num_qubits: Number of qubits for built-in circuits
        qasm_string: OpenQASM string for "qasm" circuit type
        job_name: Optional name for the job

    Returns:
        JSON formatted job submission result
    """
    if not client.is_connected:
        return json.dumps({
            "error": "Not connected to Azure Quantum",
            "suggestion": "Ensure Azure credentials are configured",
        })

    try:
        circuit = _create_circuit(circuit_type, num_qubits, qasm_string)

        job_info = await client.submit_job(
            circuit=circuit,
            backend=backend,
            shots=shots,
            name=job_name,
        )

        result = {
            "status": "submitted",
            "job_id": job_info.id,
            "name": job_info.name,
            "backend": job_info.backend,
            "shots": job_info.shots,
            "job_status": job_info.status.value,
            "cost_estimate_usd": job_info.cost_estimate,
        }

        return json.dumps(result, indent=2)

    except ValueError as e:
        return json.dumps({
            "error": f"Invalid circuit: {str(e)}",
        })
    except Exception as e:
        return json.dumps({
            "error": f"Failed to submit job: {str(e)}",
        })


async def get_job_status(
    client: "QuantumClient",
    job_id: str,
) -> str:
    """Get the status of a quantum job.

    Args:
        client: QuantumClient instance
        job_id: Job ID to query

    Returns:
        JSON formatted job status
    """
    if not client.is_connected:
        return json.dumps({
            "error": "Not connected to Azure Quantum",
        })

    try:
        job_info = await client.get_job_status(job_id)

        result = {
            "job_id": job_info.id,
            "name": job_info.name,
            "status": job_info.status.value,
            "backend": job_info.backend,
            "shots": job_info.shots,
            "is_terminal": job_info.is_terminal,
            "is_success": job_info.is_success,
        }

        if job_info.error_message:
            result["error_message"] = job_info.error_message

        return json.dumps(result, indent=2)

    except Exception as e:
        return json.dumps({
            "error": f"Failed to get job status: {str(e)}",
        })


async def get_job_result(
    client: "QuantumClient",
    job_id: str,
) -> str:
    """Get the result of a completed quantum job.

    Args:
        client: QuantumClient instance
        job_id: Job ID to retrieve result for

    Returns:
        JSON formatted job result with counts and probabilities
    """
    if not client.is_connected:
        return json.dumps({
            "error": "Not connected to Azure Quantum",
        })

    try:
        job_result = await client.get_job_result(job_id)

        most_likely = None
        if job_result.counts:
            most_likely = max(job_result.counts, key=lambda k: job_result.counts[k])

        result: dict[str, object] = {
            "job_id": job_result.job_id,
            "backend": job_result.backend,
            "shots": job_result.shots,
            "counts": job_result.counts,
            "probabilities": job_result.probabilities,
            "most_likely_outcome": most_likely,
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        return json.dumps({
            "error": f"Failed to get job result: {str(e)}",
        })


async def cancel_job(
    client: "QuantumClient",
    job_id: str,
) -> str:
    """Cancel a running quantum job.

    Args:
        client: QuantumClient instance
        job_id: Job ID to cancel

    Returns:
        JSON formatted cancellation result
    """
    if not client.is_connected:
        return json.dumps({
            "error": "Not connected to Azure Quantum",
        })

    try:
        job_info = await client.cancel_job(job_id)

        result = {
            "job_id": job_info.id,
            "status": job_info.status.value,
            "message": f"Job {job_id} has been cancelled",
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        return json.dumps({
            "error": f"Failed to cancel job: {str(e)}",
        })


async def wait_for_job(
    client: "QuantumClient",
    job_id: str,
    timeout: Optional[float] = 300.0,
    poll_interval: float = 2.0,
) -> str:
    """Wait for a job to complete and return its result.

    Args:
        client: QuantumClient instance
        job_id: Job ID to wait for
        timeout: Maximum seconds to wait (default: 300)
        poll_interval: Seconds between status checks (default: 2)

    Returns:
        JSON formatted final job status and result
    """
    if not client.is_connected:
        return json.dumps({
            "error": "Not connected to Azure Quantum",
        })

    try:
        job_info = await client.wait_for_job(
            job_id,
            poll_interval=poll_interval,
            timeout=timeout,
        )

        result: dict[str, object] = {
            "job_id": job_info.id,
            "status": job_info.status.value,
            "is_success": job_info.is_success,
        }

        if job_info.is_success:
            job_result = await client.get_job_result(job_id)
            result["counts"] = job_result.counts
            result["probabilities"] = job_result.probabilities
        elif job_info.error_message:
            result["error_message"] = job_info.error_message

        return json.dumps(result, indent=2)

    except TimeoutError:
        return json.dumps({
            "error": f"Job {job_id} did not complete within {timeout} seconds",
            "job_id": job_id,
        })
    except Exception as e:
        return json.dumps({
            "error": f"Failed while waiting for job: {str(e)}",
        })
