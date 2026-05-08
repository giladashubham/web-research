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
    sources: SourceRegistry = field(default_factory=SourceRegistry)
    pages: dict[str, FetchedPage] = field(default_factory=dict)
    evidence: list[EvidenceNote] = field(default_factory=list)
    artifacts: list[Artifact] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    cost_usd: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
