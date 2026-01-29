# Description: Q# integration for quantum program execution.
# Description: Provides compilation, validation, and execution of Q# code.
"""Q# integration for quantum program execution."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Optional

import qsharp


def _init_qsharp() -> None:
    """Initialize Q# with unrestricted target profile."""
    qsharp.init(target_profile=qsharp.TargetProfile.Unrestricted)


@dataclass
class QSharpResult:
    """Result of Q# program execution."""

    success: bool
    results: list[str] = field(default_factory=list)
    shots: int = 0
    code: str = ""
    error: Optional[str] = None
    circuit_info: Optional[str] = None

    def histogram(self) -> dict[str, int]:
        """Compute histogram of results.

        Returns:
            Dictionary mapping result values to counts
        """
        return dict(Counter(self.results))


def validate_qsharp(code: str) -> tuple[bool, Optional[str]]:
    """Validate Q# code without executing it.

    Args:
        code: Q# code to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        _init_qsharp()
        # Use eval with no shots to validate syntax
        qsharp.eval(code)
        return True, None
    except qsharp.QSharpError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Validation error: {str(e)}"


def compile_qsharp(code: str) -> Optional[str]:
    """Compile Q# code and return circuit representation.

    Args:
        code: Q# code to compile

    Returns:
        Circuit information string, or None if compilation fails
    """
    try:
        _init_qsharp()

        # Try to get circuit representation
        try:
            circuit = qsharp.circuit(code)
            return str(circuit) if circuit else "Compiled successfully"
        except Exception:
            # Fall back to just validation
            qsharp.eval(code)
            return "Compiled successfully (no circuit representation)"
    except qsharp.QSharpError:
        return None
    except Exception:
        return None


async def run_qsharp(
    code: str,
    shots: int = 100,
) -> QSharpResult:
    """Execute Q# code and return results.

    Args:
        code: Q# code to execute
        shots: Number of times to run the program

    Returns:
        QSharpResult with execution results
    """
    try:
        _init_qsharp()

        # Execute the code
        results = qsharp.run(code, shots=shots)

        # Convert results to strings
        str_results = [str(r) for r in results]

        # Try to get circuit info
        circuit_info = None
        try:
            circuit = qsharp.circuit(code)
            if circuit:
                circuit_info = str(circuit)
        except Exception:
            pass

        return QSharpResult(
            success=True,
            results=str_results,
            shots=shots,
            code=code,
            circuit_info=circuit_info,
        )

    except qsharp.QSharpError as e:
        return QSharpResult(
            success=False,
            code=code,
            error=str(e),
        )
    except Exception as e:
        return QSharpResult(
            success=False,
            code=code,
            error=f"Execution error: {str(e)}",
        )
