# Quantum Backend Tracking

This document tracks quantum computing backends relevant to quantum_mcp integration.

## Current Backends

### Azure Quantum (Gate-Based)

**Status:** Integrated (Phase 0)

Azure Quantum provides access to gate-based quantum computers through various providers:

| Provider | Hardware | Qubits | Use Case |
|----------|----------|--------|----------|
| IonQ | Trapped Ion | 11-32 | High fidelity, low depth |
| Quantinuum | Trapped Ion | 20-56 | All-to-all connectivity |
| Rigetti | Superconducting | 40-80 | Fast gate times |
| PASQAL | Neutral Atom | ~100 | Analog simulation |

**Integration Points:**
- VQE for molecular ground state estimation
- QAOA for combinatorial optimization
- Quantum kernels for ML
- Q# program execution

### D-Wave (Quantum Annealing)

**Status:** Integrated (Phase 3.9)

D-Wave provides quantum annealing hardware optimized for optimization problems:

| System | Qubits | Connectivity | Best For |
|--------|--------|--------------|----------|
| Advantage | 5000+ | Pegasus (15-way) | QUBO optimization |
| Advantage2 | 7000+ | Zephyr (20-way) | Larger problems |

**Integration Points:**
- DWaveRouter for agent selection optimization
- Direct QUBO solving (faster than QAOA for pure optimization)
- Hybrid classical/quantum workflows

**Configuration:**
```bash
DWAVE_API_TOKEN=DEV-xxx...
DWAVE_SOLVER=Advantage_system6.4
```

---

## Future Backend: Microsoft Topological Qubits

### Majorana 1 Announcement (February 2025)

Microsoft announced "Majorana 1" - the first commercially available topological qubit chip:

**Key Claims:**
- Topological qubits based on Majorana zero modes
- Inherent error protection via topological properties
- Potential for much higher qubit counts due to reduced error correction overhead

**Significance:**
Topological qubits could dramatically reduce the physical-to-logical qubit ratio needed for error correction. Current superconducting systems require ~1000 physical qubits per logical qubit. Topological systems may achieve much better ratios.

### "Magne" Deployment Timeline

Microsoft plans to deploy their first fault-tolerant quantum system ("Magne") through Azure Quantum:

| Milestone | Timeline | Description |
|-----------|----------|-------------|
| Majorana 1 Chip | Feb 2025 | First topological qubit demonstration |
| Azure Preview | Late 2025 | Limited preview access |
| General Availability | Late 2026 | Full Azure Quantum integration |

### Evaluation Checklist

When Microsoft topological qubits become available, evaluate for integration:

**Technical Readiness:**
- [ ] SDK available (Qiskit, Q#, or native)
- [ ] Azure Quantum integration complete
- [ ] Documented gate set and connectivity
- [ ] Benchmarks published (gate fidelity, coherence time)

**quantum_mcp Integration:**
- [ ] Backend abstraction supports paradigm
- [ ] Can express routing QUBO/Ising problems
- [ ] Performance improvement over alternatives
- [ ] Cost-effective for our use cases

**Specific Questions to Answer:**
1. Does topological hardware support QAOA-style algorithms?
2. What is the native gate set?
3. How does error correction compare to superconducting?
4. What problem sizes are practical?

### Monitoring Sources

Track these sources for updates:

- [Azure Quantum Blog](https://azure.microsoft.com/en-us/blog/topics/quantum/)
- [Microsoft Research Quantum](https://www.microsoft.com/en-us/research/research-area/quantum-computing/)
- [arXiv quant-ph](https://arxiv.org/list/quant-ph/recent) - Search "Microsoft topological"
- [Nature Physics](https://www.nature.com/nphys/) - Majorana publications

---

## Backend Comparison Matrix

| Criterion | Azure (Gate) | D-Wave (Annealing) | MS Topological |
|-----------|--------------|-------------------|----------------|
| Paradigm | Gate-based | Annealing | Gate-based |
| Best For | Algorithms | Optimization | TBD |
| Qubits (2026) | ~100 | 5000+ | TBD |
| Error Rate | ~0.1% | N/A | TBD |
| Status | Integrated | Integrated | Future |

---

## Integration Priority

1. **Azure Quantum** - Primary backend for algorithm research
2. **D-Wave** - Primary backend for optimization (routing, scheduling)
3. **MS Topological** - Monitor for late 2026 evaluation

---

## Document History

- v1.0 (2026-01-22): Initial tracking document for D-Wave integration
