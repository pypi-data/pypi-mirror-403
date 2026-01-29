# Description: Test job lifecycle management.
# Description: Validates job submission, status, and result retrieval.
"""Test job lifecycle management."""

from unittest.mock import MagicMock, patch

import pytest

from quantum_mcp.client import (
    BudgetExceededError,
    ConnectionError,
    JobExecutionError,
    JobInfo,
    JobResult,
    JobStatus,
    QuantumClient,
)
from quantum_mcp.config import Settings


class TestJobModels:
    """Test job-related models."""

    def test_job_info_is_terminal(self):
        """Test JobInfo.is_terminal property."""
        waiting = JobInfo(
            id="j1", name="test", status=JobStatus.WAITING, backend="ionq.sim", shots=100
        )
        assert waiting.is_terminal is False

        succeeded = JobInfo(
            id="j2", name="test", status=JobStatus.SUCCEEDED, backend="ionq.sim", shots=100
        )
        assert succeeded.is_terminal is True

        failed = JobInfo(
            id="j3", name="test", status=JobStatus.FAILED, backend="ionq.sim", shots=100
        )
        assert failed.is_terminal is True

    def test_job_info_is_success(self):
        """Test JobInfo.is_success property."""
        succeeded = JobInfo(
            id="j1", name="test", status=JobStatus.SUCCEEDED, backend="ionq.sim", shots=100
        )
        assert succeeded.is_success is True

        failed = JobInfo(
            id="j2", name="test", status=JobStatus.FAILED, backend="ionq.sim", shots=100
        )
        assert failed.is_success is False

    def test_job_result_probabilities(self):
        """Test JobResult.probabilities property."""
        result = JobResult(
            job_id="j1",
            counts={"00": 500, "11": 500},
            shots=1000,
            backend="ionq.sim",
        )
        probs = result.probabilities
        assert probs["00"] == 0.5
        assert probs["11"] == 0.5

    def test_job_result_empty_counts(self):
        """Test probabilities with empty counts."""
        result = JobResult(
            job_id="j1",
            counts={},
            shots=0,
            backend="ionq.sim",
        )
        assert result.probabilities == {}


class TestCostEstimation:
    """Test cost estimation."""

    @pytest.mark.asyncio
    async def test_estimate_simulator_free(self, mock_settings: Settings):
        """Test simulator cost is free."""
        with patch("azure.quantum.Workspace"):
            client = QuantumClient(mock_settings)
            client._connected = True
            client._workspace = MagicMock()

            estimate = await client.estimate_cost("ionq.simulator", 1000)

        assert estimate.estimated_cost_usd == 0.0
        assert "free" in estimate.notes.lower()

    @pytest.mark.asyncio
    async def test_estimate_hardware_cost(self, mock_settings: Settings):
        """Test hardware cost estimation."""
        with patch("azure.quantum.Workspace"):
            client = QuantumClient(mock_settings)
            client._connected = True
            client._workspace = MagicMock()

            estimate = await client.estimate_cost("ionq.qpu", 1000)

        assert estimate.estimated_cost_usd > 0
        assert estimate.shots == 1000

    @pytest.mark.asyncio
    async def test_budget_exceeded(self, mock_settings: Settings):
        """Test budget exceeded error."""
        mock_settings_low_budget = Settings(
            _env_file=None,
            azure_quantum_workspace_id="test",
            azure_quantum_resource_group="test",
            azure_quantum_subscription_id="test",
            budget_limit_usd=0.01,
        )

        with patch("azure.quantum.Workspace"):
            client = QuantumClient(mock_settings_low_budget)
            client._connected = True
            client._workspace = MagicMock()

            mock_circuit = MagicMock()
            with pytest.raises(BudgetExceededError):
                await client.submit_job(mock_circuit, backend="ionq.qpu", shots=10000)


