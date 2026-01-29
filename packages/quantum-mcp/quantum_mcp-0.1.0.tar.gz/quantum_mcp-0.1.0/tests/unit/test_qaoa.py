# Description: Test QAOA circuit builders and algorithm.
# Description: Validates cost/mixer construction, MaxCut encoding, and optimization.
"""Test QAOA circuit builders and algorithm."""

import pytest
from qiskit import QuantumCircuit

from quantum_mcp.circuits.qaoa import (
    QAOACostFunction,
    QAOAResult,
    build_qaoa_circuit,
    encode_maxcut_problem,
    run_qaoa,
)


class TestQAOACostFunction:
    """Test QAOA cost function dataclass."""

    def test_cost_function_creation(self):
        """Test creating a cost function."""
        edges = [(0, 1), (1, 2)]
        cost = QAOACostFunction(edges=edges, num_qubits=3)

        assert cost.edges == edges
        assert cost.num_qubits == 3

    def test_cost_function_with_weights(self):
        """Test cost function with edge weights."""
        edges = [(0, 1), (1, 2)]
        weights = [1.0, 2.0]
        cost = QAOACostFunction(edges=edges, num_qubits=3, weights=weights)

        assert cost.weights == weights


class TestMaxCutEncoding:
    """Test MaxCut problem encoding."""

    def test_encode_triangle(self):
        """Test encoding a triangle graph."""
        edges = [(0, 1), (1, 2), (0, 2)]
        cost = encode_maxcut_problem(edges)

        assert cost.num_qubits == 3
        assert len(cost.edges) == 3

    def test_encode_line_graph(self):
        """Test encoding a line graph."""
        edges = [(0, 1), (1, 2), (2, 3)]
        cost = encode_maxcut_problem(edges)

        assert cost.num_qubits == 4
        assert len(cost.edges) == 3


class TestQAOACircuit:
    """Test QAOA circuit builder."""

    def test_build_qaoa_circuit(self):
        """Test building QAOA circuit."""
        edges = [(0, 1), (1, 2)]
        cost = QAOACostFunction(edges=edges, num_qubits=3)
        circuit = build_qaoa_circuit(cost, layers=1)

        assert isinstance(circuit, QuantumCircuit)
        assert circuit.num_qubits == 3
        assert circuit.num_parameters > 0

    def test_qaoa_circuit_layers(self):
        """Test QAOA circuit depth with layers."""
        edges = [(0, 1)]
        cost = QAOACostFunction(edges=edges, num_qubits=2)

        circuit_p1 = build_qaoa_circuit(cost, layers=1)
        circuit_p2 = build_qaoa_circuit(cost, layers=2)

        # More layers means more parameters
        assert circuit_p2.num_parameters > circuit_p1.num_parameters

    def test_qaoa_circuit_parameterized(self):
        """Test QAOA circuit is parameterized."""
        edges = [(0, 1)]
        cost = QAOACostFunction(edges=edges, num_qubits=2)
        circuit = build_qaoa_circuit(cost, layers=1)

        assert len(circuit.parameters) > 0
        # Should have gamma and beta parameters
        param_names = [p.name for p in circuit.parameters]
        assert any("gamma" in name for name in param_names)
        assert any("beta" in name for name in param_names)


class TestQAOAAlgorithm:
    """Test QAOA optimization."""

    @pytest.mark.asyncio
    async def test_qaoa_runs(self):
        """Test QAOA algorithm runs without error."""
        edges = [(0, 1), (1, 2)]
        result = await run_qaoa(
            edges=edges,
            layers=1,
            optimizer="COBYLA",
            max_iterations=10,
            shots=100,
        )

        assert isinstance(result, QAOAResult)
        assert result.optimal_cost is not None
        assert result.optimal_bitstring is not None

    @pytest.mark.asyncio
    async def test_qaoa_maxcut_small(self):
        """Test QAOA on small MaxCut problem."""
        # Triangle graph - optimal cut is 2
        edges = [(0, 1), (1, 2), (0, 2)]
        result = await run_qaoa(
            edges=edges,
            layers=2,
            optimizer="COBYLA",
            max_iterations=50,
            shots=500,
        )

        assert isinstance(result, QAOAResult)
        # Optimal cut for triangle is 2 (any 2-1 partition)
        assert result.optimal_cost <= 0  # Cost is negative of cuts

    @pytest.mark.asyncio
    async def test_qaoa_convergence_history(self):
        """Test QAOA returns convergence history."""
        edges = [(0, 1)]
        result = await run_qaoa(
            edges=edges,
            layers=1,
            optimizer="COBYLA",
            max_iterations=10,
            shots=100,
        )

        assert result.convergence_history is not None
        assert len(result.convergence_history) > 0


class TestQAOAResult:
    """Test QAOAResult dataclass."""

    def test_qaoa_result_fields(self):
        """Test QAOAResult has expected fields."""
        result = QAOAResult(
            optimal_cost=-2.5,
            optimal_parameters=[0.1, 0.2],
            optimal_bitstring="101",
            num_iterations=10,
            optimizer="COBYLA",
            convergence_history=[-1.0, -2.0, -2.5],
        )

        assert result.optimal_cost == -2.5
        assert len(result.optimal_parameters) == 2
        assert result.optimal_bitstring == "101"
        assert result.num_iterations == 10
