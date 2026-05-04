from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from webresearch.tools.heuristics.domain_reliability import domain_reliability_score
from webresearch.types import EvidenceArtifact, SourceRecord

if TYPE_CHECKING:
    from webresearch.context import WorkflowContext

RECENCY_WEIGHT = 0.2
EVIDENCE_BONUS = 0.1


class RankedSource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str
    url: str
    score: float


class RankedSources(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sources: list[RankedSource]


# TODO(P3-01): decorate with openai-agents `@function_tool` once the SDK is installed.
async def rank_sources(
    ctx: WorkflowContext,
    source_ids: list[str] | None = None,
    top_k: int = 10,
) -> RankedSources:
    sources = _selected_sources(ctx, source_ids)
    ranked_sources = (
        RankedSource(source_id=source.id, url=source.url, score=_score_source(ctx, source))
        for source in sources
    )
    ranked = sorted(
        ranked_sources,
        key=lambda source: source.score,
        reverse=True,
    )
    return RankedSources(sources=ranked[:top_k])


def _selected_sources(ctx: WorkflowContext, source_ids: list[str] | None) -> list[SourceRecord]:
    if source_ids is None:
        return list(ctx.sources.list())
    selected: list[SourceRecord] = []
    for source_id in source_ids:
        source = ctx.sources.get(source_id)
        if source is not None:
            selected.append(source)
    return selected


def _score_source(ctx: WorkflowContext, source: SourceRecord) -> float:
    score = domain_reliability_score(source.url)
    score += _recency_score(source) * RECENCY_WEIGHT
    if _has_evidence_artifact(ctx, source.id):
        score += EVIDENCE_BONUS
    return round(score, 6)


def _recency_score(source: SourceRecord) -> float:
    timestamp = source.published_at or source.accessed_at
    if timestamp is None:
        return 0
    now = datetime.now(UTC)
    age_days = max((now - timestamp).days, 0)
    return max(0.0, 1.0 - (age_days / 365.0))


def _has_evidence_artifact(ctx: WorkflowContext, source_id: str) -> bool:
    return any(
        isinstance(artifact, EvidenceArtifact) and source_id in artifact.evidence_ids
        for artifact in ctx.artifacts
    )
