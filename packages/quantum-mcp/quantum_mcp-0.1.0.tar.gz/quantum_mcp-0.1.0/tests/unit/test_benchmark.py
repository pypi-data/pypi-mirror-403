# Description: Tests for baseline benchmarking infrastructure.
# Description: Validates benchmark suites, metrics, and reporting.
"""Tests for baseline benchmarking infrastructure."""

import pytest

from quantum_mcp.agents import AgentCapability, AgentConfig, AgentResponse, AgentStatus
from quantum_mcp.agents.base import BaseAgent
from quantum_mcp.orchestration.task import Task
from quantum_mcp.orchestration.benchmark import (
    Benchmark,
    BenchmarkConfig,
    BenchmarkResult,
    BenchmarkSuite,
    BenchmarkMetrics,
    TaskBenchmark,
)


class MockBenchmarkAgent(BaseAgent):
    """Mock agent for benchmark testing."""

    def __init__(
        self,
        config: AgentConfig,
        latency_ms: float = 50.0,
        tokens: int = 100,
    ):
        super().__init__(config)
        self._latency_ms = latency_ms
        self._tokens = tokens

    async def execute(self, prompt: str) -> AgentResponse:
        return AgentResponse(
            agent_id=self.agent_id,
            content=f"Response to: {prompt[:50]}",
            status=AgentStatus.SUCCESS,
            tokens_used=self._tokens,
            latency_ms=self._latency_ms,
        )

    async def stream(self, prompt: str):
        yield f"Response to: {prompt[:50]}"

    async def health_check(self) -> bool:
        return True


class TestBenchmarkConfig:
    """Test BenchmarkConfig model."""

    def test_default_config(self):
        """Test default benchmark configuration."""
        config = BenchmarkConfig()
        assert config.iterations == 10
        assert config.warmup_iterations == 2
        assert config.timeout_seconds == 60.0

    def test_custom_config(self):
        """Test custom benchmark configuration."""
        config = BenchmarkConfig(
            iterations=100,
            warmup_iterations=10,
            timeout_seconds=120.0,
        )
        assert config.iterations == 100


class TestBenchmarkMetrics:
    """Test BenchmarkMetrics model."""

    def test_metrics_from_values(self):
        """Test creating metrics from values."""
        values = [10.0, 20.0, 30.0, 40.0, 50.0]
        metrics = BenchmarkMetrics.from_values(values)

        assert metrics.count == 5
        assert metrics.mean == 30.0
        assert metrics.min == 10.0
        assert metrics.max == 50.0

    def test_metrics_percentiles(self):
        """Test percentile calculation."""
        values = list(range(1, 101))  # 1 to 100
        metrics = BenchmarkMetrics.from_values(values)

        assert metrics.p50 == pytest.approx(50.5, rel=0.1)
        assert metrics.p95 == pytest.approx(95.05, rel=0.1)
        assert metrics.p99 == pytest.approx(99.01, rel=0.1)

    def test_empty_values(self):
        """Test handling empty values."""
        metrics = BenchmarkMetrics.from_values([])

        assert metrics.count == 0
        assert metrics.mean == 0.0


class TestBenchmarkResult:
    """Test BenchmarkResult model."""

    def test_result_creation(self):
        """Test creating a benchmark result."""
        result = BenchmarkResult(
            name="test_benchmark",
            iterations=10,
            latency_metrics=BenchmarkMetrics.from_values([100.0] * 10),
            success_rate=1.0,
        )

        assert result.name == "test_benchmark"
        assert result.success_rate == 1.0

    def test_result_with_failure(self):
        """Test result with some failures."""
        result = BenchmarkResult(
            name="partial_success",
            iterations=10,
            latency_metrics=BenchmarkMetrics.from_values([100.0] * 7),
            success_rate=0.7,
            error_count=3,
        )

        assert result.success_rate == 0.7
        assert result.error_count == 3


