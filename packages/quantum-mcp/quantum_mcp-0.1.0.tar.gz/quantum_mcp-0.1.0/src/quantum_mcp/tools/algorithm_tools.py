# Description: MCP tools for quantum algorithms (VQE, QAOA, QML).
# Description: Exposes high-level quantum algorithm interfaces.
"""Quantum algorithm MCP tools."""

from __future__ import annotations

import json
from typing import Optional

from quantum_mcp.backends import create_annealing_backend
from quantum_mcp.circuits.kernels import FeatureMapType, compute_kernel_matrix
from quantum_mcp.circuits.qaoa import run_qaoa
from quantum_mcp.circuits.qsharp import run_qsharp, validate_qsharp
from quantum_mcp.circuits.vqe import run_vqe


async def quantum_vqe(
    num_qubits: int = 2,
    ansatz_type: str = "ry",
    depth: int = 2,
    hamiltonian_type: str = "h2",
    optimizer: str = "COBYLA",
    max_iterations: int = 100,
    shots: int = 1000,
    bond_distance: Optional[float] = None,
) -> str:
    """Run Variational Quantum Eigensolver (VQE) algorithm.

    VQE finds the ground state energy of a Hamiltonian using a
    parameterized quantum circuit (ansatz) optimized classically.

    Args:
        num_qubits: Number of qubits (default: 2)
        ansatz_type: Ansatz circuit type ("ry", "hardware_efficient")
        depth: Number of ansatz layers (default: 2)
        hamiltonian_type: Hamiltonian to minimize ("h2" for H2 molecule)
        optimizer: Classical optimizer ("COBYLA", "SPSA", "SLSQP")
        max_iterations: Maximum optimization iterations
        shots: Number of measurement shots per evaluation
        bond_distance: H-H bond distance in Angstroms (for h2 Hamiltonian)

    Returns:
        JSON formatted VQE result with optimal energy and parameters
    """
    try:
        result = await run_vqe(
            num_qubits=num_qubits,
            ansatz_type=ansatz_type,
            depth=depth,
            hamiltonian_type=hamiltonian_type,
            optimizer=optimizer,
            max_iterations=max_iterations,
            shots=shots,
        )

        response: dict[str, object] = {
            "algorithm": "VQE",
            "optimal_energy": result.optimal_energy,
            "optimal_parameters": result.optimal_parameters,
            "num_iterations": result.num_iterations,
            "optimizer": result.optimizer,
            "ansatz_type": ansatz_type,
            "depth": depth,
            "num_qubits": num_qubits,
            "shots": shots,
        }

        if hamiltonian_type == "h2":
            # Add context for H2 molecule
            response["molecule"] = "H2"
            response["interpretation"] = (
                f"Ground state energy estimate: {result.optimal_energy:.4f} Hartree. "
                "Exact H2 ground state at equilibrium is approximately -1.137 Hartree."
            )

        # Include convergence info
        if result.convergence_history:
            response["initial_energy"] = result.convergence_history[0]
            response["energy_improvement"] = (
                result.convergence_history[0] - result.optimal_energy
            )

        return json.dumps(response, indent=2)

    except ValueError as e:
        return json.dumps({
            "error": f"Invalid configuration: {str(e)}",
        })
    except Exception as e:
        return json.dumps({
            "error": f"VQE failed: {str(e)}",
        })


