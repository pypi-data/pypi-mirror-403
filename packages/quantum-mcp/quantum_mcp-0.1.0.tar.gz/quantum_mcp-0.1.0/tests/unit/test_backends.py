# Description: Test backend enumeration.
# Description: Validates BackendInfo model and listing functionality.
"""Test backend enumeration."""

from unittest.mock import MagicMock, patch

import pytest

from quantum_mcp.client import (
    BackendInfo,
    BackendNotFoundError,
    ConnectionError,
    QuantumClient,
)
from quantum_mcp.config import Settings


class TestBackendInfo:
    """Test BackendInfo dataclass."""

    def test_simulator_detection(self):
        """Test is_simulator property."""
        sim = BackendInfo(
            id="ionq.simulator",
            provider="ionq",
            backend_type="simulator",
            num_qubits=29,
            status="online",
        )
        assert sim.is_simulator is True

        hw = BackendInfo(
            id="ionq.qpu",
            provider="ionq",
            backend_type="hardware",
            num_qubits=29,
            status="online",
        )
        assert hw.is_simulator is False

    def test_availability_check(self):
        """Test is_available property."""
        online = BackendInfo(
            id="test",
            provider="test",
            backend_type="simulator",
            num_qubits=10,
            status="online",
        )
        assert online.is_available is True

        offline = BackendInfo(
            id="test",
            provider="test",
            backend_type="simulator",
            num_qubits=10,
            status="offline",
        )
        assert offline.is_available is False


class TestListBackends:
    """Test backend listing."""

    @pytest.mark.asyncio
    async def test_list_backends_not_connected(self, mock_settings: Settings):
        """Test list_backends raises when not connected."""
        client = QuantumClient(mock_settings)
        with pytest.raises(ConnectionError, match="Not connected"):
            await client.list_backends()

    @pytest.mark.asyncio
    async def test_list_backends_success(self, mock_settings: Settings):
        """Test successful backend listing."""
        mock_target = MagicMock()
        mock_target.name = "ionq.simulator"
        mock_target.num_qubits = 29
        mock_target.current_availability = "online"

        with patch("azure.quantum.Workspace") as mock_ws:
            mock_workspace = MagicMock()
            mock_workspace.get_targets.return_value = [mock_target]
            mock_ws.return_value = mock_workspace

            async with QuantumClient(mock_settings) as client:
                backends = await client.list_backends()

            assert len(backends) == 1
            assert backends[0].id == "ionq.simulator"
            assert backends[0].provider == "ionq"
            assert backends[0].is_simulator is True

    @pytest.mark.asyncio
    async def test_get_backend_info_found(self, mock_settings: Settings):
        """Test getting specific backend info."""
        mock_target = MagicMock()
        mock_target.name = "ionq.simulator"

        with patch("azure.quantum.Workspace") as mock_ws:
            mock_workspace = MagicMock()
            mock_workspace.get_targets.return_value = [mock_target]
            mock_ws.return_value = mock_workspace

            async with QuantumClient(mock_settings) as client:
                backend = await client.get_backend_info("ionq.simulator")

            assert backend.id == "ionq.simulator"

    @pytest.mark.asyncio
    async def test_get_backend_info_not_found(self, mock_settings: Settings):
        """Test error when backend not found."""
        with patch("azure.quantum.Workspace") as mock_ws:
            mock_workspace = MagicMock()
            mock_workspace.get_targets.return_value = []
            mock_ws.return_value = mock_workspace

            async with QuantumClient(mock_settings) as client:
                with pytest.raises(BackendNotFoundError, match="Backend not found"):
                    await client.get_backend_info("nonexistent.backend")
