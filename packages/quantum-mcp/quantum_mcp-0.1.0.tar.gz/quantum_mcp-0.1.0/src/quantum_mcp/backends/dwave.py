# Description: D-Wave Leap backend implementation.
# Description: Wraps DWaveSampler with EmbeddingComposite for QUBO solving.
"""D-Wave quantum annealing backend."""

from __future__ import annotations

import asyncio
import os
from typing import TYPE_CHECKING, Any, Optional

import structlog

from quantum_mcp.backends.annealing import AnnealingResult, AnnealingSample
from quantum_mcp.backends.protocol import (
    BackendCapabilities,
    BackendParadigm,
    BackendStatus,
    BaseQuantumBackend,
)

if TYPE_CHECKING:
    pass

logger = structlog.get_logger()


class DWaveBackend(BaseQuantumBackend):
    """D-Wave quantum annealing backend.

    Provides access to D-Wave quantum annealers via the Ocean SDK.
    Supports QUBO and BQM problem formats.
    """

    def __init__(
        self,
        token: Optional[str] = None,
        solver: str = "Advantage_system6.4",
        use_embedding: bool = True,
    ) -> None:
        """Initialize D-Wave backend.

        Args:
            token: D-Wave API token (uses DWAVE_API_TOKEN env var if not provided)
            solver: D-Wave solver name
            use_embedding: Whether to use automatic embedding (recommended)
        """
        super().__init__()
        self._token = token or os.environ.get("DWAVE_API_TOKEN")
        self._solver_name = solver
        self._use_embedding = use_embedding
        self._sampler: Any = None
        self._logger = logger.bind(backend="DWave", solver=solver)

    @property
    def backend_id(self) -> str:
        """Unique identifier for this backend."""
        return f"dwave.{self._solver_name}"

    @property
    def capabilities(self) -> BackendCapabilities:
        """Backend capabilities."""
        return BackendCapabilities(
            paradigm=BackendParadigm.ANNEALING,
            max_qubits=5000,  # Advantage system
            supports_async=True,
            is_simulator=False,
            provider="dwave",
            native_operations=["qubo", "bqm", "cqm"],
        )

    async def connect(self) -> None:
        """Connect to D-Wave via Ocean SDK.

        Raises:
            ImportError: If dwave-ocean-sdk is not installed
            RuntimeError: If connection fails
        """
        if self._connected:
            return

        try:
            from dwave.system import DWaveSampler, EmbeddingComposite
        except ImportError as e:
            raise ImportError(
                "dwave-ocean-sdk required for D-Wave backend. "
                "Install with: uv sync --extra dwave"
            ) from e

        self._logger.info("Connecting to D-Wave", solver=self._solver_name)

        try:
            loop = asyncio.get_event_loop()

            def _create_sampler() -> Any:
                base_sampler = DWaveSampler(
                    solver=self._solver_name,
                    token=self._token,
                )
                if self._use_embedding:
                    return EmbeddingComposite(base_sampler)
                return base_sampler

            self._sampler = await loop.run_in_executor(None, _create_sampler)
            self._connected = True
            self._logger.info("Connected to D-Wave")

        except Exception as e:
            self._logger.error("Failed to connect to D-Wave", error=str(e))
            raise RuntimeError(f"D-Wave connection failed: {e}") from e

    async def disconnect(self) -> None:
        """Disconnect from D-Wave."""
        if self._sampler is not None:
            self._sampler = None
        self._connected = False
        self._logger.debug("Disconnected from D-Wave")

    async def health_check(self) -> BackendStatus:
        """Check D-Wave availability."""
        if not self._connected or self._sampler is None:
            return BackendStatus.UNAVAILABLE

        try:
            # Quick check by accessing sampler properties
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: self._sampler.properties)
            return BackendStatus.AVAILABLE
        except Exception:
            return BackendStatus.DEGRADED

    async def solve_qubo(
        self,
        Q: dict[tuple[int, int], float],
        num_reads: int = 100,
        **kwargs: object,
    ) -> AnnealingResult:
        """Solve QUBO problem on D-Wave hardware.

        Args:
            Q: QUBO matrix as dict {(i, j): weight}
            num_reads: Number of annealing runs
            **kwargs: Additional D-Wave parameters (annealing_time, etc.)

        Returns:
            AnnealingResult with samples

        Raises:
            RuntimeError: If not connected
        """
        if not self._connected or self._sampler is None:
            raise RuntimeError("Not connected to D-Wave. Call connect() first.")

        if not Q:
            return AnnealingResult(
                samples=[AnnealingSample(bitstring={}, energy=0.0)],
                timing_info={},
                metadata={"solver": self._solver_name},
            )

        self._logger.debug(
            "Submitting QUBO to D-Wave",
            num_terms=len(Q),
            num_reads=num_reads,
        )

        loop = asyncio.get_event_loop()

        def _sample() -> Any:
            return self._sampler.sample_qubo(Q, num_reads=num_reads, **kwargs)

        try:
            sampleset = await loop.run_in_executor(None, _sample)
            return self._parse_sampleset(sampleset)

        except Exception as e:
            self._logger.error("D-Wave solve failed", error=str(e))
            raise RuntimeError(f"D-Wave solve failed: {e}") from e

    async def solve_bqm(
        self,
        linear: dict[int, float],
        quadratic: dict[tuple[int, int], float],
        offset: float = 0.0,
        num_reads: int = 100,
        **kwargs: object,
    ) -> AnnealingResult:
        """Solve BQM problem on D-Wave hardware.

        Args:
            linear: Linear biases {variable: bias}
            quadratic: Quadratic biases {(i, j): bias}
            offset: Constant energy offset
            num_reads: Number of annealing runs
            **kwargs: Additional D-Wave parameters

        Returns:
            AnnealingResult with samples

        Raises:
            RuntimeError: If not connected
            ImportError: If dimod not available
        """
        if not self._connected or self._sampler is None:
            raise RuntimeError("Not connected to D-Wave. Call connect() first.")

        try:
            from dimod import BinaryQuadraticModel
        except ImportError as e:
            raise ImportError(
                "dimod required for BQM support. "
                "Install with: uv sync --extra dwave"
            ) from e

        bqm = BinaryQuadraticModel(linear, quadratic, offset, vartype="BINARY")

        self._logger.debug(
            "Submitting BQM to D-Wave",
            num_variables=len(bqm.variables),
            num_reads=num_reads,
        )

        loop = asyncio.get_event_loop()

        def _sample() -> Any:
            return self._sampler.sample(bqm, num_reads=num_reads, **kwargs)

        try:
            sampleset = await loop.run_in_executor(None, _sample)
            return self._parse_sampleset(sampleset)

        except Exception as e:
            self._logger.error("D-Wave BQM solve failed", error=str(e))
            raise RuntimeError(f"D-Wave solve failed: {e}") from e

    def _parse_sampleset(self, sampleset: Any) -> AnnealingResult:
        """Convert D-Wave SampleSet to AnnealingResult.

        Args:
            sampleset: D-Wave SampleSet object

        Returns:
            AnnealingResult with parsed samples
        """
        samples = []

        for sample, energy, num_occ in sampleset.data(
            ["sample", "energy", "num_occurrences"]
        ):
            # Convert sample to dict[int, int]
            bitstring = {int(k): int(v) for k, v in dict(sample).items()}
            samples.append(
                AnnealingSample(
                    bitstring=bitstring,
                    energy=float(energy),
                    num_occurrences=int(num_occ),
                )
            )

        # Sort by energy
        samples.sort(key=lambda s: s.energy)

        # Extract timing info
        timing = {}
        info = getattr(sampleset, "info", {})
        if "timing" in info:
            timing = {k: float(v) for k, v in info["timing"].items()}

        return AnnealingResult(
            samples=samples,
            timing_info=timing,
            metadata={
                "solver": self._solver_name,
                "num_reads": sampleset.record.num_occurrences.sum(),
            },
        )
