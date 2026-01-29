# Description: Test Q# integration module.
# Description: Validates Q# compilation, execution, and result parsing.
"""Test Q# integration module."""

import pytest

from quantum_mcp.circuits.qsharp import (
    QSharpResult,
    compile_qsharp,
    run_qsharp,
    validate_qsharp,
)


class TestQSharpValidation:
    """Test Q# code validation."""

    def test_validate_simple_code(self):
        """Test validating simple Q# code."""
        code = "{ let x = 1 + 1; x }"
        is_valid, error = validate_qsharp(code)
        assert is_valid is True
        assert error is None

    def test_validate_quantum_code(self):
        """Test validating quantum Q# code."""
        code = """
        {
            use q = Qubit();
            H(q);
            let result = M(q);
            Reset(q);
            result
        }
        """
        is_valid, error = validate_qsharp(code)
        assert is_valid is True

    def test_validate_invalid_code(self):
        """Test validating invalid Q# code."""
        code = "{ InvalidOperation(x); }"
        is_valid, error = validate_qsharp(code)
        assert is_valid is False
        assert error is not None


class TestQSharpCompilation:
    """Test Q# compilation."""

    def test_compile_simple_code(self):
        """Test compiling simple Q# code."""
        code = "{ let x = 1 + 1; x }"
        circuit = compile_qsharp(code)
        assert circuit is not None

    def test_compile_quantum_code(self):
        """Test compiling quantum Q# code returns circuit info."""
        code = """
        {
            use q = Qubit();
            H(q);
            let result = M(q);
            Reset(q);
            result
        }
        """
        circuit = compile_qsharp(code)
        assert circuit is not None


class TestQSharpExecution:
    """Test Q# execution."""

    @pytest.mark.asyncio
    async def test_run_classical_code(self):
        """Test running classical Q# code."""
        code = "{ 1 + 1 }"
        result = await run_qsharp(code, shots=1)

        assert isinstance(result, QSharpResult)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_run_quantum_hadamard(self):
        """Test running Hadamard gate."""
        code = """
        {
            use q = Qubit();
            H(q);
            let result = M(q);
            Reset(q);
            result
        }
        """
        result = await run_qsharp(code, shots=100)

        assert isinstance(result, QSharpResult)
        assert result.success is True
        assert result.shots == 100
        # Should have some Zero and some One results
        assert result.results is not None
        assert len(result.results) == 100

    @pytest.mark.asyncio
    async def test_run_bell_state(self):
        """Test running Bell state circuit."""
        code = """
        {
            use (q1, q2) = (Qubit(), Qubit());
            H(q1);
            CNOT(q1, q2);
            let r1 = M(q1);
            let r2 = M(q2);
            ResetAll([q1, q2]);
            (r1, r2)
        }
        """
        result = await run_qsharp(code, shots=100)

        assert result.success is True
        assert len(result.results) == 100

    @pytest.mark.asyncio
    async def test_run_invalid_code(self):
        """Test running invalid Q# code returns error."""
        code = "{ InvalidOperation(x); }"
        result = await run_qsharp(code, shots=1)

        assert result.success is False
        assert result.error is not None


class TestQSharpResult:
    """Test QSharpResult dataclass."""

    def test_result_fields(self):
        """Test QSharpResult has expected fields."""
        result = QSharpResult(
            success=True,
            results=["Zero", "One", "Zero"],
            shots=3,
            code="test code",
        )

        assert result.success is True
        assert len(result.results) == 3
        assert result.shots == 3
        assert result.code == "test code"

    def test_result_with_histogram(self):
        """Test QSharpResult histogram calculation."""
        result = QSharpResult(
            success=True,
            results=["Zero", "One", "Zero", "Zero", "One"],
            shots=5,
            code="test",
        )

        histogram = result.histogram()
        assert histogram["Zero"] == 3
        assert histogram["One"] == 2
