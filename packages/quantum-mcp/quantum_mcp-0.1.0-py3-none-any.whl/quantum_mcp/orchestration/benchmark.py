# Description: Baseline benchmarking infrastructure for collective performance.
# Description: Provides benchmark suites, metrics collection, and reporting.
"""Baseline benchmarking infrastructure for collective performance."""

from __future__ import annotations

import statistics
import time
from typing import TYPE_CHECKING

import structlog
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    pass

from quantum_mcp.agents.base import BaseAgent
from quantum_mcp.agents.protocol import AgentStatus
from quantum_mcp.orchestration.collective import Collective, CollectiveConfig
from quantum_mcp.orchestration.task import Task

logger = structlog.get_logger()


class BenchmarkConfig(BaseModel):
    """Configuration for benchmark execution."""

    iterations: int = Field(
        default=10,
        ge=1,
        description="Number of benchmark iterations",
    )
    warmup_iterations: int = Field(
        default=2,
        ge=0,
        description="Number of warmup iterations (not counted)",
    )
    timeout_seconds: float = Field(
        default=60.0,
        ge=1.0,
        description="Timeout for each iteration",
    )
    record_responses: bool = Field(
        default=False,
        description="Whether to record full responses",
    )


class BenchmarkMetrics(BaseModel):
    """Statistical metrics for benchmark measurements."""

    count: int = Field(..., description="Number of measurements")
    mean: float = Field(..., description="Arithmetic mean")
    std: float = Field(default=0.0, description="Standard deviation")
    min: float = Field(..., description="Minimum value")
    max: float = Field(..., description="Maximum value")
    p50: float = Field(default=0.0, description="50th percentile (median)")
    p95: float = Field(default=0.0, description="95th percentile")
    p99: float = Field(default=0.0, description="99th percentile")

    @classmethod
    def from_values(cls, values: list[float]) -> "BenchmarkMetrics":
        """Create metrics from a list of values.

        Args:
            values: List of measurements

        Returns:
            BenchmarkMetrics instance
        """
        if not values:
            return cls(count=0, mean=0.0, min=0.0, max=0.0)

        sorted_values = sorted(values)
        n = len(sorted_values)

        def percentile(p: float) -> float:
            k = (n - 1) * p / 100
            f = int(k)
            c = f + 1 if f + 1 < n else f
            return sorted_values[f] + (k - f) * (sorted_values[c] - sorted_values[f])

        return cls(
            count=n,
            mean=statistics.mean(values),
            std=statistics.stdev(values) if n > 1 else 0.0,
            min=min(values),
            max=max(values),
            p50=percentile(50),
            p95=percentile(95),
            p99=percentile(99),
        )


class BenchmarkResult(BaseModel):
    """Result of a benchmark run."""

    name: str = Field(..., description="Benchmark name")
    iterations: int = Field(..., description="Number of iterations run")
    latency_metrics: BenchmarkMetrics = Field(
        ...,
        description="Latency statistics (ms)",
    )
    success_rate: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Fraction of successful iterations",
    )
    error_count: int = Field(
        default=0,
        description="Number of failed iterations",
    )
    total_tokens: int | None = Field(
        default=None,
        description="Total tokens used",
    )
    throughput_per_second: float | None = Field(
        default=None,
        description="Iterations per second",
    )
    agents_used: list[str] = Field(
        default_factory=list,
        description="IDs of agents used",
    )
    metadata: dict = Field(
        default_factory=dict,
        description="Additional metadata",
    )


class Benchmark:
    """Base class for benchmarks."""

    def __init__(
        self,
        name: str,
        description: str = "",
        config: BenchmarkConfig | None = None,
    ) -> None:
        """Initialize benchmark.

        Args:
            name: Benchmark name
            description: Benchmark description
            config: Benchmark configuration
        """
        self.name = name
        self.description = description
        self.config = config or BenchmarkConfig()
        self._logger = logger.bind(benchmark=name)


