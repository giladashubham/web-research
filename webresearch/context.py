"""Runtime state container for workflow execution.

:class:`WorkflowContext` accumulates pages, sources, evidence, artifacts,
warnings, and token/cost counters during a pipeline run.  It is owned by the
pipeline engine and passed to providers and tools as a shared mutable bag.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from webresearch.sources.registry import SourceRegistry

if TYPE_CHECKING:
    from webresearch.types import Artifact, EvidenceNote


@dataclass
class FetchedPage:
    url: str
    body: str
    content_type: str
    truncated: bool = False


@dataclass
class WorkflowContext:
    """Mutable bag of runtime state shared across all steps in a pipeline run.

    Accumulates fetched pages, registered sources, collected evidence,
    generated artifacts, warnings, and cumulative token/cost counters.
    """

    sources: SourceRegistry = field(default_factory=SourceRegistry)
    pages: dict[str, FetchedPage] = field(default_factory=dict)
    evidence: list[EvidenceNote] = field(default_factory=list)
    artifacts: list[Artifact] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    cost_usd: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    _max_sources: int | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        if self._max_sources is not None:
            self.sources._max_sources = self._max_sources
