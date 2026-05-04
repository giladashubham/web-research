from __future__ import annotations

from datetime import UTC, datetime

from webresearch.context import WorkflowContext
from webresearch.tools.rank_sources import rank_sources
from webresearch.types import EvidenceArtifact, SourceInput


async def test_gov_and_edu_sources_outrank_blogs_by_default() -> None:
    ctx = WorkflowContext()
    blog = ctx.sources.add(SourceInput(url="https://personalblog.example.com/post"))
    gov = ctx.sources.add(SourceInput(url="https://agency.gov/report"))
    edu = ctx.sources.add(SourceInput(url="https://example.edu/study"))

    result = await rank_sources(ctx)

    ranked_ids = [source.source_id for source in result.sources]
    assert ranked_ids.index(gov.id) < ranked_ids.index(blog.id)
    assert ranked_ids.index(edu.id) < ranked_ids.index(blog.id)


async def test_more_recent_sources_outrank_older_sources_all_else_equal() -> None:
    ctx = WorkflowContext()
    older = ctx.sources.add(
        SourceInput(
            url="https://example.com/older",
            published_at=datetime(2020, 1, 1, tzinfo=UTC),
        )
    )
    newer = ctx.sources.add(
        SourceInput(
            url="https://example.com/newer",
            published_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
    )

    result = await rank_sources(ctx)

    ranked_ids = [source.source_id for source in result.sources]
    assert ranked_ids.index(newer.id) < ranked_ids.index(older.id)


async def test_top_k_caps_output() -> None:
    ctx = WorkflowContext()
    ctx.sources.add(SourceInput(url="https://one.example.com"))
    ctx.sources.add(SourceInput(url="https://two.example.com"))
    ctx.sources.add(SourceInput(url="https://three.example.com"))

    result = await rank_sources(ctx, top_k=2)

    assert len(result.sources) == 2


async def test_empty_source_list_returns_empty_result() -> None:
    ctx = WorkflowContext()

    result = await rank_sources(ctx)

    assert result.sources == []


async def test_evidence_artifact_boosts_source_score() -> None:
    ctx = WorkflowContext()
    without_evidence = ctx.sources.add(SourceInput(url="https://example.com/a"))
    with_evidence = ctx.sources.add(SourceInput(url="https://example.com/b"))
    ctx.artifacts.append(
        EvidenceArtifact(
            id="artifact_1",
            title="Evidence",
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
            evidence_ids=[with_evidence.id],
        )
    )

    result = await rank_sources(ctx, source_ids=[without_evidence.id, with_evidence.id])

    assert result.sources[0].source_id == with_evidence.id