async def quantum_qaoa(
    edges: list[tuple[int, int]],
    weights: Optional[list[float]] = None,
    layers: int = 1,
    optimizer: str = "COBYLA",
    max_iterations: int = 100,
    shots: int = 1000,
) -> str:
    """Run Quantum Approximate Optimization Algorithm (QAOA) for MaxCut.

    QAOA finds approximate solutions to combinatorial optimization problems
    using a parameterized quantum circuit alternating between cost and mixer
    unitaries.

    Args:
        edges: Graph edges as list of (i, j) tuples
        weights: Optional edge weights (default: all 1.0)
        layers: Number of QAOA layers (p parameter, default: 1)
        optimizer: Classical optimizer ("COBYLA", "SPSA", "SLSQP")
        max_iterations: Maximum optimization iterations
        shots: Number of measurement shots per evaluation

    Returns:
        JSON formatted QAOA result with optimal bitstring and cost
    """
    try:
        result = await run_qaoa(
            edges=edges,
            weights=weights,
            layers=layers,
            optimizer=optimizer,
            max_iterations=max_iterations,
            shots=shots,
        )

        # Calculate actual cut value (negate the cost)
        cut_value = -result.optimal_cost

        response: dict[str, object] = {
            "algorithm": "QAOA",
            "problem": "MaxCut",
            "optimal_bitstring": result.optimal_bitstring,
            "optimal_cost": result.optimal_cost,
            "cut_value": cut_value,
            "num_iterations": result.num_iterations,
            "optimizer": result.optimizer,
            "layers": layers,
            "num_vertices": max(max(i, j) for i, j in edges) + 1,
            "num_edges": len(edges),
            "shots": shots,
        }

        # Add interpretation
        response["interpretation"] = (
            f"Found partition {result.optimal_bitstring} with cut value {cut_value:.2f}. "
            f"This partitions vertices into two groups based on bit values (0 or 1)."
        )

        # Include convergence info
        if result.convergence_history:
            response["initial_cost"] = result.convergence_history[0]
            response["cost_improvement"] = (
                result.convergence_history[0] - result.optimal_cost
            )

        return json.dumps(response, indent=2)

    except ValueError as e:
        return json.dumps({
            "error": f"Invalid configuration: {str(e)}",
        })
    except Exception as e:
        return json.dumps({
            "error": f"QAOA failed: {str(e)}",
        })


async def quantum_kernel(
    data: list[list[float]],
    num_qubits: int = 2,
    feature_map: str = "ZZ",
    shots: int = 1000,
    reps: int = 2,
) -> str:
    """Compute quantum kernel matrix for machine learning.

    Computes the kernel matrix K where K[i,j] = |<phi(x_i)|phi(x_j)>|^2
    using quantum feature maps. The kernel matrix can be used with
    classical ML algorithms like SVM.

    Args:
        data: List of data points (each a list of floats)
        num_qubits: Number of qubits for encoding
        feature_map: Feature map type ("Z", "ZZ", "ZZZ")
        shots: Number of measurement shots per kernel entry
        reps: Number of feature map repetitions

    Returns:
        JSON formatted result with kernel matrix and metadata
    """
    try:
        # Parse feature map type
        try:
            fm_type = FeatureMapType(feature_map)
        except ValueError:
            fm_type = FeatureMapType.ZZ

        result = await compute_kernel_matrix(
            data=data,
            num_qubits=num_qubits,
            feature_map_type=fm_type,
            shots=shots,
            reps=reps,
        )

        response: dict[str, object] = {
            "algorithm": "Quantum Kernel",
            "kernel_matrix": result.kernel_matrix.tolist(),
            "num_qubits": result.num_qubits,
            "feature_map_type": result.feature_map_type,
            "data_points": result.data_points,
            "shots": result.shots,
        }

        # Add interpretation
        response["interpretation"] = (
            f"Computed {result.data_points}x{result.data_points} quantum kernel matrix. "
            "Diagonal entries are 1.0 (self-similarity). "
            "Off-diagonal entries measure quantum state overlap between data points."
        )

        # Add usage hint
        response["usage"] = (
            "This kernel matrix can be used with classical SVM or other "
            "kernel-based ML algorithms: sklearn.svm.SVC(kernel='precomputed')"
        )

        return json.dumps(response, indent=2)

    except ValueError as e:
        return json.dumps({
            "error": f"Invalid configuration: {str(e)}",
        })
    except Exception as e:
        return json.dumps({
            "error": f"Kernel computation failed: {str(e)}",
        })


async def quantum_run_qsharp(
    code: str,
    shots: int = 100,
) -> str:
    """Execute Q# quantum program and return results.

    Runs Q# code in a local quantum simulator and returns
    measurement results with statistics.

    Args:
        code: Q# code to execute (should return a Result or tuple of Results)
        shots: Number of times to run the program (default: 100)

    Returns:
        JSON formatted result with execution results and statistics
    """
    try:
        # Validate code first
        is_valid, error = validate_qsharp(code)
        if not is_valid:
            return json.dumps({
                "success": False,
                "error": f"Invalid Q# code: {error}",
            })

        # Execute the code
        result = await run_qsharp(code, shots=shots)

        if not result.success:
            return json.dumps({
                "success": False,
                "error": result.error,
            })

        # Build response
        histogram = result.histogram()
        total = sum(histogram.values())

        response: dict[str, object] = {
            "success": True,
            "shots": result.shots,
            "results": result.results,
            "histogram": histogram,
            "probabilities": {
                k: v / total for k, v in histogram.items()
            } if total > 0 else {},
        }

        # Add circuit info if available
        if result.circuit_info:
            response["circuit_info"] = result.circuit_info

        # Add interpretation
        response["interpretation"] = (
            f"Executed Q# program {result.shots} times. "
            f"Found {len(histogram)} unique outcomes."
        )

        return json.dumps(response, indent=2)

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Q# execution failed: {str(e)}",
        })


