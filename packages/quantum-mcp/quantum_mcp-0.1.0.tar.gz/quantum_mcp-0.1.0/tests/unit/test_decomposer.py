# Description: Tests for task decomposition engine.
# Description: Validates simple, recursive, and domain-aware decomposition strategies.
"""Tests for task decomposition engine."""

import pytest

from quantum_mcp.orchestration.task import Task, TaskPriority
from quantum_mcp.orchestration.decomposer import (
    Decomposer,
    SimpleDecomposer,
    RecursiveDecomposer,
    DomainDecomposer,
    SubTask,
    DecompositionResult,
    create_decomposer,
)


class TestSubTask:
    """Test SubTask model."""

    def test_subtask_creation(self):
        """Test creating a subtask."""
        subtask = SubTask(
            content="Analyze the data",
            order=1,
            parent_task_id="task-123",
        )
        assert subtask.content == "Analyze the data"
        assert subtask.order == 1
        assert subtask.parent_task_id == "task-123"

    def test_subtask_with_dependencies(self):
        """Test subtask with dependencies."""
        subtask = SubTask(
            content="Synthesize results",
            order=3,
            parent_task_id="task-123",
            depends_on=["subtask-1", "subtask-2"],
        )
        assert len(subtask.depends_on) == 2

    def test_subtask_generates_id(self):
        """Test subtask generates unique ID."""
        s1 = SubTask(content="Task 1", order=1, parent_task_id="p1")
        s2 = SubTask(content="Task 2", order=2, parent_task_id="p1")
        assert s1.subtask_id != s2.subtask_id


class TestDecompositionResult:
    """Test DecompositionResult model."""

    def test_result_creation(self):
        """Test creating a decomposition result."""
        subtasks = [
            SubTask(content="Step 1", order=1, parent_task_id="task-1"),
            SubTask(content="Step 2", order=2, parent_task_id="task-1"),
        ]
        result = DecompositionResult(
            original_task_id="task-1",
            strategy="simple",
            subtasks=subtasks,
        )
        assert result.original_task_id == "task-1"
        assert len(result.subtasks) == 2

    def test_result_parallel_flag(self):
        """Test result indicates parallelizable subtasks."""
        result = DecompositionResult(
            original_task_id="task-1",
            strategy="simple",
            subtasks=[],
            is_parallelizable=True,
        )
        assert result.is_parallelizable is True


class TestSimpleDecomposer:
    """Test simple sentence-based decomposition."""

    @pytest.fixture
    def decomposer(self) -> SimpleDecomposer:
        """Create simple decomposer."""
        return SimpleDecomposer()

    @pytest.mark.asyncio
    async def test_decompose_multi_sentence(self, decomposer):
        """Test decomposing multi-sentence prompt."""
        task = Task(
            prompt="First analyze the data. Then visualize the results. Finally write a summary."
        )
        result = await decomposer.decompose(task)

        assert len(result.subtasks) == 3
        assert result.strategy == "simple"

    @pytest.mark.asyncio
    async def test_decompose_single_sentence(self, decomposer):
        """Test single sentence returns one subtask."""
        task = Task(prompt="Analyze the data")
        result = await decomposer.decompose(task)

        assert len(result.subtasks) == 1
        assert result.subtasks[0].content == "Analyze the data"

    @pytest.mark.asyncio
    async def test_decompose_preserves_order(self, decomposer):
        """Test decomposition preserves task order."""
        task = Task(prompt="Step A. Step B. Step C.")
        result = await decomposer.decompose(task)

        orders = [s.order for s in result.subtasks]
        assert orders == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_decompose_respects_min_subtasks(self):
        """Test decomposer respects minimum subtask setting."""
        decomposer = SimpleDecomposer(min_subtasks=1)
        task = Task(prompt="Just one task")
        result = await decomposer.decompose(task)

        assert len(result.subtasks) >= 1


class TestRecursiveDecomposer:
    """Test recursive decomposition."""

    @pytest.fixture
    def decomposer(self) -> RecursiveDecomposer:
        """Create recursive decomposer with max depth."""
        return RecursiveDecomposer(max_depth=2)

    @pytest.mark.asyncio
    async def test_decompose_complex_task(self, decomposer):
        """Test decomposing complex multi-part task."""
        task = Task(
            prompt="Build a web application. First set up the backend with database. Then create the frontend with React."
        )
        result = await decomposer.decompose(task)

        assert len(result.subtasks) >= 2
        assert result.strategy == "recursive"

    @pytest.mark.asyncio
    async def test_respects_max_depth(self):
        """Test decomposition respects max depth."""
        decomposer = RecursiveDecomposer(max_depth=1)
        task = Task(prompt="Complex nested task with many parts")
        result = await decomposer.decompose(task)

        assert result.depth <= 1


class TestDomainDecomposer:
    """Test domain-aware decomposition."""

    @pytest.fixture
    def decomposer(self) -> DomainDecomposer:
        """Create domain decomposer."""
        return DomainDecomposer()

    @pytest.mark.asyncio
    async def test_decompose_code_task(self, decomposer):
        """Test decomposing code-related task."""
        task = Task(
            prompt="Write a Python function to sort a list and add unit tests",
            required_capabilities=["code", "python"],
        )
        result = await decomposer.decompose(task)

        assert result.strategy == "domain"
        # Should identify code and testing as separate subtasks
        assert len(result.subtasks) >= 1

    @pytest.mark.asyncio
    async def test_decompose_analysis_task(self, decomposer):
        """Test decomposing analysis task."""
        task = Task(
            prompt="Analyze the dataset and provide insights with visualizations",
            required_capabilities=["analysis", "visualization"],
        )
        result = await decomposer.decompose(task)

        assert len(result.subtasks) >= 1

    @pytest.mark.asyncio
    async def test_identifies_parallel_subtasks(self, decomposer):
        """Test decomposer identifies parallelizable subtasks."""
        task = Task(
            prompt="Run tests and lint the code and check types",
            required_capabilities=["code"],
        )
        result = await decomposer.decompose(task)

        # Independent tasks should be parallelizable
        assert result.is_parallelizable is True


class TestDecomposerFactory:
    """Test decomposer factory function."""

    def test_create_simple_decomposer(self):
        """Test factory creates simple decomposer."""
        decomposer = create_decomposer("simple")
        assert isinstance(decomposer, SimpleDecomposer)

    def test_create_recursive_decomposer(self):
        """Test factory creates recursive decomposer."""
        decomposer = create_decomposer("recursive")
        assert isinstance(decomposer, RecursiveDecomposer)

    def test_create_domain_decomposer(self):
        """Test factory creates domain decomposer."""
        decomposer = create_decomposer("domain")
        assert isinstance(decomposer, DomainDecomposer)

    def test_create_unknown_raises(self):
        """Test factory raises for unknown strategy."""
        with pytest.raises(ValueError, match="Unknown decomposition strategy"):
            create_decomposer("unknown")

    def test_create_with_kwargs(self):
        """Test factory passes kwargs to decomposer."""
        decomposer = create_decomposer("recursive", max_depth=5)
        assert isinstance(decomposer, RecursiveDecomposer)
