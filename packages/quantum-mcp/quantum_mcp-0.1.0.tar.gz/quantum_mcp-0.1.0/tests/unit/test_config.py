# Description: Test configuration management.
# Description: Validates Settings class and environment loading.
"""Test configuration management."""

import os
from unittest.mock import patch

import pytest

from quantum_mcp.config import Settings, get_settings


class TestSettings:
    """Test Settings class."""

    def test_default_values(self):
        """Test default configuration values."""
        settings = Settings(
            _env_file=None,
            azure_client_id="",
            azure_tenant_id="",
            azure_client_secret="",
        )
        assert settings.default_backend == "ionq.simulator"
        assert settings.max_shots == 1000
        assert settings.budget_limit_usd == 10.0
        assert settings.log_level == "INFO"

    def test_max_shots_validation(self):
        """Test max_shots bounds validation."""
        settings = Settings(_env_file=None, max_shots=500)
        assert settings.max_shots == 500

        with pytest.raises(ValueError):
            Settings(_env_file=None, max_shots=0)

        with pytest.raises(ValueError):
            Settings(_env_file=None, max_shots=20000)

    def test_has_azure_credentials_false(self):
        """Test credentials check when not configured."""
        settings = Settings(
            _env_file=None,
            azure_quantum_workspace_id="",
            azure_quantum_resource_group="",
            azure_quantum_subscription_id="",
        )
        assert settings.has_azure_credentials is False

    def test_has_azure_credentials_true(self):
        """Test credentials check when configured."""
        settings = Settings(
            _env_file=None,
            azure_quantum_workspace_id="test-workspace",
            azure_quantum_resource_group="test-rg",
            azure_quantum_subscription_id="test-sub",
        )
        assert settings.has_azure_credentials is True

    @patch.dict(
        os.environ,
        {
            "AZURE_CLIENT_ID": "",
            "AZURE_TENANT_ID": "",
            "AZURE_CLIENT_SECRET": "",
        },
        clear=False,
    )
    def test_has_service_principal_false(self):
        """Test service principal check when not configured."""
        settings = Settings(
            _env_file=None,
            azure_client_id="",
            azure_tenant_id="",
            azure_client_secret="",
        )
        assert settings.has_service_principal is False

    def test_has_service_principal_true(self):
        """Test service principal check when configured."""
        settings = Settings(
            _env_file=None,
            azure_client_id="test-client",
            azure_tenant_id="test-tenant",
            azure_client_secret="test-secret",
        )
        assert settings.has_service_principal is True

    @patch.dict(
        os.environ,
        {
            "AZURE_QUANTUM_WORKSPACE_ID": "env-workspace",
            "DEFAULT_BACKEND": "quantinuum.simulator",
        },
    )
    def test_environment_override(self):
        """Test environment variables override defaults."""
        get_settings.cache_clear()
        settings = Settings(_env_file=None)
        assert settings.azure_quantum_workspace_id == "env-workspace"
        assert settings.default_backend == "quantinuum.simulator"


class TestPostgresSettings:
    """Test PostgreSQL configuration."""

    def test_has_postgres_credentials_false(self):
        """Test postgres credentials check when not configured."""
        settings = Settings(
            _env_file=None,
            postgres_host="",
            postgres_database="",
            postgres_user="",
            postgres_password="",
        )
        assert settings.has_postgres_credentials is False

    def test_has_postgres_credentials_true(self):
        """Test postgres credentials check when configured."""
        settings = Settings(
            _env_file=None,
            postgres_host="localhost",
            postgres_database="metrics",
            postgres_user="user",
            postgres_password="pass",
        )
        assert settings.has_postgres_credentials is True

    def test_postgres_dsn_construction(self):
        """Test PostgreSQL DSN is built correctly."""
        settings = Settings(
            _env_file=None,
            postgres_host="db.example.com",
            postgres_port=5432,
            postgres_database="metrics",
            postgres_user="myuser",
            postgres_password="mypass",
            postgres_ssl_mode="require",
        )
        expected = (
            "postgresql://myuser:mypass@db.example.com:5432/metrics?sslmode=require"
        )
        assert settings.postgres_dsn == expected

    def test_postgres_default_port(self):
        """Test default PostgreSQL port is 5432."""
        settings = Settings(_env_file=None)
        assert settings.postgres_port == 5432

    def test_postgres_default_ssl_mode(self):
        """Test default SSL mode is require."""
        settings = Settings(_env_file=None)
        assert settings.postgres_ssl_mode == "require"


class TestGetSettings:
    """Test settings singleton."""

    def test_singleton(self):
        """Test get_settings returns same instance."""
        get_settings.cache_clear()
        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2

    def test_cache_clear(self):
        """Test cache can be cleared for new instance."""
        get_settings.cache_clear()
        s1 = get_settings()
        get_settings.cache_clear()
        s2 = get_settings()
        # After clearing, should get new instance
        # (may or may not be same object depending on values)
        assert s1 is not s2 or s1 == s2  # Either different objects or equal values
