# Description: Test circuit conversion and validation.
# Description: Validates Qiskit to Azure Quantum format conversion.
"""Test circuit conversion and validation."""

import pytest
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter

from quantum_mcp.circuits.converters import (
    CircuitConverter,
    CircuitInfo,
    CircuitValidationError,
)


class TestCircuitInfo:
    """Test CircuitInfo model."""

    def test_circuit_info_from_circuit(self):
        """Test extracting info from a circuit."""
        qc = QuantumCircuit(2, 2)
        qc.h(0)
        qc.cx(0, 1)
        qc.measure([0, 1], [0, 1])

        info = CircuitInfo.from_circuit(qc)

        assert info.num_qubits == 2
        assert info.num_clbits == 2
        assert info.depth >= 2
        assert info.has_measurements is True
        assert info.num_parameters == 0

    def test_circuit_info_parameterized(self):
        """Test info for parameterized circuit."""
        theta = Parameter("theta")
        phi = Parameter("phi")

        qc = QuantumCircuit(1)
        qc.rx(theta, 0)
        qc.ry(phi, 0)

        info = CircuitInfo.from_circuit(qc)

        assert info.num_qubits == 1
        assert info.num_parameters == 2
        assert "theta" in info.parameter_names
        assert "phi" in info.parameter_names

    def test_circuit_info_no_measurements(self):
        """Test circuit without measurements."""
        qc = QuantumCircuit(2)
        qc.h(0)
        qc.cx(0, 1)

        info = CircuitInfo.from_circuit(qc)

        assert info.has_measurements is False


