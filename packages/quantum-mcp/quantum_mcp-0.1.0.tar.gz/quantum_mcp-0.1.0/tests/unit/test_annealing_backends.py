# Description: Unit tests for annealing backend implementations.
# Description: Tests ExactSolverBackend and backend factory functions.
"""Unit tests for annealing backends."""

from __future__ import annotations

import pytest

from quantum_mcp.backends import (
    AnnealingResult,
    AnnealingSample,
    BackendParadigm,
    BackendStatus,
    ExactSolverBackend,
    create_annealing_backend,
    has_dwave_credentials,
)


class TestAnnealingSample:
    """Tests for AnnealingSample data class."""

    def test_sample_creation(self) -> None:
        """Test creating a sample."""
        sample = AnnealingSample(
            bitstring={0: 1, 1: 0, 2: 1},
            energy=-2.5,
            num_occurrences=10,
        )
        assert sample.bitstring == {0: 1, 1: 0, 2: 1}
        assert sample.energy == -2.5
        assert sample.num_occurrences == 10

    def test_get_selected_indices(self) -> None:
        """Test extracting selected variable indices."""
        sample = AnnealingSample(
            bitstring={0: 1, 1: 0, 2: 1, 3: 0, 4: 1},
            energy=0.0,
        )
        selected = sample.get_selected_indices()
        assert selected == [0, 2, 4]

    def test_to_binary_string(self) -> None:
        """Test converting to binary string representation."""
        sample = AnnealingSample(
            bitstring={0: 1, 1: 0, 2: 1},
            energy=0.0,
        )
        assert sample.to_binary_string() == "101"
        assert sample.to_binary_string(num_vars=5) == "10100"

    def test_to_binary_string_empty(self) -> None:
        """Test binary string for empty bitstring."""
        sample = AnnealingSample(bitstring={}, energy=0.0)
        assert sample.to_binary_string() == ""


class TestAnnealingResult:
    """Tests for AnnealingResult data class."""

    def test_result_creation(self) -> None:
        """Test creating a result."""
        samples = [
            AnnealingSample(bitstring={0: 1}, energy=-1.0, num_occurrences=5),
            AnnealingSample(bitstring={0: 0}, energy=0.0, num_occurrences=3),
        ]
        result = AnnealingResult(
            samples=samples,
            timing_info={"qpu_time_us": 1000},
            metadata={"solver": "test"},
        )
        assert len(result.samples) == 2
        assert result.timing_info["qpu_time_us"] == 1000
        assert result.metadata["solver"] == "test"

    def test_best_sample(self) -> None:
        """Test getting the best (lowest energy) sample."""
        samples = [
            AnnealingSample(bitstring={0: 0}, energy=0.0),
            AnnealingSample(bitstring={0: 1}, energy=-2.0),
            AnnealingSample(bitstring={1: 1}, energy=-1.0),
        ]
        result = AnnealingResult(samples=samples)
        assert result.best_sample.energy == -2.0
        assert result.best_sample.bitstring == {0: 1}

    def test_best_energy(self) -> None:
        """Test getting the best energy."""
        samples = [
            AnnealingSample(bitstring={0: 0}, energy=1.5),
            AnnealingSample(bitstring={0: 1}, energy=-0.5),
        ]
        result = AnnealingResult(samples=samples)
        assert result.best_energy == -0.5

    def test_num_samples(self) -> None:
        """Test counting unique samples."""
        samples = [
            AnnealingSample(bitstring={0: 0}, energy=0.0),
            AnnealingSample(bitstring={0: 1}, energy=-1.0),
        ]
        result = AnnealingResult(samples=samples)
        assert result.num_samples == 2

    def test_total_occurrences(self) -> None:
        """Test counting total occurrences."""
        samples = [
            AnnealingSample(bitstring={0: 0}, energy=0.0, num_occurrences=5),
            AnnealingSample(bitstring={0: 1}, energy=-1.0, num_occurrences=3),
        ]
        result = AnnealingResult(samples=samples)
        assert result.total_occurrences == 8

    def test_get_samples_below_energy(self) -> None:
        """Test filtering samples by energy threshold."""
        samples = [
            AnnealingSample(bitstring={0: 0}, energy=1.0),
            AnnealingSample(bitstring={0: 1}, energy=-1.0),
            AnnealingSample(bitstring={1: 1}, energy=0.5),
        ]
        result = AnnealingResult(samples=samples)
        below = result.get_samples_below_energy(0.0)
        assert len(below) == 1
        assert below[0].energy == -1.0

    def test_empty_result_raises(self) -> None:
        """Test that best_sample raises for empty result."""
        result = AnnealingResult(samples=[])
        with pytest.raises(ValueError, match="No samples"):
            _ = result.best_sample