class TestJobSubmission:
    """Test job submission."""

    @pytest.mark.asyncio
    async def test_submit_not_connected(self, mock_settings: Settings):
        """Test submit raises when not connected."""
        client = QuantumClient(mock_settings)
        with pytest.raises(ConnectionError):
            await client.submit_job(MagicMock())

    @pytest.mark.asyncio
    async def test_submit_success(self, mock_settings: Settings):
        """Test successful job submission."""
        mock_job = MagicMock()
        mock_job.id.return_value = "test-job-id"
        mock_job.status.return_value = "Waiting"

        mock_backend = MagicMock()
        mock_backend.run.return_value = mock_job

        mock_provider = MagicMock()
        mock_provider.get_backend.return_value = mock_backend

        mock_qiskit_module = MagicMock(
            AzureQuantumProvider=MagicMock(return_value=mock_provider)
        )

        with patch("azure.quantum.Workspace"):
            with patch.dict(
                "sys.modules",
                {"azure.quantum.qiskit": mock_qiskit_module},
            ):
                client = QuantumClient(mock_settings)
                client._connected = True
                client._workspace = MagicMock()

                result = await client.submit_job(
                    MagicMock(),
                    backend="ionq.simulator",
                    shots=100,
                    name="test-job",
                )

        assert result.id == "test-job-id"
        assert result.status == JobStatus.WAITING
        assert result.name == "test-job"


class TestJobStatus:
    """Test job status polling."""

    @pytest.mark.asyncio
    async def test_get_status_not_connected(self, mock_settings: Settings):
        """Test get_job_status raises when not connected."""
        client = QuantumClient(mock_settings)
        with pytest.raises(ConnectionError):
            await client.get_job_status("some-job-id")

    @pytest.mark.asyncio
    async def test_get_status_success(self, mock_settings: Settings):
        """Test successful status retrieval."""
        mock_job = MagicMock()
        mock_job.id = "test-job-id"
        mock_job.details = {
            "status": "Succeeded",
            "name": "test-job-id",
            "target": "ionq.simulator",
            "inputParams": {"shots": 100},
            "errorData": None,
        }

        mock_workspace = MagicMock()
        mock_workspace.get_job.return_value = mock_job

        with patch("azure.quantum.Workspace"):
            client = QuantumClient(mock_settings)
            client._connected = True
            client._workspace = mock_workspace

            result = await client.get_job_status("test-job-id")

        assert result.id == "test-job-id"
        assert result.status == JobStatus.SUCCEEDED


class TestJobResult:
    """Test job result retrieval."""

    @pytest.mark.asyncio
    async def test_get_result_not_complete(self, mock_settings: Settings):
        """Test error when job not complete."""
        mock_job = MagicMock()
        mock_job.id = "test-job-id"
        mock_job.details = {
            "status": "Executing",
            "name": "test-job-id",
            "target": "ionq.simulator",
            "inputParams": {"shots": 100},
            "errorData": None,
        }

        mock_workspace = MagicMock()
        mock_workspace.get_job.return_value = mock_job

        with patch("azure.quantum.Workspace"):
            client = QuantumClient(mock_settings)
            client._connected = True
            client._workspace = mock_workspace

            with pytest.raises(JobExecutionError, match="not complete"):
                await client.get_job_result("test-job-id")

    @pytest.mark.asyncio
    async def test_get_result_success(self, mock_settings: Settings):
        """Test successful result retrieval."""
        mock_job = MagicMock()
        mock_job.id = "test-job-id"
        mock_job.details = {
            "status": "Succeeded",
            "name": "test-job-id",
            "target": "ionq.simulator",
            "inputParams": {"shots": 100},
            "errorData": None,
        }
        mock_job.get_results.return_value = {"00": 50, "11": 50}

        mock_workspace = MagicMock()
        mock_workspace.get_job.return_value = mock_job

        with patch("azure.quantum.Workspace"):
            client = QuantumClient(mock_settings)
            client._connected = True
            client._workspace = mock_workspace

            result = await client.get_job_result("test-job-id")

        assert result.job_id == "test-job-id"
        assert result.counts == {"00": 50, "11": 50}
