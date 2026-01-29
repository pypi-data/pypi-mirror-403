# Description: Task decomposition engine for breaking down complex tasks.
# Description: Provides simple, recursive, and domain-aware decomposition strategies.
"""Task decomposition engine for breaking down complex tasks."""

from __future__ import annotations

import re
import uuid
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

import structlog
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    pass

from quantum_mcp.orchestration.task import Task

logger = structlog.get_logger()


class SubTask(BaseModel):
    """A subtask derived from decomposing a larger task."""

    subtask_id: str = Field(
        default_factory=lambda: f"subtask-{uuid.uuid4().hex[:12]}",
        description="Unique identifier for the subtask",
    )
    content: str = Field(..., description="The subtask content/prompt")
    order: int = Field(..., ge=1, description="Execution order (1-indexed)")
    parent_task_id: str = Field(..., description="ID of the parent task")
    depends_on: list[str] = Field(
        default_factory=list,
        description="IDs of subtasks this depends on",
    )
    required_capabilities: list[str] = Field(
        default_factory=list,
        description="Capabilities needed for this subtask",
    )
    estimated_complexity: float = Field(
        default=1.0,
        ge=0.0,
        le=10.0,
        description="Estimated complexity (0-10 scale)",
    )


class DecompositionResult(BaseModel):
    """Result of decomposing a task into subtasks."""

    original_task_id: str = Field(..., description="ID of the original task")
    strategy: str = Field(..., description="Decomposition strategy used")
    subtasks: list[SubTask] = Field(
        default_factory=list,
        description="List of subtasks",
    )
    is_parallelizable: bool = Field(
        default=False,
        description="Whether subtasks can run in parallel",
    )
    depth: int = Field(
        default=1,
        ge=1,
        description="Decomposition depth (for recursive)",
    )
    reasoning: str | None = Field(
        default=None,
        description="Explanation of decomposition logic",
    )


class Decomposer(ABC):
    """Abstract base class for task decomposers.

    Decomposers break complex tasks into smaller, manageable subtasks
    that can be distributed across agents.
    """

    def __init__(self) -> None:
        """Initialize decomposer."""
        self._logger = logger.bind(decomposer=self.__class__.__name__)

    @abstractmethod
    async def decompose(self, task: Task) -> DecompositionResult:
        """Decompose a task into subtasks.

        Args:
            task: Task to decompose

        Returns:
            DecompositionResult with subtasks
        """
        raise NotImplementedError


class SimpleDecomposer(Decomposer):
    """Simple sentence-based decomposition.

    Splits task prompts by sentences, treating each as a subtask.
    """

    def __init__(self, min_subtasks: int = 1) -> None:
        """Initialize simple decomposer.

        Args:
            min_subtasks: Minimum number of subtasks to produce
        """
        super().__init__()
        self._min_subtasks = min_subtasks

    async def decompose(self, task: Task) -> DecompositionResult:
        """Decompose task by splitting on sentence boundaries.

        Args:
            task: Task to decompose

        Returns:
            DecompositionResult with sentence-based subtasks
        """
        # Split on sentence-ending punctuation
        sentences = re.split(r'(?<=[.!?])\s+', task.prompt.strip())
        sentences = [s.strip() for s in sentences if s.strip()]

        if len(sentences) < self._min_subtasks:
            sentences = [task.prompt]

        subtasks = []
        for i, sentence in enumerate(sentences, 1):
            subtask = SubTask(
                content=sentence,
                order=i,
                parent_task_id=task.task_id,
                required_capabilities=task.required_capabilities.copy(),
            )
            subtasks.append(subtask)

        self._logger.debug(
            "Simple decomposition complete",
            task_id=task.task_id,
            num_subtasks=len(subtasks),
        )

        return DecompositionResult(
            original_task_id=task.task_id,
            strategy="simple",
            subtasks=subtasks,
            is_parallelizable=False,
            reasoning=f"Split prompt into {len(subtasks)} sentences",
        )