class TestExactSolverBackend:
    """Tests for ExactSolverBackend."""

    @pytest.fixture
    def backend(self) -> ExactSolverBackend:
        """Create backend instance."""
        return ExactSolverBackend(max_variables=20)

    def test_backend_properties(self, backend: ExactSolverBackend) -> None:
        """Test backend properties."""
        assert backend.backend_id == "classical.exact_solver"
        assert backend.capabilities.paradigm == BackendParadigm.ANNEALING
        assert backend.capabilities.is_simulator is True
        assert backend.capabilities.provider == "classical"

    @pytest.mark.asyncio
    async def test_connect(self, backend: ExactSolverBackend) -> None:
        """Test connecting to backend."""
        assert not backend.is_connected
        await backend.connect()
        assert backend.is_connected

    @pytest.mark.asyncio
    async def test_health_check(self, backend: ExactSolverBackend) -> None:
        """Test health check."""
        await backend.connect()
        status = await backend.health_check()
        assert status == BackendStatus.AVAILABLE

    @pytest.mark.asyncio
    async def test_solve_empty_qubo(self, backend: ExactSolverBackend) -> None:
        """Test solving empty QUBO."""
        await backend.connect()
        result = await backend.solve_qubo({})
        assert len(result.samples) == 1
        assert result.best_energy == 0.0

    @pytest.mark.asyncio
    async def test_solve_simple_qubo(self, backend: ExactSolverBackend) -> None:
        """Test solving a simple QUBO with known solution."""
        await backend.connect()

        # QUBO: minimize x0 + x1 - 2*x0*x1
        # Optimal: x0=1, x1=1 -> 1 + 1 - 2 = 0
        # vs x0=0, x1=0 -> 0
        # vs x0=1, x1=0 -> 1
        # vs x0=0, x1=1 -> 1
        Q = {
            (0, 0): 1.0,  # x0
            (1, 1): 1.0,  # x1
            (0, 1): -2.0,  # -2*x0*x1
        }

        result = await backend.solve_qubo(Q)
        best = result.best_sample

        # Both (0,0) and (1,1) have energy 0, so either is valid
        assert best.energy == 0.0

    @pytest.mark.asyncio
    async def test_solve_qubo_finds_minimum(self, backend: ExactSolverBackend) -> None:
        """Test that solver finds the global minimum."""
        await backend.connect()

        # QUBO: -3*x0 - 2*x1 + 4*x0*x1
        # x0=0, x1=0: 0
        # x0=1, x1=0: -3
        # x0=0, x1=1: -2
        # x0=1, x1=1: -3 - 2 + 4 = -1
        # Optimal: x0=1, x1=0 with energy -3
        Q = {
            (0, 0): -3.0,
            (1, 1): -2.0,
            (0, 1): 4.0,
        }

        result = await backend.solve_qubo(Q)
        assert result.best_energy == -3.0
        assert result.best_sample.bitstring == {0: 1, 1: 0}

    @pytest.mark.asyncio
    async def test_solve_bqm(self, backend: ExactSolverBackend) -> None:
        """Test solving a BQM problem."""
        await backend.connect()

        # BQM equivalent to above QUBO
        linear = {0: -3.0, 1: -2.0}
        quadratic = {(0, 1): 4.0}

        result = await backend.solve_bqm(linear, quadratic)
        assert result.best_energy == -3.0

    @pytest.mark.asyncio
    async def test_solve_bqm_with_offset(self, backend: ExactSolverBackend) -> None:
        """Test that BQM offset is applied to energies."""
        await backend.connect()

        linear = {0: -1.0}
        quadratic = {}
        offset = 5.0

        result = await backend.solve_bqm(linear, quadratic, offset=offset)
        # Optimal: x0=1, energy = -1 + 5 = 4
        assert result.best_energy == 4.0

    @pytest.mark.asyncio
    async def test_context_manager(self) -> None:
        """Test async context manager."""
        async with ExactSolverBackend() as backend:
            assert backend.is_connected
            result = await backend.solve_qubo({(0, 0): -1.0})
            assert result.best_sample.bitstring[0] == 1
        assert not backend.is_connected


class TestBackendFactory:
    """Tests for backend factory functions."""

    def test_create_exact_backend(self) -> None:
        """Test creating exact solver backend."""
        backend = create_annealing_backend("exact")
        assert isinstance(backend, ExactSolverBackend)
        assert backend.backend_id == "classical.exact_solver"

    def test_create_auto_backend_without_credentials(self) -> None:
        """Test auto backend falls back to exact without D-Wave credentials."""
        # This should work even without D-Wave SDK installed
        backend = create_annealing_backend("auto")
        # Without DWAVE_API_TOKEN, should get ExactSolver
        assert isinstance(backend, ExactSolverBackend)

    def test_create_unknown_backend_raises(self) -> None:
        """Test that unknown backend type raises ValueError."""
        with pytest.raises(ValueError, match="Unknown annealing backend"):
            create_annealing_backend("invalid_backend")

    def test_has_dwave_credentials(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test D-Wave credentials check."""
        monkeypatch.delenv("DWAVE_API_TOKEN", raising=False)
        assert has_dwave_credentials() is False

        monkeypatch.setenv("DWAVE_API_TOKEN", "test-token")
        assert has_dwave_credentials() is True


class TestExactSolverGreedy:
    """Tests for greedy fallback in ExactSolver."""

    @pytest.mark.asyncio
    async def test_greedy_for_large_problems(self) -> None:
        """Test that greedy solver is used for large problems."""
        backend = ExactSolverBackend(max_variables=5)  # Low threshold
        await backend.connect()

        # Create a 10-variable problem (exceeds max_variables)
        Q = {(i, i): -1.0 for i in range(10)}

        result = await backend.solve_qubo(Q)
        # Greedy should find a reasonable solution
        # Exact minimum would be -10 (all selected)
        assert result.best_energy <= 0.0
        assert result.metadata.get("method") == "greedy"

    @pytest.mark.asyncio
    async def test_brute_force_for_small_problems(self) -> None:
        """Test that brute force is used for small problems."""
        backend = ExactSolverBackend(max_variables=20)
        await backend.connect()

        # Create a 5-variable problem
        Q = {(i, i): -1.0 for i in range(5)}

        result = await backend.solve_qubo(Q)
        # Brute force finds exact minimum
        assert result.best_energy == -5.0
        assert result.metadata.get("method") == "brute_force"
