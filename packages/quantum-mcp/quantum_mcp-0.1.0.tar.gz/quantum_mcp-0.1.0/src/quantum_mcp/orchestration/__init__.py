# Description: Orchestration module for multi-agent coordination.
# Description: Exports collective, observability, benchmark, router, consensus.
"""Orchestration module for multi-agent coordination."""

from quantum_mcp.orchestration.benchmark import (
    Benchmark,
    BenchmarkConfig,
    BenchmarkMetrics,
    BenchmarkResult,
    BenchmarkSuite,
    TaskBenchmark,
)
from quantum_mcp.orchestration.collective import (
    Collective,
    CollectiveConfig,
    CollectiveHealthStatus,
    CollectiveResult,
    ExecutionMode,
)
from quantum_mcp.orchestration.consensus import (
    Consensus,
    ConsensusResult,
    DebateConsensus,
    VotingConsensus,
    WeightedMergeConsensus,
    create_consensus,
)
from quantum_mcp.orchestration.dwave_router import DWaveRouter
from quantum_mcp.orchestration.decomposer import (
    DecompositionResult,
    Decomposer,
    DomainDecomposer,
    RecursiveDecomposer,
    SimpleDecomposer,
    SubTask,
    create_decomposer,
)
from quantum_mcp.orchestration.observability import (
    Event,
    EventEmitter,
    EventSeverity,
    MetricsCollector,
    Span,
    SpanContext,
    SpanStatus,
    Tracer,
)
from quantum_mcp.orchestration.qaoa_router import (
    QAOARouter,
    build_qubo_qaoa_circuit,
    ising_to_qaoa_cost,
    qubo_to_ising,
)
from quantum_mcp.orchestration.qubo import (
    QUBOFormulation,
    QUBORouter,
    RouteQUBO,
)
from quantum_mcp.orchestration.router import (
    CapabilityRouter,
    LearnedRouter,
    LoadBalancingRouter,
    Router,
    RoutingDecision,
    create_router,
)
from quantum_mcp.orchestration.task import (
    Task,
    TaskMetadata,
    TaskPriority,
    TaskResult,
    TaskStatus,
)

__all__ = [
    "Benchmark",
    "BenchmarkConfig",
    "BenchmarkMetrics",
    "BenchmarkResult",
    "BenchmarkSuite",
    "CapabilityRouter",
    "Collective",
    "CollectiveConfig",
    "CollectiveHealthStatus",
    "CollectiveResult",
    "Consensus",
    "ConsensusResult",
    "DebateConsensus",
    "DecompositionResult",
    "Decomposer",
    "DomainDecomposer",
    "DWaveRouter",
    "Event",
    "EventEmitter",
    "EventSeverity",
    "ExecutionMode",
    "LearnedRouter",
    "LoadBalancingRouter",
    "MetricsCollector",
    "QAOARouter",
    "QUBOFormulation",
    "QUBORouter",
    "RecursiveDecomposer",
    "RouteQUBO",
    "Router",
    "RoutingDecision",
    "SimpleDecomposer",
    "Span",
    "SpanContext",
    "SpanStatus",
    "SubTask",
    "Task",
    "TaskBenchmark",
    "TaskMetadata",
    "TaskPriority",
    "TaskResult",
    "TaskStatus",
    "Tracer",
    "VotingConsensus",
    "WeightedMergeConsensus",
    "build_qubo_qaoa_circuit",
    "create_consensus",
    "create_decomposer",
    "create_router",
    "ising_to_qaoa_cost",
    "qubo_to_ising",
]
