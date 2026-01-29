# Description: Pytest configuration and shared fixtures.
# Description: Provides common test utilities and mock settings.
"""Pytest configuration and fixtures."""

import pytest

from quantum_mcp.config import Settings


@pytest.fixture
def mock_settings() -> Settings:
    """Provide test settings that don't require Azure credentials."""
    return Settings(
        _env_file=None,
        azure_quantum_workspace_id="test-workspace",
        azure_quantum_resource_group="test-rg",
        azure_quantum_subscription_id="test-sub",
        azure_quantum_location="eastus",
        azure_client_id="test-client",
        azure_tenant_id="test-tenant",
        azure_client_secret="test-secret",
        default_backend="ionq.simulator",
        max_shots=100,
        budget_limit_usd=1.0,
        log_level="DEBUG",
    )


@pytest.fixture
def settings_no_azure() -> Settings:
    """Provide settings without Azure credentials."""
    return Settings(
        _env_file=None,
        azure_quantum_workspace_id="",
        azure_quantum_resource_group="",
        azure_quantum_subscription_id="",
        azure_client_id="",
        azure_tenant_id="",
        azure_client_secret="",
        default_backend="ionq.simulator",
        max_shots=100,
    )
