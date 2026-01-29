# Integration with predictive-insights

This document describes the integration points between quantum_mcp and the predictive-insights project.

## Project Overview

### quantum_mcp

**Repository:** https://github.com/ryanmat/quantum_mcp

**Focus:**
- Azure Quantum integration (VQE, QAOA, Kernels, Q#)
- Multi-agent orchestration (routing, consensus, decomposition)
- Quantum-enhanced orchestration (QUBO/QAOA routing)

**MCP Tools:** 8 tools for quantum computing accessible via Claude Code

### predictive-insights

**Repository:** https://github.com/ryanmat/Predictive-Diagnostics

**Focus:**
- Temporal X-DEC (BiGRU-XVAE-DEC) for metric prediction
- Foundation model integration (Chronos-2, TimesFM 2.0)
- LLaMA3-8B + LoRA for log anomaly detection
- Physics-GAT for topology awareness
- MoE (Mixture of Experts) unification
- TD3/EPO agentic layer

---

## Integration Points

### Phase 14: MoE Unification

When predictive-insights reaches Phase 14 (MoE Unification), quantum_mcp can provide:

#### 1. QAOA-Optimized Expert Routing

**Problem:** MoE architectures require selecting sparse experts from a pool. This is a combinatorial optimization problem.

**quantum_mcp Solution:**
- Formulate expert selection as QUBO (Quadratic Unconstrained Binary Optimization)
- Solve using QAOA (Quantum Approximate Optimization Algorithm)
- Provides provably optimal or near-optimal expert selection

**Integration Pattern:**
```python
from quantum_mcp.quantum_routing import QAOARouter

# Create router with expert scores
router = QAOARouter(
    agents=expert_pool,
    qaoa_layers=2,
    use_quantum=True  # Falls back to classical if Azure unavailable
)

# Route task to optimal expert(s)
selected_experts = await router.route(task, count=3)
```

#### 2. Multi-Agent Consensus

**Problem:** When multiple prediction experts disagree, how to reach consensus?

**quantum_mcp Solution:**
- Quantum consensus formulation (Phase 3.3-3.4)
- QAOA-based consensus optimization
- Weighted voting with quantum-derived weights

**Integration Pattern:**
```python
from quantum_mcp.orchestration.consensus import WeightedMergeConsensus

# Gather predictions from multiple experts
predictions = [expert.predict(data) for expert in experts]

# Reach consensus
consensus = WeightedMergeConsensus()
final_prediction = await consensus.merge(predictions)
```

#### 3. Quantum Kernel Enhancement

**Problem:** DEC layer clustering quality affects prediction accuracy.

**quantum_mcp Solution:**
- Quantum kernels (ZZ, ZZZ feature maps)
- Enhanced similarity computation for clustering
- Quantum-enhanced distance metrics

**Integration Pattern:**
```python
from quantum_mcp.circuits.kernels import QuantumKernelComputer

# Compute kernel matrix for clustering
kernel_computer = QuantumKernelComputer(
    num_qubits=4,
    feature_map="ZZ",
    shots=1000
)

# Use kernel for enhanced clustering
kernel_matrix = await kernel_computer.compute_kernel(data_points)
```

---

## Technical Requirements

### For quantum_mcp to integrate with predictive-insights:

1. **MCP Server Running**
   ```bash
   cd quantum_mcp
   uv run python -m quantum_mcp
   ```

2. **Azure Quantum Configured** (for hardware execution)
   - Workspace: rm-quantum
   - Service Principal: 62a49f65-acf7-46da-a04a-d4679512ea53
   - Falls back to Qiskit Aer simulator if unavailable

3. **Optional: Direct Python Import**
   ```bash
   pip install -e /path/to/quantum_mcp
   ```

### For predictive-insights to consume quantum_mcp:

1. **Via MCP Protocol** (preferred)
   - Configure Claude Code with quantum_mcp MCP server
   - Use MCP tools for quantum operations

2. **Via Direct Python Import**
   - Add quantum_mcp as dependency
   - Import routers, consensus, kernels directly

---

## Roadmap Alignment

| predictive-insights Phase | quantum_mcp Integration |
|---------------------------|-------------------------|
| Phase 9: Temporal X-DEC | No direct integration |
| Phase 10: Foundation Models | No direct integration |
| Phase 11: LLaMA3 + LoRA | No direct integration |
| Phase 12: Physics-GAT | Potential quantum kernel |
| Phase 13: Ensemble Distillation | No direct integration |
| Phase 14: MoE Unification | QAOA expert routing |
| Phase 15: TD3/EPO Agentic | Multi-agent orchestration |
| Phase 16: Production Deploy | MCP server integration |

---

## Current Status

### quantum_mcp

| Phase | Status |
|-------|--------|
| Phase 0: Quantum Foundation | Complete |
| Phase 1: Multi-Agent Orchestration | Complete |
| Phase 3: Quantum Orchestration | In Progress (3.3 pending) |

### predictive-insights

See predictive-insights/docs/phases/ for detailed phase specifications.

---

## Migration History

X-DEC metric intelligence was originally prototyped in quantum_mcp (Phase 2) but migrated to predictive-insights due to superior implementation:

| Feature | quantum_mcp (removed) | predictive-insights |
|---------|----------------------|---------------------|
| Encoder | MLP-based | BiGRU with temporal attention |
| Sequence | Single timestep | 30-timestep native |
| Clusters | Generic | 5 semantic operational states |
| Training | Basic | Two-stage with lambda annealing |
| Deployment | None | FastAPI production-ready |

---

## Contact

Both projects maintained by Ryan Matuszewski.

- quantum_mcp: Quantum computing and multi-agent orchestration
- predictive-insights: Metric prediction and anomaly detection
