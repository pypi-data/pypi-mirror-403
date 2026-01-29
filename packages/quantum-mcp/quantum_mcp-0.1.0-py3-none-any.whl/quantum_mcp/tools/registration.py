# Description: Tool registration for MCP server.
# Description: Wires up all quantum computing tools to the MCP server.
"""Tool registration for MCP server."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from quantum_mcp.server import QuantumMCPServer


def register_all_tools(server: "QuantumMCPServer") -> None:
    """Register all tools with the MCP server.

    Args:
        server: The MCP server instance to register tools with
    """
    register_quantum_tools(server)


def register_quantum_tools(server: "QuantumMCPServer") -> None:
    """Register quantum algorithm tools.

    Args:
        server: The MCP server instance
    """
    from quantum_mcp.tools.algorithm_tools import (
        quantum_anneal,
        quantum_kernel,
        quantum_qaoa,
        quantum_run_qsharp,
        quantum_vqe,
    )
    from quantum_mcp.tools.backend_tools import estimate_cost, list_backends
    from quantum_mcp.tools.simulation_tools import simulate_circuit

    # VQE Tool
    server.register_tool(
        name="quantum_vqe",
        description=(
            "Run Variational Quantum Eigensolver (VQE) to find ground state energy. "
            "VQE uses a parameterized quantum circuit optimized classically. "
            "Supports H2 molecule Hamiltonian for chemistry simulations."
        ),
        schema={
            "type": "object",
            "properties": {
                "num_qubits": {
                    "type": "integer",
                    "default": 2,
                    "description": "Number of qubits",
                },
                "ansatz_type": {
                    "type": "string",
                    "enum": ["ry", "hardware_efficient"],
                    "default": "ry",
                    "description": "Ansatz circuit type",
                },
                "depth": {
                    "type": "integer",
                    "default": 2,
                    "description": "Number of ansatz layers",
                },
                "hamiltonian_type": {
                    "type": "string",
                    "default": "h2",
                    "description": "Hamiltonian to minimize (h2 for H2 molecule)",
                },
                "optimizer": {
                    "type": "string",
                    "enum": ["COBYLA", "SPSA", "SLSQP"],
                    "default": "COBYLA",
                    "description": "Classical optimizer",
                },
                "max_iterations": {
                    "type": "integer",
                    "default": 100,
                    "description": "Maximum optimization iterations",
                },
                "shots": {
                    "type": "integer",
                    "default": 1000,
                    "description": "Measurement shots per evaluation",
                },
            },
        },
        handler=quantum_vqe,
    )

    # QAOA Tool
    server.register_tool(
        name="quantum_qaoa",
        description=(
            "Run Quantum Approximate Optimization Algorithm (QAOA) for MaxCut problems. "
            "QAOA finds approximate solutions to combinatorial optimization using "
            "alternating cost and mixer unitaries."
        ),
        schema={
            "type": "object",
            "properties": {
                "edges": {
                    "type": "array",
                    "items": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "minItems": 2,
                        "maxItems": 2,
                    },
                    "description": "Graph edges as list of [i, j] pairs",
                },
                "weights": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "Optional edge weights (default: all 1.0)",
                },
                "layers": {
                    "type": "integer",
                    "default": 1,
                    "description": "Number of QAOA layers (p parameter)",
                },
                "optimizer": {
                    "type": "string",
                    "enum": ["COBYLA", "SPSA", "SLSQP"],
                    "default": "COBYLA",
                    "description": "Classical optimizer",
                },
                "max_iterations": {
                    "type": "integer",
                    "default": 100,
                    "description": "Maximum optimization iterations",
                },
                "shots": {
                    "type": "integer",
                    "default": 1000,
                    "description": "Measurement shots per evaluation",
                },
            },
            "required": ["edges"],
        },
        handler=quantum_qaoa,
    )

    # Quantum Kernel Tool
    server.register_tool(
        name="quantum_kernel",
        description=(
            "Compute quantum kernel matrix for machine learning. "
            "Returns K[i,j] = |<phi(x_i)|phi(x_j)>|^2 using quantum feature maps. "
            "Use with classical SVM or other kernel-based ML algorithms."
        ),
        schema={
            "type": "object",
            "properties": {
                "data": {
                    "type": "array",
                    "items": {
                        "type": "array",
                        "items": {"type": "number"},
                    },
                    "description": "List of data points (each a list of floats)",
                },
                "num_qubits": {
                    "type": "integer",
                    "default": 2,
                    "description": "Number of qubits for encoding",
                },
                "feature_map": {
                    "type": "string",
                    "enum": ["Z", "ZZ", "ZZZ"],
                    "default": "ZZ",
                    "description": "Feature map type",
                },
                "shots": {
                    "type": "integer",
                    "default": 1000,
                    "description": "Measurement shots per kernel entry",
                },
                "reps": {
                    "type": "integer",
                    "default": 2,
                    "description": "Feature map repetitions",
                },
            },
            "required": ["data"],
        },
        handler=quantum_kernel,
    )

    # Q# Execution Tool
    server.register_tool(
        name="quantum_run_qsharp",
        description=(
            "Execute Q# quantum program in a local simulator. "
            "Runs Q# code and returns measurement results with statistics. "
            "Supports any valid Q# program that returns Result or tuple of Results."
        ),
        schema={
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Q# code to execute",
                },
                "shots": {
                    "type": "integer",
                    "default": 100,
                    "description": "Number of times to run the program",
                },
            },
            "required": ["code"],
        },
        handler=quantum_run_qsharp,
    )

    # List Backends Tool
    server.register_tool(
        name="quantum_list_backends",
        description=(
            "List available quantum backends from Azure Quantum. "
            "Returns information about simulators and hardware from IonQ, "
            "Quantinuum, Rigetti, and other providers."
        ),
        schema={
            "type": "object",
            "properties": {
                "simulators_only": {
                    "type": "boolean",
                    "default": False,
                    "description": "Only return simulator backends (no hardware)",
                },
                "provider": {
                    "type": "string",
                    "description": "Filter by provider name (e.g., ionq, quantinuum)",
                },
            },
        },
        handler=_list_backends_handler,
    )

    # Simulate Circuit Tool
    server.register_tool(
        name="quantum_simulate",
        description=(
            "Simulate a quantum circuit locally without using Azure Quantum. "
            "Fast simulation for testing and development. "
            "Supports circuits up to ~20 qubits depending on memory."
        ),
        schema={
            "type": "object",
            "properties": {
                "circuit_type": {
                    "type": "string",
                    "enum": ["bell", "ghz", "qft", "custom"],
                    "description": "Type of circuit to simulate",
                },
                "num_qubits": {
                    "type": "integer",
                    "default": 2,
                    "description": "Number of qubits",
                },
                "shots": {
                    "type": "integer",
                    "default": 1000,
                    "description": "Number of measurement shots",
                },
                "qasm": {
                    "type": "string",
                    "description": "OpenQASM code (for custom circuit type)",
                },
            },
            "required": ["circuit_type"],
        },
        handler=simulate_circuit,
    )

    # Estimate Cost Tool
    server.register_tool(
        name="quantum_estimate_cost",
        description=(
            "Estimate the cost of running a quantum job on Azure Quantum. "
            "Returns cost breakdown by provider before submitting."
        ),
        schema={
            "type": "object",
            "properties": {
                "backend": {
                    "type": "string",
                    "description": "Backend ID (e.g., ionq.simulator)",
                },
                "shots": {
                    "type": "integer",
                    "default": 1000,
                    "description": "Number of measurement shots",
                },
            },
            "required": ["backend"],
        },
        handler=_estimate_cost_handler,
    )

    # Quantum Annealing Tool
    server.register_tool(
        name="quantum_anneal",
        description=(
            "Solve QUBO optimization problems using quantum annealing. "
            "Uses D-Wave quantum annealers when available, with automatic fallback "
            "to classical exact solvers. Ideal for combinatorial optimization, "
            "scheduling, routing, and constraint satisfaction problems."
        ),
        schema={
            "type": "object",
            "properties": {
                "qubo": {
                    "type": "object",
                    "additionalProperties": {"type": "number"},
                    "description": (
                        "QUBO matrix as dict with 'i,j' string keys mapping to coefficients. "
                        "Example: {'0,0': -1, '1,1': -1, '0,1': 2} for -x0 - x1 + 2*x0*x1"
                    ),
                },
                "num_reads": {
                    "type": "integer",
                    "default": 100,
                    "description": "Number of samples to take",
                },
                "backend_type": {
                    "type": "string",
                    "enum": ["auto", "dwave", "exact"],
                    "default": "auto",
                    "description": (
                        "Backend: 'auto' tries D-Wave then exact, "
                        "'dwave' for D-Wave only, 'exact' for classical solver"
                    ),
                },
            },
            "required": ["qubo"],
        },
        handler=quantum_anneal,
    )


async def _list_backends_handler(
    simulators_only: bool = False,
    provider: str | None = None,
) -> str:
    """Handler for list_backends that injects the client from the server singleton."""
    from quantum_mcp.server import get_server
    from quantum_mcp.tools.backend_tools import list_backends

    server = get_server()
    if server.client is None:
        return '{"error": "Quantum client not configured"}'
    return await list_backends(
        client=server.client,
        simulators_only=simulators_only,
        provider=provider,
    )


async def _estimate_cost_handler(
    backend: str,
    shots: int = 1000,
) -> str:
    """Handler for estimate_cost that injects the client from the server singleton."""
    from quantum_mcp.server import get_server
    from quantum_mcp.tools.backend_tools import estimate_cost

    server = get_server()
    if server.client is None:
        return '{"error": "Quantum client not configured"}'
    return await estimate_cost(
        client=server.client,
        backend=backend,
        shots=shots,
    )