class TaskBenchmark(Benchmark):
    """Benchmark for measuring task execution performance."""

    def __init__(
        self,
        name: str,
        agents: list[BaseAgent],
        config: BenchmarkConfig | None = None,
        collective_config: CollectiveConfig | None = None,
    ) -> None:
        """Initialize task benchmark.

        Args:
            name: Benchmark name
            agents: Agents to benchmark
            config: Benchmark configuration
            collective_config: Configuration for the collective
        """
        super().__init__(name=name, config=config)
        self._agents = agents
        self._collective_config = collective_config
        self._collective = Collective(
            agents=agents,
            config=collective_config,
        )

    async def run(self, task: Task) -> BenchmarkResult:
        """Run benchmark on a task.

        Args:
            task: Task to benchmark

        Returns:
            BenchmarkResult with measurements
        """
        self._logger.info(
            "Starting benchmark",
            iterations=self.config.iterations,
            warmup=self.config.warmup_iterations,
        )

        # Warmup iterations
        for i in range(self.config.warmup_iterations):
            self._logger.debug("Warmup iteration", iteration=i + 1)
            await self._collective.execute(task)

        # Actual benchmark iterations
        latencies = []
        total_tokens = 0
        error_count = 0
        agents_used = set()
        start_time = time.monotonic()

        for i in range(self.config.iterations):
            iter_start = time.monotonic()

            try:
                result = await self._collective.execute(task)

                if result.success:
                    latency_ms = (time.monotonic() - iter_start) * 1000
                    latencies.append(latency_ms)
                    total_tokens += result.total_tokens or 0
                    agents_used.update(result.agents_used)
                else:
                    error_count += 1
            except Exception as e:
                self._logger.error("Iteration failed", iteration=i + 1, error=str(e))
                error_count += 1

        total_time = time.monotonic() - start_time
        success_count = self.config.iterations - error_count

        latency_metrics = BenchmarkMetrics.from_values(latencies)
        throughput = (
            self.config.iterations / total_time if total_time > 0 else 0.0
        )

        self._logger.info(
            "Benchmark complete",
            mean_latency_ms=latency_metrics.mean,
            success_rate=success_count / self.config.iterations,
            throughput=throughput,
        )

        return BenchmarkResult(
            name=self.name,
            iterations=self.config.iterations,
            latency_metrics=latency_metrics,
            success_rate=success_count / self.config.iterations,
            error_count=error_count,
            total_tokens=total_tokens,
            throughput_per_second=throughput,
            agents_used=list(agents_used),
        )


class BenchmarkSuite:
    """Suite for running multiple benchmarks."""

    def __init__(
        self,
        name: str,
        agents: list[BaseAgent],
        config: BenchmarkConfig | None = None,
    ) -> None:
        """Initialize benchmark suite.

        Args:
            name: Suite name
            agents: Agents to benchmark
            config: Default benchmark configuration
        """
        self.name = name
        self._agents = agents
        self._config = config or BenchmarkConfig()
        self._logger = logger.bind(suite=name)

    async def run(self, tasks: list[Task]) -> list[BenchmarkResult]:
        """Run benchmarks for multiple tasks.

        Args:
            tasks: Tasks to benchmark

        Returns:
            List of benchmark results
        """
        self._logger.info("Starting benchmark suite", num_tasks=len(tasks))

        results = []
        for i, task in enumerate(tasks):
            benchmark = TaskBenchmark(
                name=f"{self.name}_task_{i + 1}",
                agents=self._agents,
                config=self._config,
            )
            result = await benchmark.run(task)
            results.append(result)

        self._logger.info("Benchmark suite complete", num_results=len(results))
        return results

    def generate_report(self, results: list[BenchmarkResult]) -> str:
        """Generate a summary report for benchmark results.

        Args:
            results: Benchmark results to summarize

        Returns:
            Formatted report string
        """
        lines = [
            f"# Benchmark Suite: {self.name}",
            "",
            f"Tasks benchmarked: {len(results)}",
            f"Iterations per task: {self._config.iterations}",
            "",
            "## Results Summary",
            "",
        ]

        for result in results:
            lines.extend([
                f"### {result.name}",
                f"- Success Rate: {result.success_rate * 100:.1f}%",
                f"- Mean Latency: {result.latency_metrics.mean:.2f} ms",
                f"- P95 Latency: {result.latency_metrics.p95:.2f} ms",
                f"- P99 Latency: {result.latency_metrics.p99:.2f} ms",
                f"- Throughput: {result.throughput_per_second:.2f}/s",
                "",
            ])

        # Overall summary
        if results:
            all_means = [r.latency_metrics.mean for r in results]
            all_success = [r.success_rate for r in results]

            lines.extend([
                "## Overall Statistics",
                f"- Average Mean Latency: {statistics.mean(all_means):.2f} ms",
                f"- Average Success Rate: {statistics.mean(all_success) * 100:.1f}%",
                "",
            ])

        return "\n".join(lines)

    def compare(
        self,
        baseline: BenchmarkResult,
        optimized: BenchmarkResult,
    ) -> dict:
        """Compare two benchmark results.

        Args:
            baseline: Baseline result
            optimized: Optimized result to compare

        Returns:
            Comparison metrics
        """
        baseline_mean = baseline.latency_metrics.mean
        optimized_mean = optimized.latency_metrics.mean

        improvement = (
            (baseline_mean - optimized_mean) / baseline_mean * 100
            if baseline_mean > 0 else 0.0
        )

        return {
            "baseline_name": baseline.name,
            "optimized_name": optimized.name,
            "baseline_mean": baseline_mean,
            "optimized_mean": optimized_mean,
            "latency_improvement": improvement,
            "baseline_success_rate": baseline.success_rate,
            "optimized_success_rate": optimized.success_rate,
            "success_rate_change": (
                optimized.success_rate - baseline.success_rate
            ) * 100,
        }
