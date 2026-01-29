# Description: Test QuantumClient class.
# Description: Validates connection management and client behavior.
"""Test QuantumClient class."""

from unittest.mock import MagicMock, patch

import pytest

from quantum_mcp.client import QuantumClient
from quantum_mcp.config import Settings


class TestQuantumClientInit:
    """Test QuantumClient initialization."""

    def test_init_with_settings(self, mock_settings: Settings):
        """Test client initializes with settings."""
        client = QuantumClient(mock_settings)
        assert client.settings is mock_settings
        assert client.is_connected is False

    def test_init_stores_settings(self, mock_settings: Settings):
        """Test settings are accessible."""
        client = QuantumClient(mock_settings)
        assert client.settings.default_backend == mock_settings.default_backend


class TestQuantumClientConnection:
    """Test connection management."""

    @pytest.mark.asyncio
    async def test_connect_without_credentials_raises(
        self, settings_no_azure: Settings
    ):
        """Test connect raises when credentials missing."""
        client = QuantumClient(settings_no_azure)
        with pytest.raises(ValueError, match="credentials not configured"):
            await client.connect()

    @pytest.mark.asyncio
    async def test_connect_success(self, mock_settings: Settings):
        """Test successful connection with mocked Azure."""
        with patch("azure.quantum.Workspace") as mock_ws:
            mock_ws.return_value = MagicMock()

            client = QuantumClient(mock_settings)
            await client.connect()

            assert client.is_connected is True
            mock_ws.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect(self, mock_settings: Settings):
        """Test disconnect cleans up."""
        with patch("azure.quantum.Workspace"):
            client = QuantumClient(mock_settings)
            await client.connect()
            assert client.is_connected is True

            await client.disconnect()
            assert client.is_connected is False

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_settings: Settings):
        """Test async context manager."""
        with patch("azure.quantum.Workspace"):
            async with QuantumClient(mock_settings) as client:
                assert client.is_connected is True
            assert client.is_connected is False

    @pytest.mark.asyncio
    async def test_connect_already_connected(self, mock_settings: Settings):
        """Test connect when already connected is no-op."""
        with patch("azure.quantum.Workspace") as mock_ws:
            client = QuantumClient(mock_settings)
            await client.connect()
            await client.connect()

            assert mock_ws.call_count == 1
