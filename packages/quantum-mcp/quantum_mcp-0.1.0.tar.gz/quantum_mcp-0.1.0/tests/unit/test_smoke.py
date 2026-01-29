# Description: Smoke tests to verify project setup.
# Description: Validates all packages import and configuration works.
"""Smoke tests to verify project setup."""

import importlib.util


class TestPackageImports:
    """Test all package imports work."""

    def test_main_package(self):
        """Test main package imports."""
        from quantum_mcp import __version__

        assert __version__ == "0.1.0"

    def test_config_module(self):
        """Test config module imports."""
        from quantum_mcp.config import Settings

        settings = Settings(_env_file=None)
        assert settings is not None

    def test_client_module(self):
        """Test client module imports (even if empty)."""
        from quantum_mcp import client

        assert client is not None

    def test_tools_module(self):
        """Test tools module imports."""
        from quantum_mcp import tools

        assert tools is not None

    def test_circuits_module(self):
        """Test circuits module imports."""
        from quantum_mcp import circuits

        assert circuits is not None


class TestExternalDependencies:
    """Test external dependencies are available."""

    def test_numpy_scipy(self):
        """Test numpy and scipy available."""
        import numpy as np

        assert np.array([1, 2, 3]).sum() == 6

    def test_pydantic(self):
        """Test pydantic available."""
        from pydantic import BaseModel

        class TestModel(BaseModel):
            value: int

        m = TestModel(value=42)
        assert m.value == 42

    def test_structlog(self):
        """Test structlog available."""
        import structlog

        logger = structlog.get_logger()
        assert logger is not None

    def test_tenacity(self):
        """Test tenacity available."""
        from tenacity import retry

        assert retry is not None

    def test_azure_quantum_installed(self):
        """Test azure-quantum package is installed."""
        spec = importlib.util.find_spec("azure.quantum")
        assert spec is not None, "azure-quantum not installed"

    def test_qiskit_installed(self):
        """Test qiskit package is installed."""
        spec = importlib.util.find_spec("qiskit")
        assert spec is not None, "qiskit not installed"

    def test_mcp_installed(self):
        """Test mcp package is installed."""
        spec = importlib.util.find_spec("mcp")
        assert spec is not None, "mcp not installed"


class TestConfigurationSingleton:
    """Test configuration singleton behavior."""

    def test_singleton_returns_same_instance(self):
        """Test get_settings returns same instance."""
        from quantum_mcp import get_settings

        get_settings.cache_clear()
        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2

    def test_settings_can_be_created_with_values(self):
        """Test Settings can be instantiated with values."""
        from quantum_mcp import Settings

        settings = Settings(
            _env_file=None,
            default_backend="test.simulator",
            max_shots=500,
            budget_limit_usd=5.0,
        )
        assert settings.default_backend == "test.simulator"
        assert settings.max_shots == 500
        assert settings.budget_limit_usd == 5.0


class TestProjectStructure:
    """Test project structure is correct."""

    def test_version_defined(self):
        """Test version is defined."""
        from quantum_mcp import __version__

        assert __version__
        parts = __version__.split(".")
        assert len(parts) >= 2

    def test_all_exports_defined(self):
        """Test __all__ exports are available."""
        import quantum_mcp

        for name in quantum_mcp.__all__:
            assert hasattr(quantum_mcp, name)
