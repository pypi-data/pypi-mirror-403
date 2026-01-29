# Description: Circuit format converters for Azure Quantum compatibility.
# Description: Validates circuits and prepares them for Azure Quantum execution.
"""Circuit converters and validators for Azure Quantum."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from qiskit import QuantumCircuit


class CircuitValidationError(Exception):
    """Error during circuit validation."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.details = details or {}


@dataclass
class CircuitInfo:
    """Information extracted from a quantum circuit."""

    num_qubits: int
    num_clbits: int
    depth: int
    gate_counts: dict[str, int]
    has_measurements: bool
    num_parameters: int
    parameter_names: list[str]

    @classmethod
    def from_circuit(cls, circuit: "QuantumCircuit") -> "CircuitInfo":
        """Extract info from a Qiskit QuantumCircuit.

        Args:
            circuit: Qiskit QuantumCircuit to analyze

        Returns:
            CircuitInfo with circuit statistics
        """
        gate_counts: dict[str, int] = {}
        has_measurements = False

        for instruction in circuit.data:
            name = instruction.operation.name
            gate_counts[name] = gate_counts.get(name, 0) + 1
            if name == "measure":
                has_measurements = True

        parameters = list(circuit.parameters)

        return cls(
            num_qubits=circuit.num_qubits,
            num_clbits=circuit.num_clbits,
            depth=circuit.depth(),
            gate_counts=gate_counts,
            has_measurements=has_measurements,
            num_parameters=len(parameters),
            parameter_names=[p.name for p in parameters],
        )


