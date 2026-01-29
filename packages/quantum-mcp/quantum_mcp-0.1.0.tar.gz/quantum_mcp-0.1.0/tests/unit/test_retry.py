# Description: Test retry logic and error handling.
# Description: Validates retry behavior and custom exceptions.
"""Test retry logic and error handling."""

from unittest.mock import MagicMock, patch

import pytest

from quantum_mcp.client import (
    AuthenticationError,
    BackendNotFoundError,
    ConnectionError,
    QuantumClient,
)
from quantum_mcp.config import Settings


class TestRetryLogic:
    """Test retry behavior."""

    @pytest.mark.asyncio
    async def test_connect_retries_on_transient_error(self, mock_settings: Settings):
        """Test connection retries on transient errors."""
        call_count = 0

        def flaky_workspace(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise OSError("Network error")
            return MagicMock()

        with patch(
            "azure.quantum.Workspace",
            side_effect=flaky_workspace,
        ):
            client = QuantumClient(mock_settings)
            await client.connect()

        assert call_count == 3
        assert client.is_connected

    @pytest.mark.asyncio
    async def test_connect_fails_after_max_retries(self, mock_settings: Settings):
        """Test connection fails after max retries."""
        with patch(
            "azure.quantum.Workspace",
            side_effect=OSError("Persistent error"),
        ):
            client = QuantumClient(mock_settings)
            with pytest.raises(ConnectionError):
                await client.connect()


class TestCustomExceptions:
    """Test custom exception handling."""

    @pytest.mark.asyncio
    async def test_authentication_error(self, mock_settings: Settings):
        """Test authentication errors are wrapped."""
        with patch(
            "azure.quantum.Workspace",
            side_effect=Exception("authentication failed"),
        ):
            client = QuantumClient(mock_settings)
            with pytest.raises(AuthenticationError):
                await client.connect()

    @pytest.mark.asyncio
    async def test_backend_not_found_has_details(self, mock_settings: Settings):
        """Test BackendNotFoundError includes available backends."""
        mock_target = MagicMock()
        mock_target.name = "ionq.simulator"

        with patch("azure.quantum.Workspace") as mock_ws:
            mock_workspace = MagicMock()
            mock_workspace.get_targets.return_value = [mock_target]
            mock_ws.return_value = mock_workspace

            async with QuantumClient(mock_settings) as client:
                try:
                    await client.get_backend_info("nonexistent")
                except BackendNotFoundError as e:
                    assert "ionq.simulator" in e.details["available"]
