# Description: Verify all main packages can be imported.
# Description: Validates dependencies are installed correctly.
"""Verify all main packages can be imported."""
import importlib.util


def test_quantum_mcp_imports():
    """Test that quantum_mcp package imports."""
    from quantum_mcp import __version__

    assert __version__ == "0.1.0"


def test_external_dependencies():
    """Test external packages are available."""
    import numpy
    import pydantic
    import scipy

    assert numpy is not None
    assert scipy is not None
    assert pydantic is not None


def test_azure_quantum_installed():
    """Test azure-quantum package is installed."""
    spec = importlib.util.find_spec("azure.quantum")
    assert spec is not None, "azure-quantum not installed"


def test_qiskit_installed():
    """Test qiskit package is installed."""
    spec = importlib.util.find_spec("qiskit")
    assert spec is not None, "qiskit not installed"


def test_mcp_installed():
    """Test mcp package is installed."""
    spec = importlib.util.find_spec("mcp")
    assert spec is not None, "mcp not installed"
