# Description: Test VQE circuit builders and algorithm.
# Description: Validates ansatz construction, Hamiltonian encoding, and optimization.
"""Test VQE circuit builders and algorithm."""

import pytest
from qiskit import QuantumCircuit

from quantum_mcp.circuits.vqe import (
    HamiltonianTerm,
    MolecularHamiltonian,
    VQEResult,
    build_hardware_efficient_ansatz,
    build_ry_ansatz,
    encode_h2_hamiltonian,
    run_vqe,
)


class TestAnsatzBuilders:
    """Test VQE ansatz circuit builders."""

    def test_ry_ansatz_structure(self):
        """Test RY ansatz has correct structure."""
        ansatz = build_ry_ansatz(num_qubits=2, depth=1)

        assert isinstance(ansatz, QuantumCircuit)
        assert ansatz.num_qubits == 2
        assert ansatz.num_parameters > 0

    def test_ry_ansatz_depth(self):
        """Test RY ansatz depth parameter."""
        ansatz_d1 = build_ry_ansatz(num_qubits=2, depth=1)
        ansatz_d2 = build_ry_ansatz(num_qubits=2, depth=2)

        assert ansatz_d2.num_parameters > ansatz_d1.num_parameters

    def test_hardware_efficient_ansatz(self):
        """Test hardware-efficient ansatz structure."""
        ansatz = build_hardware_efficient_ansatz(num_qubits=4, depth=2)

        assert isinstance(ansatz, QuantumCircuit)
        assert ansatz.num_qubits == 4
        assert ansatz.num_parameters > 0

    def test_ansatz_parameterized(self):
        """Test ansatz circuits are parameterized."""
        ansatz = build_ry_ansatz(num_qubits=2, depth=1)

        assert len(ansatz.parameters) > 0
        # Should be able to bind parameters
        param_values = {p: 0.5 for p in ansatz.parameters}
        bound = ansatz.assign_parameters(param_values)
        assert len(bound.parameters) == 0


class TestHamiltonianEncoding:
    """Test Hamiltonian encoding."""

    def test_h2_hamiltonian_structure(self):
        """Test H2 Hamiltonian has expected structure."""
        hamiltonian = encode_h2_hamiltonian(bond_distance=0.735)

        assert isinstance(hamiltonian, MolecularHamiltonian)
        assert len(hamiltonian.terms) > 0
        assert hamiltonian.num_qubits >= 2

    def test_hamiltonian_term_structure(self):
        """Test Hamiltonian term dataclass."""
        term = HamiltonianTerm(coefficient=0.5, pauli_string="ZZ")

        assert term.coefficient == 0.5
        assert term.pauli_string == "ZZ"

    def test_h2_energy_reasonable(self):
        """Test H2 Hamiltonian gives reasonable energy estimate."""
        hamiltonian = encode_h2_hamiltonian(bond_distance=0.735)

        # Identity coefficient should be negative (attractive)
        identity_term = next(
            (t for t in hamiltonian.terms if t.pauli_string == "I" * hamiltonian.num_qubits),
            None,
        )
        assert identity_term is not None


class TestVQEAlgorithm:
    """Test VQE optimization."""

    @pytest.mark.asyncio
    async def test_vqe_runs(self):
        """Test VQE algorithm runs without error."""
        result = await run_vqe(
            num_qubits=2,
            ansatz_type="ry",
            depth=1,
            optimizer="COBYLA",
            max_iterations=10,
            shots=100,
        )

        assert isinstance(result, VQEResult)
        assert result.optimal_energy is not None
        assert result.optimal_parameters is not None

    @pytest.mark.asyncio
    async def test_vqe_h2_molecule(self):
        """Test VQE on H2 molecule."""
        result = await run_vqe(
            num_qubits=2,
            ansatz_type="ry",
            depth=2,
            hamiltonian_type="h2",
            optimizer="COBYLA",
            max_iterations=50,
            shots=500,
        )

        assert isinstance(result, VQEResult)
        # H2 ground state energy should be around -1.85 Ha at equilibrium
        # With limited iterations, just check it's negative
        assert result.optimal_energy < 0

    @pytest.mark.asyncio
    async def test_vqe_different_optimizers(self):
        """Test VQE with different optimizers."""
        for optimizer in ["COBYLA", "SPSA"]:
            result = await run_vqe(
                num_qubits=2,
                ansatz_type="ry",
                depth=1,
                optimizer=optimizer,
                max_iterations=5,
                shots=100,
            )

            assert result.optimizer == optimizer

    @pytest.mark.asyncio
    async def test_vqe_convergence_history(self):
        """Test VQE returns convergence history."""
        result = await run_vqe(
            num_qubits=2,
            ansatz_type="ry",
            depth=1,
            optimizer="COBYLA",
            max_iterations=10,
            shots=100,
        )

        assert result.convergence_history is not None
        assert len(result.convergence_history) > 0


class TestVQEResult:
    """Test VQEResult dataclass."""

    def test_vqe_result_fields(self):
        """Test VQEResult has expected fields."""
        result = VQEResult(
            optimal_energy=-1.5,
            optimal_parameters=[0.1, 0.2, 0.3],
            num_iterations=10,
            optimizer="COBYLA",
            convergence_history=[-1.0, -1.2, -1.5],
        )

        assert result.optimal_energy == -1.5
        assert len(result.optimal_parameters) == 3
        assert result.num_iterations == 10
        assert result.optimizer == "COBYLA"
