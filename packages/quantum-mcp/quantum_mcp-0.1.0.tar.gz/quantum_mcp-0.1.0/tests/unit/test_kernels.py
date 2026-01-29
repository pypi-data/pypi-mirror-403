# Description: Test quantum kernel methods for machine learning.
# Description: Validates feature maps, kernel computation, and fidelity calculation.
"""Test quantum kernel methods for machine learning."""

import numpy as np
import pytest
from qiskit import QuantumCircuit

from quantum_mcp.circuits.kernels import (
    FeatureMapType,
    KernelResult,
    build_feature_map,
    compute_kernel_entry,
    compute_kernel_matrix,
)


class TestFeatureMaps:
    """Test quantum feature map builders."""

    def test_zz_feature_map_structure(self):
        """Test ZZ feature map has correct structure."""
        feature_map = build_feature_map(
            num_qubits=2,
            feature_dim=2,
            feature_map_type=FeatureMapType.ZZ,
        )

        assert isinstance(feature_map, QuantumCircuit)
        assert feature_map.num_qubits == 2
        assert feature_map.num_parameters > 0

    def test_z_feature_map(self):
        """Test Z feature map (no entanglement)."""
        feature_map = build_feature_map(
            num_qubits=3,
            feature_dim=3,
            feature_map_type=FeatureMapType.Z,
        )

        assert isinstance(feature_map, QuantumCircuit)
        assert feature_map.num_qubits == 3

    def test_feature_map_depth(self):
        """Test feature map with different depths."""
        fm_d1 = build_feature_map(
            num_qubits=2, feature_dim=2, reps=1
        )
        fm_d2 = build_feature_map(
            num_qubits=2, feature_dim=2, reps=2
        )

        # More reps means deeper circuit (more gates)
        assert fm_d2.depth() > fm_d1.depth()

    def test_feature_map_parameterized(self):
        """Test feature map is parameterized."""
        feature_map = build_feature_map(num_qubits=2, feature_dim=2)

        assert len(feature_map.parameters) > 0


class TestKernelComputation:
    """Test kernel value computation."""

    @pytest.mark.asyncio
    async def test_compute_kernel_entry_same_point(self):
        """Test kernel entry for same data point is ~1."""
        x = [0.1, 0.2]

        kernel_val = await compute_kernel_entry(x, x, num_qubits=2, shots=1000)

        # Same point should have high overlap
        assert kernel_val > 0.9

    @pytest.mark.asyncio
    async def test_compute_kernel_entry_different_points(self):
        """Test kernel entry for different data points."""
        x1 = [0.0, 0.0]
        x2 = [np.pi, np.pi]

        kernel_val = await compute_kernel_entry(x1, x2, num_qubits=2, shots=1000)

        # Different points should have lower overlap
        assert 0.0 <= kernel_val <= 1.0

    @pytest.mark.asyncio
    async def test_compute_kernel_entry_bounds(self):
        """Test kernel values are in valid range."""
        x1 = [0.5, 0.5]
        x2 = [1.0, 1.0]

        kernel_val = await compute_kernel_entry(x1, x2, num_qubits=2, shots=1000)

        assert 0.0 <= kernel_val <= 1.0


class TestKernelMatrix:
    """Test kernel matrix computation."""

    @pytest.mark.asyncio
    async def test_compute_kernel_matrix(self):
        """Test computing full kernel matrix."""
        data = [
            [0.1, 0.2],
            [0.3, 0.4],
            [0.5, 0.6],
        ]

        result = await compute_kernel_matrix(
            data=data,
            num_qubits=2,
            shots=100,
        )

        assert isinstance(result, KernelResult)
        assert result.kernel_matrix is not None
        assert result.kernel_matrix.shape == (3, 3)

    @pytest.mark.asyncio
    async def test_kernel_matrix_symmetric(self):
        """Test kernel matrix is symmetric."""
        data = [
            [0.1, 0.2],
            [0.3, 0.4],
        ]

        result = await compute_kernel_matrix(
            data=data,
            num_qubits=2,
            shots=500,
        )

        # Check symmetry (within tolerance due to shot noise)
        matrix = result.kernel_matrix
        assert np.allclose(matrix, matrix.T, atol=0.1)

    @pytest.mark.asyncio
    async def test_kernel_matrix_diagonal_ones(self):
        """Test kernel matrix has ~1 on diagonal."""
        data = [
            [0.1, 0.2],
            [0.3, 0.4],
        ]

        result = await compute_kernel_matrix(
            data=data,
            num_qubits=2,
            shots=500,
        )

        # Diagonal should be close to 1
        diagonal = np.diag(result.kernel_matrix)
        assert np.all(diagonal > 0.8)


class TestKernelResult:
    """Test KernelResult dataclass."""

    def test_kernel_result_fields(self):
        """Test KernelResult has expected fields."""
        matrix = np.array([[1.0, 0.5], [0.5, 1.0]])
        result = KernelResult(
            kernel_matrix=matrix,
            num_qubits=2,
            feature_map_type="ZZ",
            shots=1000,
        )

        assert np.array_equal(result.kernel_matrix, matrix)
        assert result.num_qubits == 2
        assert result.feature_map_type == "ZZ"
        assert result.shots == 1000