class TestCircuitConverter:
    """Test CircuitConverter functionality."""

    @pytest.fixture
    def converter(self):
        """Create converter instance."""
        return CircuitConverter()

    def test_validate_bell_state(self, converter: CircuitConverter):
        """Test validation of Bell state circuit."""
        qc = QuantumCircuit(2, 2)
        qc.h(0)
        qc.cx(0, 1)
        qc.measure([0, 1], [0, 1])

        result = converter.validate(qc)

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_validate_ghz_state(self, converter: CircuitConverter):
        """Test validation of GHZ state circuit."""
        qc = QuantumCircuit(3, 3)
        qc.h(0)
        qc.cx(0, 1)
        qc.cx(1, 2)
        qc.measure_all()

        result = converter.validate(qc)

        assert result.is_valid is True

    def test_validate_too_many_qubits(self, converter: CircuitConverter):
        """Test validation fails for too many qubits."""
        qc = QuantumCircuit(100, 100)
        qc.h(range(100))
        qc.measure_all()

        result = converter.validate(qc, max_qubits=29)

        assert result.is_valid is False
        assert any("qubits" in err.lower() for err in result.errors)

    def test_validate_unsupported_gate(self, converter: CircuitConverter):
        """Test validation warns for exotic gates."""
        qc = QuantumCircuit(3, 3)
        qc.h(0)
        qc.ccx(0, 1, 2)  # Toffoli gate
        qc.measure_all()

        result = converter.validate(qc)

        # Toffoli should be valid but may have warnings on some backends
        assert result.is_valid is True

    def test_validate_no_measurements(self, converter: CircuitConverter):
        """Test validation warns when no measurements."""
        qc = QuantumCircuit(2)
        qc.h(0)
        qc.cx(0, 1)

        result = converter.validate(qc)

        assert result.is_valid is True
        assert any("measurement" in w.lower() for w in result.warnings)

    def test_add_measurements(self, converter: CircuitConverter):
        """Test adding measurements to circuit."""
        qc = QuantumCircuit(2)
        qc.h(0)
        qc.cx(0, 1)

        result = converter.add_measurements(qc)

        assert result.num_clbits == 2
        info = CircuitInfo.from_circuit(result)
        assert info.has_measurements is True

    def test_add_measurements_already_present(self, converter: CircuitConverter):
        """Test add_measurements when already present."""
        qc = QuantumCircuit(2, 2)
        qc.h(0)
        qc.cx(0, 1)
        qc.measure([0, 1], [0, 1])

        result = converter.add_measurements(qc)

        # Should return same circuit (or copy)
        assert CircuitInfo.from_circuit(result).has_measurements is True

    def test_bind_parameters(self, converter: CircuitConverter):
        """Test parameter binding."""
        theta = Parameter("theta")
        phi = Parameter("phi")

        qc = QuantumCircuit(1, 1)
        qc.rx(theta, 0)
        qc.ry(phi, 0)
        qc.measure(0, 0)

        bound = converter.bind_parameters(qc, {"theta": 1.57, "phi": 3.14})

        info = CircuitInfo.from_circuit(bound)
        assert info.num_parameters == 0

    def test_bind_parameters_missing(self, converter: CircuitConverter):
        """Test error when parameter missing."""
        theta = Parameter("theta")
        phi = Parameter("phi")

        qc = QuantumCircuit(1)
        qc.rx(theta, 0)
        qc.ry(phi, 0)

        with pytest.raises(CircuitValidationError, match="Missing"):
            converter.bind_parameters(qc, {"theta": 1.57})

    def test_bind_parameters_partial_allowed(self, converter: CircuitConverter):
        """Test partial binding when allowed."""
        theta = Parameter("theta")
        phi = Parameter("phi")

        qc = QuantumCircuit(1)
        qc.rx(theta, 0)
        qc.ry(phi, 0)

        result = converter.bind_parameters(
            qc, {"theta": 1.57}, allow_partial=True
        )

        info = CircuitInfo.from_circuit(result)
        assert info.num_parameters == 1
        assert "phi" in info.parameter_names

    def test_prepare_for_backend_simulator(self, converter: CircuitConverter):
        """Test preparing circuit for simulator."""
        qc = QuantumCircuit(2, 2)
        qc.h(0)
        qc.cx(0, 1)
        qc.measure([0, 1], [0, 1])

        result = converter.prepare_for_backend(qc, "ionq.simulator")

        assert result is not None
        info = CircuitInfo.from_circuit(result)
        assert info.has_measurements is True

    def test_prepare_for_backend_adds_measurements(self, converter: CircuitConverter):
        """Test preparing circuit adds measurements if needed."""
        qc = QuantumCircuit(2)
        qc.h(0)
        qc.cx(0, 1)

        result = converter.prepare_for_backend(qc, "ionq.simulator")

        info = CircuitInfo.from_circuit(result)
        assert info.has_measurements is True

    def test_prepare_for_backend_validates(self, converter: CircuitConverter):
        """Test preparing circuit validates against backend."""
        qc = QuantumCircuit(50, 50)
        qc.h(range(50))
        qc.measure_all()

        with pytest.raises(CircuitValidationError, match="qubits"):
            converter.prepare_for_backend(qc, "ionq.simulator", max_qubits=29)


class TestBackendRouting:
    """Test backend routing logic."""

    @pytest.fixture
    def converter(self):
        """Create converter instance."""
        return CircuitConverter()

    def test_route_to_simulator_small_circuit(self, converter: CircuitConverter):
        """Test routing small circuit to simulator."""
        qc = QuantumCircuit(5, 5)
        qc.h(range(5))
        qc.measure_all()

        backend = converter.recommend_backend(qc, prefer_simulator=True)

        assert "simulator" in backend.lower() or "sim" in backend.lower()

    def test_route_to_hardware_when_requested(self, converter: CircuitConverter):
        """Test routing to hardware when explicitly requested."""
        qc = QuantumCircuit(5, 5)
        qc.h(range(5))
        qc.measure_all()

        backend = converter.recommend_backend(qc, prefer_simulator=False)

        assert backend is not None
        # Should return hardware backend when explicitly requested
        assert backend == "ionq.qpu"

    def test_route_large_circuit_to_simulator(self, converter: CircuitConverter):
        """Test large circuit defaults to simulator."""
        qc = QuantumCircuit(25, 25)
        qc.h(range(25))
        qc.measure_all()

        backend = converter.recommend_backend(qc)

        # Large circuits should prefer simulator
        assert "simulator" in backend.lower() or "sim" in backend.lower()