class TestBenchmark:
    """Test Benchmark base class."""

    @pytest.fixture
    def agents(self) -> list[MockBenchmarkAgent]:
        """Create test agents."""
        return [
            MockBenchmarkAgent(
                AgentConfig(name="fast-agent", provider="test"),
                latency_ms=10.0,
            ),
            MockBenchmarkAgent(
                AgentConfig(name="slow-agent", provider="test"),
                latency_ms=100.0,
            ),
        ]

    def test_benchmark_creation(self):
        """Test creating a benchmark."""
        benchmark = Benchmark(
            name="test_benchmark",
            description="A test benchmark",
        )
        assert benchmark.name == "test_benchmark"


class TestTaskBenchmark:
    """Test TaskBenchmark for task execution."""

    @pytest.fixture
    def agents(self) -> list[MockBenchmarkAgent]:
        """Create test agents."""
        return [
            MockBenchmarkAgent(
                AgentConfig(
                    name="test-agent",
                    provider="test",
                    capabilities=[
                        AgentCapability(name="general", description="General"),
                    ],
                ),
                latency_ms=50.0,
                tokens=100,
            ),
        ]

    @pytest.fixture
    def benchmark(self, agents) -> TaskBenchmark:
        """Create task benchmark."""
        return TaskBenchmark(
            name="task_execution",
            agents=agents,
            config=BenchmarkConfig(iterations=5, warmup_iterations=1),
        )

    @pytest.mark.asyncio
    async def test_run_benchmark(self, benchmark):
        """Test running a task benchmark."""
        task = Task(prompt="Benchmark test task")
        result = await benchmark.run(task)

        assert result.name == "task_execution"
        assert result.iterations == 5
        assert result.success_rate > 0

    @pytest.mark.asyncio
    async def test_benchmark_records_latency(self, benchmark):
        """Test benchmark records latency metrics."""
        task = Task(prompt="Latency test")
        result = await benchmark.run(task)

        assert result.latency_metrics.count == 5
        assert result.latency_metrics.mean > 0

    @pytest.mark.asyncio
    async def test_benchmark_tokens_tracked(self, benchmark):
        """Test benchmark tracks token usage."""
        task = Task(prompt="Token test")
        result = await benchmark.run(task)

        assert result.total_tokens is not None
        assert result.total_tokens > 0


class TestBenchmarkSuite:
    """Test BenchmarkSuite for running multiple benchmarks."""

    @pytest.fixture
    def agents(self) -> list[MockBenchmarkAgent]:
        """Create test agents."""
        return [
            MockBenchmarkAgent(
                AgentConfig(name="test-agent", provider="test"),
                latency_ms=50.0,
            ),
        ]

    @pytest.fixture
    def suite(self, agents) -> BenchmarkSuite:
        """Create benchmark suite."""
        return BenchmarkSuite(
            name="test_suite",
            agents=agents,
            config=BenchmarkConfig(iterations=3, warmup_iterations=1),
        )

    def test_suite_creation(self, suite):
        """Test creating a benchmark suite."""
        assert suite.name == "test_suite"

    @pytest.mark.asyncio
    async def test_run_suite(self, suite):
        """Test running benchmark suite."""
        tasks = [
            Task(prompt="Task 1"),
            Task(prompt="Task 2"),
        ]
        results = await suite.run(tasks)

        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_suite_generates_report(self, suite):
        """Test suite generates summary report."""
        tasks = [
            Task(prompt="Task 1"),
            Task(prompt="Task 2"),
        ]
        results = await suite.run(tasks)
        report = suite.generate_report(results)

        assert "test_suite" in report
        assert "mean" in report.lower() or "latency" in report.lower()

    def test_compare_results(self, suite):
        """Test comparing benchmark results."""
        result1 = BenchmarkResult(
            name="baseline",
            iterations=10,
            latency_metrics=BenchmarkMetrics.from_values([100.0] * 10),
            success_rate=1.0,
        )
        result2 = BenchmarkResult(
            name="optimized",
            iterations=10,
            latency_metrics=BenchmarkMetrics.from_values([50.0] * 10),
            success_rate=1.0,
        )

        comparison = suite.compare(result1, result2)

        assert comparison["latency_improvement"] > 0
        assert comparison["baseline_mean"] == 100.0
        assert comparison["optimized_mean"] == 50.0
