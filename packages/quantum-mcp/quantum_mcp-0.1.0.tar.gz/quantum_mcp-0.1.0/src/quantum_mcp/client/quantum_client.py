# Description: Azure Quantum client wrapper with async support.
# Description: Manages connections, job submission, and result retrieval.
"""Azure Quantum client wrapper."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, Callable, Optional

import structlog
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from quantum_mcp.client.exceptions import (
    AuthenticationError,
    BackendNotFoundError,
    BudgetExceededError,
    JobExecutionError,
    JobSubmissionError,
    RateLimitError,
)
from quantum_mcp.client.exceptions import (
    ConnectionError as QConnectionError,
)
from quantum_mcp.client.models import (
    BackendInfo,
    CostEstimate,
    JobInfo,
    JobResult,
    JobStatus,
)

if TYPE_CHECKING:
    from azure.quantum import Workspace

    from quantum_mcp.config import Settings

logger = structlog.get_logger()


def _get_retry_decorator(
    max_attempts: int = 3,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Create retry decorator with exponential backoff."""
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((OSError, TimeoutError)),
        reraise=True,
    )


class QuantumClient:
    """Async client for Azure Quantum operations.

    Usage:
        async with QuantumClient(settings) as client:
            backends = await client.list_backends()
    """

    def __init__(self, settings: "Settings") -> None:
        """Initialize client with settings.

        Args:
            settings: Configuration settings
        """
        self._settings = settings
        self._workspace: Optional["Workspace"] = None
        self._connected = False
        self._logger = logger.bind(component="QuantumClient")

    @property
    def is_connected(self) -> bool:
        """Check if connected to Azure Quantum."""
        return self._connected and self._workspace is not None

    @property
    def settings(self) -> "Settings":
        """Get client settings."""
        return self._settings

    async def connect(self) -> None:
        """Establish connection to Azure Quantum workspace.

        Raises:
            QConnectionError: If connection fails
            AuthenticationError: If authentication fails
            ValueError: If credentials not configured
        """
        if self._connected:
            self._logger.debug("Already connected")
            return

        if not self._settings.has_azure_credentials:
            raise ValueError(
                "Azure Quantum credentials not configured. "
                "Set AZURE_QUANTUM_WORKSPACE_ID, AZURE_QUANTUM_RESOURCE_GROUP, "
                "and AZURE_QUANTUM_SUBSCRIPTION_ID environment variables."
            )

        self._logger.info(
            "Connecting to Azure Quantum",
            workspace_id=self._settings.azure_quantum_workspace_id,
            location=self._settings.azure_quantum_location,
        )

        @_get_retry_decorator(max_attempts=3)
        def create_workspace() -> "Workspace":
            from azure.quantum import Workspace

            return Workspace(
                subscription_id=self._settings.azure_quantum_subscription_id,
                resource_group=self._settings.azure_quantum_resource_group,
                name=self._settings.azure_quantum_workspace_id,
                location=self._settings.azure_quantum_location,
            )

        try:
            loop = asyncio.get_event_loop()
            self._workspace = await loop.run_in_executor(None, create_workspace)
            self._connected = True
            self._logger.info("Connected to Azure Quantum")

        except Exception as e:
            error_msg = str(e).lower()
            if "authentication" in error_msg or "credential" in error_msg:
                raise AuthenticationError(f"Authentication failed: {e}") from e
            self._logger.error("Connection failed", error=str(e))
            raise QConnectionError(f"Failed to connect to Azure Quantum: {e}") from e

    async def disconnect(self) -> None:
        """Clean up connection."""
        if self._connected:
            self._logger.info("Disconnecting from Azure Quantum")
            self._workspace = None
            self._connected = False

    async def __aenter__(self) -> "QuantumClient":
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[BaseException],
        exc_tb: Optional[object],
    ) -> None:
        """Async context manager exit."""
        await self.disconnect()

    async def list_backends(self) -> list[BackendInfo]:
        """List all available quantum backends.

        Returns:
            List of BackendInfo for each backend

        Raises:
            QConnectionError: If not connected
            RateLimitError: If rate limited
        """
        if not self.is_connected:
            raise QConnectionError("Not connected to Azure Quantum")

        self._logger.debug("Listing backends")

        @_get_retry_decorator(max_attempts=3)
        def get_targets() -> list[object]:
            return list(self._workspace.get_targets())  # type: ignore

        try:
            loop = asyncio.get_event_loop()
            targets = await loop.run_in_executor(None, get_targets)

            backends = []
            for target in targets:
                backend = self._parse_target(target)
                backends.append(backend)

            self._logger.info("Found backends", count=len(backends))
            return backends

        except Exception as e:
            if "rate" in str(e).lower() or "429" in str(e):
                raise RateLimitError(f"Rate limit exceeded: {e}") from e
            self._logger.error("Failed to list backends", error=str(e))
            raise

    async def get_backend_info(self, backend_id: str) -> BackendInfo:
        """Get information for a specific backend.

        Args:
            backend_id: Backend identifier (e.g., "ionq.simulator")

        Returns:
            BackendInfo for the backend

        Raises:
            BackendNotFoundError: If backend not found
        """
        backends = await self.list_backends()
        for backend in backends:
            if backend.id == backend_id:
                return backend
        raise BackendNotFoundError(
            f"Backend not found: {backend_id}",
            details={"available": [b.id for b in backends]},
        )

    def _parse_target(self, target: object) -> BackendInfo:
        """Parse Azure Quantum target into BackendInfo.

        Args:
            target: Azure Quantum Target object

        Returns:
            Parsed BackendInfo
        """
        target_id = getattr(target, "name", str(target))
        provider = target_id.split(".")[0] if "." in target_id else "unknown"

        is_sim = "simulator" in target_id.lower() or "sim" in target_id.lower()
        backend_type = "simulator" if is_sim else "hardware"

        num_qubits = getattr(target, "num_qubits", 0)
        if num_qubits == 0:
            defaults = {
                "ionq": 29 if not is_sim else 29,
                "quantinuum": 20 if not is_sim else 32,
                "rigetti": 80 if not is_sim else 32,
            }
            num_qubits = defaults.get(provider, 20)

        status = getattr(target, "current_availability", "online")
        if isinstance(status, str):
            status = status.lower()
        else:
            status = "online"

        return BackendInfo(
            id=target_id,
            provider=provider,
            backend_type=backend_type,
            num_qubits=num_qubits,
            status=status,
            gate_set=["h", "cx", "rz", "rx", "ry"],
            description=getattr(target, "description", None),
        )

    async def submit_job(
        self,
        circuit: object,
        backend: Optional[str] = None,
        shots: Optional[int] = None,
        name: Optional[str] = None,
    ) -> JobInfo:
        """Submit a quantum circuit for execution.

        Args:
            circuit: Qiskit QuantumCircuit to execute
            backend: Backend ID (defaults to settings.default_backend)
            shots: Number of shots (defaults to settings.max_shots)
            name: Job name (auto-generated if not provided)

        Returns:
            JobInfo with job ID and status

        Raises:
            QConnectionError: If not connected
            JobSubmissionError: If submission fails
            BudgetExceededError: If cost exceeds budget
        """
        if not self.is_connected:
            raise QConnectionError("Not connected to Azure Quantum")

        backend = backend or self._settings.default_backend
        shots = shots or self._settings.max_shots
        name = name or f"quantum-mcp-job-{id(circuit)}"

        estimate = await self.estimate_cost(backend, shots)
        if estimate.estimated_cost_usd > self._settings.budget_limit_usd:
            raise BudgetExceededError(
                f"Estimated cost ${estimate.estimated_cost_usd:.2f} exceeds "
                f"budget ${self._settings.budget_limit_usd:.2f}",
                details={
                    "estimated_cost": estimate.estimated_cost_usd,
                    "budget_limit": self._settings.budget_limit_usd,
                },
            )

        self._logger.info(
            "Submitting job",
            backend=backend,
            shots=shots,
            name=name,
        )

        @_get_retry_decorator(max_attempts=3)
        def submit() -> object:
            from azure.quantum.qiskit import AzureQuantumProvider

            provider = AzureQuantumProvider(workspace=self._workspace)
            qiskit_backend = provider.get_backend(backend)
            job = qiskit_backend.run(circuit, shots=shots)
            return job

        try:
            loop = asyncio.get_event_loop()
            job = await loop.run_in_executor(None, submit)

            job_info = JobInfo(
                id=job.id(),
                name=name,
                status=self._parse_job_status(job.status()),
                backend=backend,
                shots=shots,
                cost_estimate=estimate.estimated_cost_usd,
            )

            self._logger.info("Job submitted", job_id=job_info.id)
            return job_info

        except Exception as e:
            self._logger.error("Job submission failed", error=str(e))
            raise JobSubmissionError(f"Failed to submit job: {e}") from e

    async def get_job_status(self, job_id: str) -> JobInfo:
        """Get the status of a job.

        Args:
            job_id: Job ID to query

        Returns:
            JobInfo with current status

        Raises:
            QConnectionError: If not connected
        """
        if not self.is_connected:
            raise QConnectionError("Not connected to Azure Quantum")

        self._logger.debug("Getting job status", job_id=job_id)

        @_get_retry_decorator(max_attempts=3)
        def get_status() -> object:
            job = self._workspace.get_job(job_id)  # type: ignore
            return job

        try:
            loop = asyncio.get_event_loop()
            job = await loop.run_in_executor(None, get_status)

            # Access job properties through job.details dict
            details = job.details if hasattr(job, "details") else {}
            return JobInfo(
                id=job.id,
                name=details.get("name", job_id),
                status=self._parse_job_status(details.get("status", "Unknown")),
                backend=details.get("target", "unknown"),
                shots=details.get("inputParams", {}).get("shots", 0),
                error_message=(details.get("errorData") or {}).get("message"),
            )

        except Exception as e:
            self._logger.error("Failed to get job status", job_id=job_id, error=str(e))
            raise

    async def get_job_result(self, job_id: str) -> JobResult:
        """Get the result of a completed job.

        Args:
            job_id: Job ID to retrieve result for

        Returns:
            JobResult with measurement counts

        Raises:
            QConnectionError: If not connected
            JobExecutionError: If job failed or not complete
        """
        if not self.is_connected:
            raise QConnectionError("Not connected to Azure Quantum")

        job_info = await self.get_job_status(job_id)
        if not job_info.is_terminal:
            raise JobExecutionError(
                f"Job {job_id} is not complete (status: {job_info.status.value})"
            )
        if not job_info.is_success:
            raise JobExecutionError(
                f"Job {job_id} failed: {job_info.error_message}",
                details={"status": job_info.status.value},
            )

        self._logger.debug("Getting job result", job_id=job_id)

        @_get_retry_decorator(max_attempts=3)
        def get_result() -> object:
            job = self._workspace.get_job(job_id)  # type: ignore
            return job.get_results()

        try:
            loop = asyncio.get_event_loop()
            raw_result = await loop.run_in_executor(None, get_result)

            counts = self._parse_result_counts(raw_result, job_info.shots)

            return JobResult(
                job_id=job_id,
                counts=counts,
                shots=job_info.shots,
                backend=job_info.backend,
                raw_result=raw_result,
            )

        except JobExecutionError:
            raise
        except Exception as e:
            self._logger.error("Failed to get job result", job_id=job_id, error=str(e))
            raise JobExecutionError(f"Failed to get result: {e}") from e

    async def wait_for_job(
        self,
        job_id: str,
        poll_interval: float = 2.0,
        timeout: Optional[float] = None,
    ) -> JobInfo:
        """Wait for a job to complete.

        Args:
            job_id: Job ID to wait for
            poll_interval: Seconds between status checks
            timeout: Maximum seconds to wait (None for no timeout)

        Returns:
            JobInfo with final status

        Raises:
            TimeoutError: If timeout exceeded
        """
        import time

        start_time = time.time()
        self._logger.info("Waiting for job", job_id=job_id)

        while True:
            job_info = await self.get_job_status(job_id)
            if job_info.is_terminal:
                self._logger.info(
                    "Job completed",
                    job_id=job_id,
                    status=job_info.status.value,
                )
                return job_info

            if timeout and (time.time() - start_time) > timeout:
                raise TimeoutError(f"Job {job_id} did not complete within {timeout}s")

            await asyncio.sleep(poll_interval)

    async def cancel_job(self, job_id: str) -> JobInfo:
        """Cancel a running job.

        Args:
            job_id: Job ID to cancel

        Returns:
            JobInfo with updated status
        """
        if not self.is_connected:
            raise QConnectionError("Not connected to Azure Quantum")

        self._logger.info("Cancelling job", job_id=job_id)

        @_get_retry_decorator(max_attempts=3)
        def cancel() -> object:
            job = self._workspace.get_job(job_id)  # type: ignore
            job.cancel()
            return job

        try:
            loop = asyncio.get_event_loop()
            job = await loop.run_in_executor(None, cancel)

            return JobInfo(
                id=job.id,
                name=getattr(job, "name", job_id),
                status=JobStatus.CANCELLED,
                backend=getattr(job, "target", "unknown"),
                shots=0,
            )

        except Exception as e:
            self._logger.error("Failed to cancel job", job_id=job_id, error=str(e))
            raise

    async def estimate_cost(self, backend: str, shots: int) -> CostEstimate:
        """Estimate cost for a job.

        Args:
            backend: Backend ID
            shots: Number of shots

        Returns:
            CostEstimate with estimated cost
        """
        cost_per_shot = {
            "ionq.simulator": 0.0,
            "ionq.qpu": 0.00003,
            "ionq.qpu.aria-1": 0.00022,
            "quantinuum.sim.h1-1sc": 0.0,
            "quantinuum.sim.h1-1e": 0.0,
            "quantinuum.qpu.h1-1": 0.00125,
            "rigetti.sim.qvm": 0.0,
        }

        per_shot = cost_per_shot.get(backend, 0.0001)
        is_simulator = "simulator" in backend.lower() or "sim" in backend.lower()

        if is_simulator:
            per_shot = 0.0

        estimated = per_shot * shots
        notes = "Simulator (free)" if is_simulator else f"${per_shot}/shot"

        return CostEstimate(
            backend=backend,
            shots=shots,
            estimated_cost_usd=estimated,
            notes=notes,
        )

    def _parse_job_status(self, status: object) -> JobStatus:
        """Parse Azure job status to JobStatus enum."""
        status_str = str(status).lower()
        mapping = {
            "waiting": JobStatus.WAITING,
            "queued": JobStatus.WAITING,
            "executing": JobStatus.EXECUTING,
            "running": JobStatus.EXECUTING,
            "succeeded": JobStatus.SUCCEEDED,
            "finished": JobStatus.SUCCEEDED,
            "failed": JobStatus.FAILED,
            "error": JobStatus.FAILED,
            "cancelled": JobStatus.CANCELLED,
            "canceled": JobStatus.CANCELLED,
        }
        return mapping.get(status_str, JobStatus.WAITING)

    def _parse_result_counts(
        self, raw_result: object, shots: int = 100
    ) -> dict[str, int]:
        """Parse raw result to measurement counts.

        Args:
            raw_result: Raw result from the backend
            shots: Number of shots (used to convert probabilities to counts)

        Returns:
            Dictionary mapping bitstrings to counts
        """
        if hasattr(raw_result, "get_counts"):
            return dict(raw_result.get_counts())
        if isinstance(raw_result, dict):
            if "counts" in raw_result:
                return dict(raw_result["counts"])
            if "histogram" in raw_result:
                counts = {}
                for k, v in raw_result["histogram"].items():
                    key = self._normalize_bitstring_key(k)
                    counts[key] = int(v * shots)
                return counts
            # Check if values are probabilities (floats that sum to ~1.0)
            values = list(raw_result.values())
            if values and all(isinstance(v, float) and 0 <= v <= 1 for v in values):
                total = sum(values)
                if 0.99 <= total <= 1.01:
                    # Values are probabilities, convert to counts
                    counts = {}
                    for k, v in raw_result.items():
                        key = self._normalize_bitstring_key(k)
                        counts[key] = int(v * shots)
                    return counts
            return dict(raw_result)
        return {}

    def _normalize_bitstring_key(self, key: str) -> str:
        """Normalize bitstring keys to standard format.

        Converts formats like '[0, 0]' or '[0,1]' to '00' or '01'.
        """
        if key.startswith("[") and key.endswith("]"):
            # Parse list format like '[0, 0]' or '[0,1]'
            inner = key[1:-1]
            bits = [b.strip() for b in inner.split(",")]
            return "".join(bits)
        return key