class RecursiveDecomposer(Decomposer):
    """Recursive decomposition with depth control.

    Breaks tasks into subtasks, potentially decomposing subtasks further.
    """

    def __init__(self, max_depth: int = 2) -> None:
        """Initialize recursive decomposer.

        Args:
            max_depth: Maximum recursion depth
        """
        super().__init__()
        self._max_depth = max_depth

    async def decompose(self, task: Task) -> DecompositionResult:
        """Decompose task recursively.

        Args:
            task: Task to decompose

        Returns:
            DecompositionResult with hierarchical subtasks
        """
        subtasks = await self._decompose_recursive(
            task.prompt,
            task.task_id,
            task.required_capabilities,
            current_depth=1,
        )

        self._logger.debug(
            "Recursive decomposition complete",
            task_id=task.task_id,
            num_subtasks=len(subtasks),
            max_depth=self._max_depth,
        )

        return DecompositionResult(
            original_task_id=task.task_id,
            strategy="recursive",
            subtasks=subtasks,
            is_parallelizable=self._check_parallelizable(subtasks),
            depth=min(self._max_depth, len(subtasks)),
            reasoning=f"Recursive decomposition with max depth {self._max_depth}",
        )

    async def _decompose_recursive(
        self,
        content: str,
        parent_id: str,
        capabilities: list[str],
        current_depth: int,
    ) -> list[SubTask]:
        """Recursively decompose content.

        Args:
            content: Content to decompose
            parent_id: Parent task ID
            capabilities: Required capabilities
            current_depth: Current recursion depth

        Returns:
            List of subtasks
        """
        if current_depth > self._max_depth:
            return [
                SubTask(
                    content=content,
                    order=1,
                    parent_task_id=parent_id,
                    required_capabilities=capabilities.copy(),
                )
            ]

        # Split on major delimiters (periods, "then", "and then", numbered items)
        parts = self._split_content(content)

        if len(parts) <= 1:
            return [
                SubTask(
                    content=content.strip(),
                    order=1,
                    parent_task_id=parent_id,
                    required_capabilities=capabilities.copy(),
                )
            ]

        subtasks = []
        for i, part in enumerate(parts, 1):
            part = part.strip()
            if not part:
                continue

            subtask = SubTask(
                content=part,
                order=i,
                parent_task_id=parent_id,
                required_capabilities=capabilities.copy(),
            )
            subtasks.append(subtask)

        return subtasks

    def _split_content(self, content: str) -> list[str]:
        """Split content into logical parts.

        Args:
            content: Content to split

        Returns:
            List of content parts
        """
        # Try numbered list first
        numbered = re.split(r'\d+[.)]\s*', content)
        if len(numbered) > 1:
            return [p for p in numbered if p.strip()]

        # Try "then" / "and then" delimiters
        then_parts = re.split(r'\.\s*(?:and\s+)?then\s+', content, flags=re.IGNORECASE)
        if len(then_parts) > 1:
            return then_parts

        # Fall back to sentence splitting
        sentences = re.split(r'(?<=[.!?])\s+', content)
        return [s for s in sentences if s.strip()]

    def _check_parallelizable(self, subtasks: list[SubTask]) -> bool:
        """Check if subtasks can run in parallel.

        Args:
            subtasks: List of subtasks

        Returns:
            True if subtasks have no dependencies
        """
        return all(len(s.depends_on) == 0 for s in subtasks)