async def quantum_anneal(
    qubo: dict[str, float],
    num_reads: int = 100,
    backend_type: str = "auto",
) -> str:
    """Solve a QUBO optimization problem using quantum annealing.

    QUBO (Quadratic Unconstrained Binary Optimization) is a mathematical
    formulation for optimization problems. This tool uses D-Wave quantum
    annealers when available, with automatic fallback to classical solvers.

    Args:
        qubo: QUBO matrix as dict with string keys "i,j" mapping to coefficients.
              For example: {"0,0": -1, "1,1": -1, "0,1": 2} represents
              -x0 - x1 + 2*x0*x1
        num_reads: Number of samples to take (default: 100)
        backend_type: Backend to use ("auto", "dwave", "exact")
                     "auto" tries D-Wave first, falls back to classical

    Returns:
        JSON formatted result with best solution, energy, and sample statistics
    """
    try:
        # Convert string keys to tuple keys for internal use
        qubo_dict: dict[tuple[int, int], float] = {}
        for key, value in qubo.items():
            parts = key.split(",")
            if len(parts) != 2:
                return json.dumps({
                    "error": f"Invalid QUBO key format: {key}. Expected 'i,j' format.",
                })
            try:
                i, j = int(parts[0].strip()), int(parts[1].strip())
                qubo_dict[(i, j)] = float(value)
            except ValueError:
                return json.dumps({
                    "error": f"Invalid QUBO key: {key}. Keys must be integers.",
                })

        if not qubo_dict:
            return json.dumps({
                "error": "Empty QUBO provided. Please provide at least one term.",
            })

        # Determine number of variables
        all_indices = set()
        for i, j in qubo_dict.keys():
            all_indices.add(i)
            all_indices.add(j)
        num_variables = max(all_indices) + 1

        # Create backend and solve
        backend = create_annealing_backend(backend_type=backend_type)

        async with backend:
            result = await backend.solve_qubo(qubo_dict, num_reads=num_reads)

        # Format best solution as readable dict
        best = result.best_sample
        solution_dict = {str(k): v for k, v in sorted(best.bitstring.items())}

        # Calculate sample statistics
        unique_energies = sorted(set(s.energy for s in result.samples))
        energy_counts = {}
        for s in result.samples:
            e = s.energy
            energy_counts[e] = energy_counts.get(e, 0) + s.num_occurrences

        response: dict[str, object] = {
            "algorithm": "Quantum Annealing",
            "backend": backend.backend_id,
            "best_solution": solution_dict,
            "best_energy": best.energy,
            "num_variables": num_variables,
            "num_reads": num_reads,
            "num_samples": len(result.samples),
            "unique_energies": len(unique_energies),
        }

        # Add timing info if available
        if result.timing_info:
            response["timing"] = result.timing_info

        # Add sample distribution (top 5 energies)
        top_energies = unique_energies[:5]
        response["energy_distribution"] = {
            str(e): energy_counts[e] for e in top_energies
        }

        # Add interpretation
        solution_str = "".join(str(best.bitstring.get(i, 0)) for i in range(num_variables))
        response["interpretation"] = (
            f"Found optimal solution {solution_str} with energy {best.energy:.4f}. "
            f"Sampled {len(result.samples)} configurations, found {len(unique_energies)} unique energies."
        )

        return json.dumps(response, indent=2)

    except ImportError as e:
        return json.dumps({
            "error": f"Backend not available: {str(e)}. Install with: uv sync --extra dwave",
        })
    except Exception as e:
        return json.dumps({
            "error": f"Annealing failed: {str(e)}",
        })
