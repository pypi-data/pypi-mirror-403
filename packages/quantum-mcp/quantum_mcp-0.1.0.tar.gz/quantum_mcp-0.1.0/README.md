# Quantum MCP Server

MCP server providing quantum computing capabilities to Claude Code via the Model Context Protocol. Integrates Azure Quantum (gate-based) and D-Wave (quantum annealing) backends with multi-agent orchestration.

## Project Status

| Phase | Focus | Status | Tests |
|-------|-------|--------|-------|
| Phase 0 | Quantum Foundation (VQE, QAOA, Kernels, Q#) | Complete | ~174 |
| Phase 1 | Multi-Agent Orchestration | Complete | ~180 |
| Phase 3 | Quantum Orchestration (QUBO, D-Wave) | In Progress | ~88 |

**Total: 442 tests passing**

## Architecture

```
Azure Quantum (Gate-Based)     D-Wave (Annealing)
   VQE, QAOA, Kernels, Q#         QUBO Solving
            │                          │
            └──────────┬───────────────┘
                       │
         ┌─────────────┴───────────────┐
         │   Multi-Agent Orchestration │
         │   Routing | Consensus       │
         │   Decomposition             │
         └─────────────┬───────────────┘
                       │
         ┌─────────────┴───────────────┐
         │   Backend Abstraction       │
         │   Azure | D-Wave | Exact    │
         └─────────────┬───────────────┘
                       │
                ┌──────┴──────┐
                │  MCP Server │
                └──────┬──────┘
                       │
                ┌──────┴──────┐
                │ Claude Code │
                └─────────────┘
```

## Requirements

- Python 3.11+
- uv package manager
- Azure Quantum workspace (optional, for cloud execution)
- D-Wave Leap account (optional, for quantum annealing)

## Installation

```bash
git clone https://github.com/ryanmat/quantum_mcp.git
cd quantum_mcp
uv sync --all-extras
```

For D-Wave support:
```bash
uv sync --extra dwave
```

## Configuration

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

### Azure Quantum (Gate-Based)

```bash
AZURE_QUANTUM_WORKSPACE_ID=your-workspace-id
AZURE_QUANTUM_RESOURCE_GROUP=your-resource-group
AZURE_QUANTUM_SUBSCRIPTION_ID=your-subscription-id

# Service Principal (optional)
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
```

### D-Wave Quantum Annealing

```bash
DWAVE_API_TOKEN=DEV-xxx...
DWAVE_SOLVER=Advantage_system6.4
```

### Execution Settings

```bash
DEFAULT_BACKEND=ionq.simulator
MAX_SHOTS=1000
BUDGET_LIMIT_USD=10.0
LOG_LEVEL=INFO
```

## Running the Server

```bash
uv run python -m quantum_mcp
```

## MCP Tools

### Connectivity

| Tool | Description |
|------|-------------|
| `ping` | Test server connectivity |

### Backend Management

| Tool | Description |
|------|-------------|
| `quantum_list_backends` | List Azure Quantum backends |
| `quantum_estimate_cost` | Estimate job cost before submission |

### Circuit Simulation

| Tool | Description |
|------|-------------|
| `quantum_simulate` | Local Qiskit simulation (bell, ghz, qft, custom) |

### Quantum Algorithms

| Tool | Description |
|------|-------------|
| `quantum_vqe` | Variational Quantum Eigensolver for ground state energy |
| `quantum_qaoa` | QAOA for combinatorial optimization (MaxCut) |
| `quantum_kernel` | Quantum kernel matrix for ML classification |
| `quantum_run_qsharp` | Execute Q# quantum programs |
| `quantum_anneal` | Solve QUBO via D-Wave quantum annealing |

### Tool Examples

**VQE (Ground State Energy)**
```python
quantum_vqe(
    num_qubits=2,
    ansatz_type="ry",
    hamiltonian_type="h2",
    optimizer="COBYLA",
    shots=1000
)
```

**QAOA (Combinatorial Optimization)**
```python
quantum_qaoa(
    edges=[[0, 1], [1, 2], [0, 2]],
    layers=2,
    optimizer="COBYLA",
    shots=1000
)
```

**Quantum Annealing (QUBO)**
```python
quantum_anneal(
    qubo={"0,0": -1, "1,1": -1, "0,1": 2},
    num_reads=100,
    backend_type="auto"
)
```

**Q# Execution**
```python
quantum_run_qsharp(
    code='''
    {
        use q = Qubit();
        H(q);
        let result = M(q);
        Reset(q);
        result
    }
    ''',
    shots=100
)
```

## Multi-Agent Orchestration

### Agent Types

- **ClaudeAgent** - Anthropic Claude
- **OpenAIAgent** - OpenAI GPT
- **LocalAgent** - Ollama local models
- **ToolAgent** - Tool-based wrapper

### Routing Strategies

- **CapabilityRouter** - Routes by agent capabilities
- **LoadBalancingRouter** - Distributes load
- **LearnedRouter** - ML-based with performance tracking
- **QUBORouter** - QUBO formulation for routing
- **QAOARouter** - Quantum-enhanced via QAOA
- **DWaveRouter** - D-Wave annealing for routing

### Consensus Mechanisms

- **VotingConsensus** - Majority voting
- **WeightedMergeConsensus** - Weighted merging
- **DebateConsensus** - Multi-round debate

## Project Structure

```
quantum_mcp/
├── src/quantum_mcp/
│   ├── __main__.py              # Entry point
│   ├── config.py                # Configuration
│   ├── server.py                # MCP server
│   ├── agents/                  # Agent implementations
│   ├── backends/                # Quantum backends
│   │   ├── annealing.py         # Annealing protocol
│   │   ├── dwave.py             # D-Wave Leap
│   │   └── exact_solver.py      # Classical fallback
│   ├── circuits/                # Quantum algorithms
│   │   ├── vqe.py               # VQE
│   │   ├── qaoa.py              # QAOA
│   │   ├── kernels.py           # QML kernels
│   │   └── qsharp.py            # Q#
│   ├── client/                  # Azure Quantum client
│   ├── orchestration/           # Multi-agent system
│   │   ├── router.py            # Routing strategies
│   │   ├── consensus.py         # Consensus mechanisms
│   │   ├── decomposer.py        # Task decomposition
│   │   ├── qubo.py              # QUBO formulation
│   │   ├── qaoa_router.py       # QAOA router
│   │   └── dwave_router.py      # D-Wave router
│   └── tools/                   # MCP tools
│       ├── registration.py      # Tool registration
│       └── algorithm_tools.py   # Algorithm tools
├── tests/
│   ├── unit/                    # Unit tests (442)
│   └── integration/             # Integration tests
├── docs/                        # Internal documentation
├── mcp.json                     # MCP configuration
├── pyproject.toml               # Project config
└── .env.example                 # Environment template
```

## Testing

```bash
# Unit tests
uv run pytest tests/unit -v

# With coverage
uv run pytest tests/unit --cov=quantum_mcp

# Integration tests (requires credentials)
uv run pytest tests/integration -v
```

## Cost Management

Default budget: $10.00 USD

Backend costs:
- IonQ Simulator: Free
- IonQ Hardware: ~$0.01/shot
- D-Wave: Per-second QPU time
- Quantinuum: Varies by plan

Use `quantum_estimate_cost` before Azure hardware submissions.

## MCP Configuration for Claude Code

Add to your `~/.claude/mcp.json`:

```json
{
  "mcpServers": {
    "quantum": {
      "command": "uv",
      "args": ["--directory", "/path/to/quantum_mcp", "run", "python", "-m", "quantum_mcp"],
      "env": {
        "DWAVE_API_TOKEN": "DEV-xxx..."
      }
    }
  }
}
```

## Dependencies

**Core:**
- azure-quantum, azure-identity
- qiskit, qiskit-aer
- qsharp
- mcp
- pydantic

**Optional:**
- anthropic, openai (agents)
- dwave-ocean-sdk, dimod (annealing)

**Dev:**
- pytest, pytest-asyncio, pytest-cov
- ruff, mypy

## Related Projects

**predictive-insights** - Temporal X-DEC for metric prediction
- BiGRU-XVAE-DEC with temporal attention
- 5 semantic operational state clusters

Future integration planned at Phase 14 (MoE).

## License

MIT
