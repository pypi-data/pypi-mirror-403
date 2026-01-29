# Description: Test MCP tools for job management.
# Description: Validates job submission, status, and result retrieval tools.
"""Test MCP tools for job management."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from quantum_mcp.client import JobInfo, JobResult, JobStatus
from quantum_mcp.tools.job_tools import (
    cancel_job,
    get_job_result,
    get_job_status,
    submit_job,
)


class TestSubmitJob:
    """Test quantum_submit_job tool."""

    @pytest.mark.asyncio
    async def test_submit_bell_circuit(self):
        """Test submitting a Bell state circuit."""
        mock_client = MagicMock()
        mock_client.is_connected = True
        mock_client.submit_job = AsyncMock(
            return_value=JobInfo(
                id="job-123",
                name="test-job",
                status=JobStatus.WAITING,
                backend="ionq.simulator",
                shots=1000,
            )
        )

        result = await submit_job(
            mock_client,
            circuit_type="bell",
            backend="ionq.simulator",
            shots=1000,
        )

        assert "job-123" in result
        assert "waiting" in result.lower() or "submitted" in result.lower()

    @pytest.mark.asyncio
    async def test_submit_with_qasm(self):
        """Test submitting a QASM circuit."""
        mock_client = MagicMock()
        mock_client.is_connected = True
        mock_client.submit_job = AsyncMock(
            return_value=JobInfo(
                id="job-456",
                name="qasm-job",
                status=JobStatus.WAITING,
                backend="ionq.simulator",
                shots=500,
            )
        )

        qasm = """
        OPENQASM 2.0;
        include "qelib1.inc";
        qreg q[2];
        creg c[2];
        h q[0];
        cx q[0], q[1];
        measure q -> c;
        """

        result = await submit_job(
            mock_client,
            circuit_type="qasm",
            qasm_string=qasm,
            backend="ionq.simulator",
            shots=500,
        )

        assert "job-456" in result

    @pytest.mark.asyncio
    async def test_submit_not_connected(self):
        """Test error when not connected."""
        mock_client = MagicMock()
        mock_client.is_connected = False

        result = await submit_job(
            mock_client,
            circuit_type="bell",
            backend="ionq.simulator",
            shots=1000,
        )

        assert "error" in result.lower() or "not connected" in result.lower()


class TestGetJobStatus:
    """Test quantum_get_status tool."""

    @pytest.mark.asyncio
    async def test_get_status_waiting(self):
        """Test getting status of waiting job."""
        mock_client = MagicMock()
        mock_client.is_connected = True
        mock_client.get_job_status = AsyncMock(
            return_value=JobInfo(
                id="job-123",
                name="test-job",
                status=JobStatus.WAITING,
                backend="ionq.simulator",
                shots=1000,
            )
        )

        result = await get_job_status(mock_client, job_id="job-123")

        assert "job-123" in result
        assert "waiting" in result.lower()

    @pytest.mark.asyncio
    async def test_get_status_succeeded(self):
        """Test getting status of succeeded job."""
        mock_client = MagicMock()
        mock_client.is_connected = True
        mock_client.get_job_status = AsyncMock(
            return_value=JobInfo(
                id="job-123",
                name="test-job",
                status=JobStatus.SUCCEEDED,
                backend="ionq.simulator",
                shots=1000,
            )
        )

        result = await get_job_status(mock_client, job_id="job-123")

        assert "succeeded" in result.lower()

    @pytest.mark.asyncio
    async def test_get_status_not_connected(self):
        """Test error when not connected."""
        mock_client = MagicMock()
        mock_client.is_connected = False

        result = await get_job_status(mock_client, job_id="job-123")

        assert "error" in result.lower() or "not connected" in result.lower()


class TestGetJobResult:
    """Test quantum_get_result tool."""

    @pytest.mark.asyncio
    async def test_get_result_success(self):
        """Test getting result of completed job."""
        mock_client = MagicMock()
        mock_client.is_connected = True
        mock_client.get_job_result = AsyncMock(
            return_value=JobResult(
                job_id="job-123",
                counts={"00": 500, "11": 500},
                shots=1000,
                backend="ionq.simulator",
            )
        )

        result = await get_job_result(mock_client, job_id="job-123")

        assert "job-123" in result
        assert "00" in result
        assert "11" in result
        assert "500" in result

    @pytest.mark.asyncio
    async def test_get_result_with_probabilities(self):
        """Test result includes probabilities."""
        mock_client = MagicMock()
        mock_client.is_connected = True
        mock_client.get_job_result = AsyncMock(
            return_value=JobResult(
                job_id="job-123",
                counts={"00": 250, "11": 750},
                shots=1000,
                backend="ionq.simulator",
            )
        )

        result = await get_job_result(mock_client, job_id="job-123")

        assert "0.25" in result or "25" in result
        assert "0.75" in result or "75" in result

    @pytest.mark.asyncio
    async def test_get_result_not_connected(self):
        """Test error when not connected."""
        mock_client = MagicMock()
        mock_client.is_connected = False

        result = await get_job_result(mock_client, job_id="job-123")

        assert "error" in result.lower() or "not connected" in result.lower()


class TestCancelJob:
    """Test quantum_cancel_job tool."""

    @pytest.mark.asyncio
    async def test_cancel_job_success(self):
        """Test cancelling a job."""
        mock_client = MagicMock()
        mock_client.is_connected = True
        mock_client.cancel_job = AsyncMock(
            return_value=JobInfo(
                id="job-123",
                name="test-job",
                status=JobStatus.CANCELLED,
                backend="ionq.simulator",
                shots=1000,
            )
        )

        result = await cancel_job(mock_client, job_id="job-123")

        assert "job-123" in result
        assert "cancelled" in result.lower() or "canceled" in result.lower()

    @pytest.mark.asyncio
    async def test_cancel_job_not_connected(self):
        """Test error when not connected."""
        mock_client = MagicMock()
        mock_client.is_connected = False

        result = await cancel_job(mock_client, job_id="job-123")

        assert "error" in result.lower() or "not connected" in result.lower()
