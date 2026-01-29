# Description: Test MCP tools for quantum operations.
# Description: Validates tool implementations for backends, simulation, and cost.
"""Test MCP tools for quantum operations."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from quantum_mcp.client import BackendInfo, CostEstimate
from quantum_mcp.config import Settings
from quantum_mcp.tools.backend_tools import (
    estimate_cost,
    list_backends,
)
from quantum_mcp.tools.simulation_tools import (
    simulate_circuit,
)


@pytest.fixture
def mock_settings():
    """Create mock settings."""
    return Settings(
        _env_file=None,
        azure_quantum_workspace_id="test-workspace",
        azure_quantum_resource_group="test-rg",
        azure_quantum_subscription_id="test-sub",
    )


class TestListBackends:
    """Test quantum_list_backends tool."""

    @pytest.mark.asyncio
    async def test_list_backends_returns_json(self, mock_settings: Settings):
        """Test list_backends returns JSON formatted result."""
        mock_backends = [
            BackendInfo(
                id="ionq.simulator",
                provider="ionq",
                backend_type="simulator",
                num_qubits=29,
                status="online",
            ),
            BackendInfo(
                id="ionq.qpu",
                provider="ionq",
                backend_type="hardware",
                num_qubits=29,
                status="online",
            ),
        ]

        mock_client = MagicMock()
        mock_client.list_backends = AsyncMock(return_value=mock_backends)
        mock_client.is_connected = True

        result = await list_backends(mock_client)

        assert "ionq.simulator" in result
        assert "ionq.qpu" in result
        assert "simulator" in result.lower()

    @pytest.mark.asyncio
    async def test_list_backends_filter_simulators(self, mock_settings: Settings):
        """Test list_backends can filter to simulators only."""
        mock_backends = [
            BackendInfo(
                id="ionq.simulator",
                provider="ionq",
                backend_type="simulator",
                num_qubits=29,
                status="online",
            ),
            BackendInfo(
                id="ionq.qpu",
                provider="ionq",
                backend_type="hardware",
                num_qubits=29,
                status="online",
            ),
        ]

        mock_client = MagicMock()
        mock_client.list_backends = AsyncMock(return_value=mock_backends)
        mock_client.is_connected = True

        result = await list_backends(mock_client, simulators_only=True)

        assert "ionq.simulator" in result
        assert "ionq.qpu" not in result

    @pytest.mark.asyncio
    async def test_list_backends_not_connected(self):
        """Test list_backends when not connected."""
        mock_client = MagicMock()
        mock_client.is_connected = False

        result = await list_backends(mock_client)

        assert "not connected" in result.lower() or "error" in result.lower()


class TestEstimateCost:
    """Test quantum_estimate_cost tool."""

    @pytest.mark.asyncio
    async def test_estimate_cost_simulator(self):
        """Test cost estimation for simulator."""
        mock_client = MagicMock()
        mock_client.is_connected = True
        mock_client.estimate_cost = AsyncMock(
            return_value=CostEstimate(
                backend="ionq.simulator",
                shots=1000,
                estimated_cost_usd=0.0,
                notes="Simulator (free)",
            )
        )

        result = await estimate_cost(mock_client, backend="ionq.simulator", shots=1000)

        assert "$0.00" in result or "free" in result.lower()
        assert "ionq.simulator" in result

    @pytest.mark.asyncio
    async def test_estimate_cost_hardware(self):
        """Test cost estimation for hardware."""
        mock_client = MagicMock()
        mock_client.is_connected = True
        mock_client.estimate_cost = AsyncMock(
            return_value=CostEstimate(
                backend="ionq.qpu",
                shots=1000,
                estimated_cost_usd=0.03,
                notes="$0.00003/shot",
            )
        )

        result = await estimate_cost(mock_client, backend="ionq.qpu", shots=1000)

        assert "0.03" in result or "$" in result
        assert "ionq.qpu" in result


class TestSimulateCircuit:
    """Test quantum_simulate tool."""

    @pytest.mark.asyncio
    async def test_simulate_bell_state(self):
        """Test simulating a Bell state circuit."""
        result = await simulate_circuit(
            circuit_type="bell",
            num_qubits=2,
            shots=1000,
        )

        assert "counts" in result.lower() or "result" in result.lower()
        # Bell state should have 00 and 11 outcomes
        assert "00" in result or "11" in result

    @pytest.mark.asyncio
    async def test_simulate_ghz_state(self):
        """Test simulating a GHZ state circuit."""
        result = await simulate_circuit(
            circuit_type="ghz",
            num_qubits=3,
            shots=1000,
        )

        assert "counts" in result.lower() or "result" in result.lower()
        # GHZ should have 000 and 111 outcomes
        assert "000" in result or "111" in result

    @pytest.mark.asyncio
    async def test_simulate_custom_qasm(self):
        """Test simulating a custom QASM circuit."""
        qasm = """
        OPENQASM 2.0;
        include "qelib1.inc";
        qreg q[2];
        creg c[2];
        h q[0];
        cx q[0], q[1];
        measure q -> c;
        """
        result = await simulate_circuit(
            circuit_type="qasm",
            qasm_string=qasm,
            shots=100,
        )

        assert "counts" in result.lower() or "result" in result.lower()

    @pytest.mark.asyncio
    async def test_simulate_invalid_circuit(self):
        """Test error handling for invalid circuit."""
        result = await simulate_circuit(
            circuit_type="invalid",
            num_qubits=2,
            shots=100,
        )

        assert "error" in result.lower() or "invalid" in result.lower()