class DomainDecomposer(Decomposer):
    """Domain-aware decomposition using capability hints.

    Uses required capabilities and domain patterns to intelligently
    decompose tasks.
    """

    # Domain-specific patterns for identifying subtasks
    DOMAIN_PATTERNS: dict[str, list[str]] = {
        "code": [
            r"(?:write|create|implement)\s+(?:a\s+)?(?:function|class|module)",
            r"(?:add\s+)?(?:unit\s+)?tests?",
            r"(?:add\s+)?(?:type\s+)?(?:hints?|annotations?)",
            r"(?:refactor|optimize)",
            r"(?:document|add\s+(?:doc)?strings?)",
        ],
        "analysis": [
            r"(?:analyze|examine|study)",
            r"(?:visualize|plot|chart|graph)",
            r"(?:summarize|report|present)",
            r"(?:compare|contrast)",
        ],
        "research": [
            r"(?:search|find|look\s+up)",
            r"(?:summarize|synthesize)",
            r"(?:evaluate|assess)",
        ],
    }

    # Parallel indicators - these subtasks can often run concurrently
    PARALLEL_INDICATORS = [
        r"\band\b",
        r"\bwhile\b",
        r"\bat\s+the\s+same\s+time\b",
        r"\bsimultaneously\b",
        r"\bconcurrently\b",
    ]

    async def decompose(self, task: Task) -> DecompositionResult:
        """Decompose task using domain-aware patterns.

        Args:
            task: Task to decompose

        Returns:
            DecompositionResult with domain-aware subtasks
        """
        # Determine domain from capabilities
        domain = self._identify_domain(task.required_capabilities)

        # Extract subtasks using domain patterns
        subtasks = self._extract_domain_subtasks(task, domain)

        # Check for parallelization
        is_parallel = self._check_parallel_indicators(task.prompt)

        self._logger.debug(
            "Domain decomposition complete",
            task_id=task.task_id,
            domain=domain,
            num_subtasks=len(subtasks),
            is_parallel=is_parallel,
        )

        return DecompositionResult(
            original_task_id=task.task_id,
            strategy="domain",
            subtasks=subtasks,
            is_parallelizable=is_parallel,
            reasoning=f"Domain-aware decomposition for {domain} domain",
        )

    def _identify_domain(self, capabilities: list[str]) -> str:
        """Identify domain from capabilities.

        Args:
            capabilities: Required capabilities

        Returns:
            Domain name
        """
        cap_set = set(c.lower() for c in capabilities)

        if cap_set & {"code", "python", "javascript", "programming"}:
            return "code"
        if cap_set & {"analysis", "data", "visualization", "statistics"}:
            return "analysis"
        if cap_set & {"research", "search", "information"}:
            return "research"

        return "general"

    def _extract_domain_subtasks(
        self,
        task: Task,
        domain: str,
    ) -> list[SubTask]:
        """Extract subtasks using domain patterns.

        Args:
            task: Task to decompose
            domain: Identified domain

        Returns:
            List of domain-aware subtasks
        """
        patterns = self.DOMAIN_PATTERNS.get(domain, [])
        prompt_lower = task.prompt.lower()

        # Find matching patterns
        matches = []
        for pattern in patterns:
            for match in re.finditer(pattern, prompt_lower):
                matches.append((match.start(), match.group()))

        # If patterns found, extract corresponding parts
        if matches:
            matches.sort(key=lambda x: x[0])
            subtasks = []
            for i, (pos, match_text) in enumerate(matches, 1):
                # Extract context around the match
                content = self._extract_context(task.prompt, pos, match_text)
                subtask = SubTask(
                    content=content,
                    order=i,
                    parent_task_id=task.task_id,
                    required_capabilities=task.required_capabilities.copy(),
                )
                subtasks.append(subtask)

            # Deduplicate if needed
            seen = set()
            unique = []
            for s in subtasks:
                if s.content not in seen:
                    seen.add(s.content)
                    unique.append(s)

            if unique:
                return unique

        # Fall back to simple decomposition
        simple = SimpleDecomposer()
        result = self._run_sync(simple.decompose(task))
        return result.subtasks if result else [
            SubTask(
                content=task.prompt,
                order=1,
                parent_task_id=task.task_id,
                required_capabilities=task.required_capabilities.copy(),
            )
        ]

    def _extract_context(
        self,
        prompt: str,
        pos: int,
        match_text: str,
    ) -> str:
        """Extract context around a pattern match.

        Args:
            prompt: Full prompt
            pos: Match position
            match_text: Matched text

        Returns:
            Context string
        """
        # Find sentence containing the match
        sentences = re.split(r'(?<=[.!?])\s+', prompt)
        cumulative = 0
        for sentence in sentences:
            if cumulative <= pos < cumulative + len(sentence):
                return sentence.strip()
            cumulative += len(sentence) + 1

        # Fall back to match text
        return match_text

    def _check_parallel_indicators(self, prompt: str) -> bool:
        """Check if prompt indicates parallel execution.

        Args:
            prompt: Task prompt

        Returns:
            True if parallel execution indicated
        """
        for pattern in self.PARALLEL_INDICATORS:
            if re.search(pattern, prompt, re.IGNORECASE):
                return True
        return False

    def _run_sync(self, coro):
        """Run coroutine synchronously (for fallback).

        Args:
            coro: Coroutine to run

        Returns:
            Coroutine result
        """
        import asyncio

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Create new task in running loop
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(asyncio.run, coro)
                    return future.result()
            return loop.run_until_complete(coro)
        except RuntimeError:
            return asyncio.run(coro)


def create_decomposer(strategy: str, **kwargs) -> Decomposer:
    """Create a decomposer with the specified strategy.

    Args:
        strategy: Decomposition strategy (simple, recursive, domain)
        **kwargs: Additional arguments for the decomposer

    Returns:
        Configured decomposer instance

    Raises:
        ValueError: If strategy is unknown
    """
    if strategy == "simple":
        return SimpleDecomposer(**kwargs)
    elif strategy == "recursive":
        return RecursiveDecomposer(**kwargs)
    elif strategy == "domain":
        return DomainDecomposer(**kwargs)
    else:
        raise ValueError(f"Unknown decomposition strategy: {strategy}")
