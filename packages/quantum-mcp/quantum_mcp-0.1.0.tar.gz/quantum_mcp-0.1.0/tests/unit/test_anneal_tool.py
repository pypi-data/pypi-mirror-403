# Description: Tests for the quantum_anneal MCP tool.
# Description: Validates QUBO solving via the MCP interface.
"""Tests for quantum_anneal MCP tool."""

from __future__ import annotations

import json

import pytest

from quantum_mcp.tools.algorithm_tools import quantum_anneal


class TestQuantumAnnealTool:
    """Tests for the quantum_anneal tool function."""

    @pytest.mark.asyncio
    async def test_simple_qubo(self) -> None:
        """Test solving a simple 2-variable QUBO."""
        # QUBO: -x0 - x1 + 2*x0*x1
        # Minimum at x0=1, x1=0 or x0=0, x1=1 (energy = -1)
        qubo = {"0,0": -1, "1,1": -1, "0,1": 2}

        result = await quantum_anneal(qubo=qubo, num_reads=50)
        data = json.loads(result)

        assert "error" not in data
        assert data["algorithm"] == "Quantum Annealing"
        assert data["best_energy"] == -1.0
        assert data["num_variables"] == 2

    @pytest.mark.asyncio
    async def test_single_variable(self) -> None:
        """Test solving a single-variable QUBO."""
        # QUBO: -x0 (minimum at x0=1, energy=-1)
        qubo = {"0,0": -1}

        result = await quantum_anneal(qubo=qubo, num_reads=10)
        data = json.loads(result)

        assert "error" not in data
        assert data["best_energy"] == -1.0
        assert data["best_solution"]["0"] == 1

    @pytest.mark.asyncio
    async def test_three_variable_qubo(self) -> None:
        """Test solving a 3-variable QUBO."""
        # QUBO favoring x0=1, x1=1, x2=0
        qubo = {
            "0,0": -2,
            "1,1": -2,
            "2,2": 1,
            "0,1": 0.5,
            "0,2": 3,
            "1,2": 3,
        }

        result = await quantum_anneal(qubo=qubo, num_reads=100)
        data = json.loads(result)

        assert "error" not in data
        assert data["num_variables"] == 3
        assert "best_solution" in data
        assert "best_energy" in data

    @pytest.mark.asyncio
    async def test_exact_backend(self) -> None:
        """Test using the exact classical backend explicitly."""
        qubo = {"0,0": -1, "1,1": -1, "0,1": 2}

        result = await quantum_anneal(qubo=qubo, num_reads=10, backend_type="exact")
        data = json.loads(result)

        assert "error" not in data
        assert data["backend"] == "classical.exact_solver"

    @pytest.mark.asyncio
    async def test_response_structure(self) -> None:
        """Test that response contains expected fields."""
        qubo = {"0,0": -1, "1,1": -1}

        result = await quantum_anneal(qubo=qubo, num_reads=20)
        data = json.loads(result)

        assert "error" not in data
        assert "algorithm" in data
        assert "backend" in data
        assert "best_solution" in data
        assert "best_energy" in data
        assert "num_variables" in data
        assert "num_reads" in data
        assert "interpretation" in data
        assert "energy_distribution" in data

    @pytest.mark.asyncio
    async def test_invalid_qubo_key_format(self) -> None:
        """Test error handling for invalid QUBO key format."""
        qubo = {"invalid_key": -1}

        result = await quantum_anneal(qubo=qubo, num_reads=10)
        data = json.loads(result)

        assert "error" in data
        assert "Invalid QUBO key format" in data["error"]

    @pytest.mark.asyncio
    async def test_invalid_qubo_key_non_integer(self) -> None:
        """Test error handling for non-integer QUBO keys."""
        qubo = {"a,b": -1}

        result = await quantum_anneal(qubo=qubo, num_reads=10)
        data = json.loads(result)

        assert "error" in data
        assert "Invalid QUBO key" in data["error"]

    @pytest.mark.asyncio
    async def test_empty_qubo(self) -> None:
        """Test error handling for empty QUBO."""
        qubo: dict[str, float] = {}

        result = await quantum_anneal(qubo=qubo, num_reads=10)
        data = json.loads(result)

        assert "error" in data
        assert "Empty QUBO" in data["error"]

    @pytest.mark.asyncio
    async def test_symmetric_qubo(self) -> None:
        """Test that symmetric QUBO entries work correctly."""
        # Both (0,1) and (1,0) specified - should still work
        qubo = {"0,0": -1, "1,1": -1, "0,1": 1, "1,0": 1}

        result = await quantum_anneal(qubo=qubo, num_reads=50)
        data = json.loads(result)

        assert "error" not in data
        assert data["num_variables"] == 2

    @pytest.mark.asyncio
    async def test_interpretation_format(self) -> None:
        """Test that interpretation is human-readable."""
        qubo = {"0,0": -1, "1,1": -1}

        result = await quantum_anneal(qubo=qubo, num_reads=20)
        data = json.loads(result)

        assert "error" not in data
        interpretation = data["interpretation"]
        assert "optimal solution" in interpretation.lower()
        assert "energy" in interpretation.lower()