@dataclass
class ValidationResult:
    """Result of circuit validation."""

    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class CircuitConverter:
    """Converter for preparing circuits for Azure Quantum execution.

    Handles validation, measurement addition, parameter binding, and
    backend routing for Qiskit circuits.
    """

    # Default backend constraints
    DEFAULT_MAX_QUBITS = 29  # IonQ simulator limit
    DEFAULT_HARDWARE_BACKEND = "ionq.qpu"
    DEFAULT_SIMULATOR_BACKEND = "ionq.simulator"

    # Gate sets by provider
    IONQ_GATES = {"h", "x", "y", "z", "rx", "ry", "rz", "cx", "cz", "swap", "ccx", "id"}
    QUANTINUUM_GATES = {"h", "x", "y", "z", "rx", "ry", "rz", "cx", "cz", "swap", "ccx"}
    RIGETTI_GATES = {"h", "x", "y", "z", "rx", "ry", "rz", "cx", "cz", "swap", "ccx"}

    def validate(
        self,
        circuit: "QuantumCircuit",
        max_qubits: int | None = None,
        required_gates: set[str] | None = None,
    ) -> ValidationResult:
        """Validate a circuit for Azure Quantum execution.

        Args:
            circuit: Circuit to validate
            max_qubits: Maximum allowed qubits (default: 29)
            required_gates: Set of allowed gate names (default: IonQ gates)

        Returns:
            ValidationResult with errors and warnings
        """
        max_qubits = max_qubits or self.DEFAULT_MAX_QUBITS
        allowed_gates = required_gates or self.IONQ_GATES

        errors: list[str] = []
        warnings: list[str] = []

        info = CircuitInfo.from_circuit(circuit)

        # Check qubit count
        if info.num_qubits > max_qubits:
            errors.append(
                f"Circuit has {info.num_qubits} qubits but backend "
                f"supports max {max_qubits} qubits"
            )

        # Check for measurements
        if not info.has_measurements:
            warnings.append(
                "Circuit has no measurements. Measurements will be added automatically."
            )

        # Check for unbound parameters
        if info.num_parameters > 0:
            warnings.append(
                f"Circuit has {info.num_parameters} unbound parameters: "
                f"{info.parameter_names}. Bind parameters before execution."
            )

        # Check for unsupported gates
        for gate_name in info.gate_counts:
            if gate_name not in allowed_gates and gate_name != "measure":
                # Just warn, don't fail - Azure may decompose these
                warnings.append(
                    f"Gate '{gate_name}' may not be natively supported. "
                    "Circuit may be decomposed."
                )

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    def add_measurements(self, circuit: "QuantumCircuit") -> "QuantumCircuit":
        """Add measurement operations to all qubits.

        Args:
            circuit: Circuit to add measurements to

        Returns:
            New circuit with measurements added
        """
        info = CircuitInfo.from_circuit(circuit)
        if info.has_measurements:
            return circuit.copy()

        # Create new circuit with classical bits if needed
        new_circuit = circuit.copy()
        if new_circuit.num_clbits < new_circuit.num_qubits:
            from qiskit import ClassicalRegister

            creg = ClassicalRegister(new_circuit.num_qubits - new_circuit.num_clbits)
            new_circuit.add_register(creg)

        new_circuit.measure_all(add_bits=False)
        return new_circuit

    def bind_parameters(
        self,
        circuit: "QuantumCircuit",
        parameters: dict[str, float],
        allow_partial: bool = False,
    ) -> "QuantumCircuit":
        """Bind parameter values to a parameterized circuit.

        Args:
            circuit: Parameterized circuit
            parameters: Dict mapping parameter names to values
            allow_partial: If True, allow some parameters to remain unbound

        Returns:
            Circuit with parameters bound

        Raises:
            CircuitValidationError: If required parameters are missing
        """
        info = CircuitInfo.from_circuit(circuit)

        # Check for missing parameters
        missing = set(info.parameter_names) - set(parameters.keys())
        if missing and not allow_partial:
            raise CircuitValidationError(
                f"Missing parameter values: {missing}",
                details={"missing": list(missing), "provided": list(parameters.keys())},
            )

        # Build parameter dict using circuit's Parameter objects
        param_dict = {}
        for param in circuit.parameters:
            if param.name in parameters:
                param_dict[param] = parameters[param.name]

        return circuit.assign_parameters(param_dict)

    def prepare_for_backend(
        self,
        circuit: "QuantumCircuit",
        backend: str,
        max_qubits: int | None = None,
    ) -> "QuantumCircuit":
        """Prepare a circuit for execution on a specific backend.

        Validates, adds measurements if needed, and returns prepared circuit.

        Args:
            circuit: Circuit to prepare
            backend: Target backend ID
            max_qubits: Override max qubits for validation

        Returns:
            Prepared circuit ready for execution

        Raises:
            CircuitValidationError: If circuit is invalid for backend
        """
        # Determine max qubits based on backend
        if max_qubits is None:
            max_qubits = self._get_backend_max_qubits(backend)

        # Validate
        result = self.validate(circuit, max_qubits=max_qubits)
        if not result.is_valid:
            raise CircuitValidationError(
                f"Circuit invalid for backend {backend}: {result.errors}",
                details={"errors": result.errors, "backend": backend},
            )

        # Add measurements if needed
        prepared = self.add_measurements(circuit)

        return prepared

    def recommend_backend(
        self,
        circuit: "QuantumCircuit",
        prefer_simulator: bool = True,
    ) -> str:
        """Recommend a backend for the given circuit.

        Args:
            circuit: Circuit to route
            prefer_simulator: If True, prefer simulators (default: True)

        Returns:
            Recommended backend ID
        """
        info = CircuitInfo.from_circuit(circuit)

        # Large circuits should use simulator
        if info.num_qubits > 10:
            return self.DEFAULT_SIMULATOR_BACKEND

        # Deep circuits benefit from simulator (noise-free)
        if info.depth > 50:
            return self.DEFAULT_SIMULATOR_BACKEND

        # Default based on preference
        if prefer_simulator:
            return self.DEFAULT_SIMULATOR_BACKEND
        else:
            return self.DEFAULT_HARDWARE_BACKEND

    def _get_backend_max_qubits(self, backend: str) -> int:
        """Get maximum qubits for a backend.

        Args:
            backend: Backend ID

        Returns:
            Maximum qubit count
        """
        backend_lower = backend.lower()

        if "ionq" in backend_lower:
            if "simulator" in backend_lower:
                return 29
            return 29  # IonQ hardware

        if "quantinuum" in backend_lower:
            if "sim" in backend_lower:
                return 32
            return 20  # H1 hardware

        if "rigetti" in backend_lower:
            if "sim" in backend_lower or "qvm" in backend_lower:
                return 32
            return 80  # Aspen hardware

        return self.DEFAULT_MAX_QUBITS
