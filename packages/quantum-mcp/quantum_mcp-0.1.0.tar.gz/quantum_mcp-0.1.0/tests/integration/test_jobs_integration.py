# Description: Integration tests for job lifecycle.
# Description: Tests job submission, polling, and result retrieval.
"""Integration tests for job lifecycle.

These tests require real Azure credentials and submit jobs to simulators.
"""

import os

import pytest
from qiskit import QuantumCircuit

from quantum_mcp.client import CostEstimate, JobInfo, JobResult, JobStatus, QuantumClient
from quantum_mcp.config import Settings, get_settings

pytestmark = pytest.mark.skipif(
    not os.getenv("AZURE_QUANTUM_WORKSPACE_ID"),
    reason="Azure Quantum credentials not configured",
)


@pytest.fixture
def real_settings() -> Settings:
    """Get settings from environment."""
    get_settings.cache_clear()
    return get_settings()


@pytest.fixture
def bell_circuit() -> QuantumCircuit:
    """Create a simple Bell state circuit for testing."""
    qc = QuantumCircuit(2, 2)
    qc.h(0)
    qc.cx(0, 1)
    qc.measure([0, 1], [0, 1])
    return qc


@pytest.mark.integration
class TestCostEstimation:
    """Test cost estimation with real backends."""

    @pytest.mark.asyncio
    async def test_estimate_simulator_cost(self, real_settings: Settings):
        """Test simulator cost estimation."""
        async with QuantumClient(real_settings) as client:
            estimate = await client.estimate_cost("ionq.simulator", 1000)

        assert isinstance(estimate, CostEstimate)
        assert estimate.estimated_cost_usd == 0.0
        assert estimate.shots == 1000


@pytest.mark.integration
class TestJobLifecycle:
    """Test full job lifecycle on simulators."""

    @pytest.mark.asyncio
    async def test_submit_to_simulator(
        self, real_settings: Settings, bell_circuit: QuantumCircuit
    ):
        """Test job submission to simulator."""
        async with QuantumClient(real_settings) as client:
            backends = await client.list_backends()
            simulator = next((b for b in backends if "simulator" in b.id.lower()), None)

            if simulator is None:
                pytest.skip("No simulator available")

            job = await client.submit_job(
                bell_circuit,
                backend=simulator.id,
                shots=100,
                name="test-bell-state",
            )

        assert isinstance(job, JobInfo)
        assert job.id is not None
        assert job.name == "test-bell-state"

    @pytest.mark.asyncio
    async def test_job_status_polling(
        self, real_settings: Settings, bell_circuit: QuantumCircuit
    ):
        """Test job status polling."""
        async with QuantumClient(real_settings) as client:
            backends = await client.list_backends()
            simulator = next((b for b in backends if "simulator" in b.id.lower()), None)

            if simulator is None:
                pytest.skip("No simulator available")

            job = await client.submit_job(
                bell_circuit,
                backend=simulator.id,
                shots=100,
            )

            status = await client.get_job_status(job.id)

        assert isinstance(status, JobInfo)
        assert status.id == job.id

    @pytest.mark.asyncio
    async def test_wait_for_job(
        self, real_settings: Settings, bell_circuit: QuantumCircuit
    ):
        """Test waiting for job completion."""
        async with QuantumClient(real_settings) as client:
            backends = await client.list_backends()
            simulator = next((b for b in backends if "simulator" in b.id.lower()), None)

            if simulator is None:
                pytest.skip("No simulator available")

            job = await client.submit_job(
                bell_circuit,
                backend=simulator.id,
                shots=100,
            )

            final = await client.wait_for_job(job.id, poll_interval=1.0, timeout=120)

        assert final.is_terminal
        assert final.status == JobStatus.SUCCEEDED

    @pytest.mark.asyncio
    async def test_get_job_result(
        self, real_settings: Settings, bell_circuit: QuantumCircuit
    ):
        """Test retrieving job results."""
        async with QuantumClient(real_settings) as client:
            backends = await client.list_backends()
            simulator = next((b for b in backends if "simulator" in b.id.lower()), None)

            if simulator is None:
                pytest.skip("No simulator available")

            job = await client.submit_job(
                bell_circuit,
                backend=simulator.id,
                shots=100,
            )

            await client.wait_for_job(job.id, poll_interval=1.0, timeout=120)

            result = await client.get_job_result(job.id)

        assert isinstance(result, JobResult)
        assert result.job_id == job.id
        assert len(result.counts) > 0
        assert sum(result.counts.values()) == 100

        probs = result.probabilities
        assert "00" in probs or "11" in probs
