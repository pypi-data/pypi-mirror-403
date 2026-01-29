# Description: Integration tests for Azure Quantum connection.
# Description: Requires real Azure credentials to run.
"""Integration tests for Azure Quantum connection.

These tests require real Azure credentials and will be skipped
if credentials are not configured.
"""

import os

import pytest

from quantum_mcp.client import BackendInfo, QuantumClient
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


@pytest.mark.integration
class TestRealConnection:
    """Test real Azure Quantum connection."""

    @pytest.mark.asyncio
    async def test_connect_to_workspace(self, real_settings: Settings):
        """Test connecting to real Azure workspace."""
        client = QuantumClient(real_settings)
        await client.connect()

        assert client.is_connected
        await client.disconnect()
        assert not client.is_connected

    @pytest.mark.asyncio
    async def test_context_manager(self, real_settings: Settings):
        """Test context manager with real connection."""
        async with QuantumClient(real_settings) as client:
            assert client.is_connected
        assert not client.is_connected

    @pytest.mark.asyncio
    async def test_list_backends(self, real_settings: Settings):
        """Test listing real backends."""
        async with QuantumClient(real_settings) as client:
            backends = await client.list_backends()

        assert len(backends) > 0
        assert all(isinstance(b, BackendInfo) for b in backends)

        simulators = [b for b in backends if b.is_simulator]
        assert len(simulators) > 0

    @pytest.mark.asyncio
    async def test_get_simulator_info(self, real_settings: Settings):
        """Test getting simulator backend info."""
        async with QuantumClient(real_settings) as client:
            backends = await client.list_backends()

            simulator = next((b for b in backends if b.is_simulator), None)
            assert simulator is not None

            info = await client.get_backend_info(simulator.id)
            assert info.id == simulator.id

    @pytest.mark.asyncio
    async def test_connection_recovery(self, real_settings: Settings):
        """Test reconnection works."""
        client = QuantumClient(real_settings)

        await client.connect()
        await client.disconnect()

        await client.connect()
        backends = await client.list_backends()
        assert len(backends) > 0

        await client.disconnect()
