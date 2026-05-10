from __future__ import annotations

from webresearch.context import FetchedPage, WorkflowContext
from webresearch.providers.extract import ExtractProvider
from webresearch.types import SourceInput


async def test_extract_fails_on_missing_page() -> None:
    ctx = WorkflowContext()
    provider = ExtractProvider()
    result = await provider.extract(ctx, "https://example.com/missing")

    assert result.status == "failed"
    assert "No fetched page body" in (result.reason or "")


async def test_extract_returns_text() -> None:
    ctx = WorkflowContext()
    ctx.sources.add(SourceInput(url="https://example.com/article"))
    ctx.pages["https://example.com/article"] = FetchedPage(
        url="https://example.com/article",
        body="<html><body><article><h1>Title</h1><p>Content here</p></article></body></html>",
        content_type="text/html",
    )

    provider = ExtractProvider()
    result = await provider.extract(ctx, "https://example.com/article")

    assert result.status == "extracted"
    assert len(result.text) > 0
    assert result.char_count > 0
    assert result.source_id is not None
    assert result.artifact_id is not None


async def test_extract_truncates_long_text() -> None:
    ctx = WorkflowContext()
    long_body = "<html><body>" + "p" * 10_000 + "</body></html>"
    ctx.pages["https://example.com/long"] = FetchedPage(
        url="https://example.com/long",
        body=long_body,
        content_type="text/html",
    )

    provider = ExtractProvider(max_chars=100)
    result = await provider.extract(ctx, "https://example.com/long")

    assert result.status == "extracted"
    assert result.truncated is True
    assert result.char_count <= 100


async def test_extract_adds_evidence_and_artifact() -> None:
    ctx = WorkflowContext()
    ctx.pages["https://example.com/evidence"] = FetchedPage(
        url="https://example.com/evidence",
        body="<html><body>Important evidence content</body></html>",
        content_type="text/html",
    )

    provider = ExtractProvider()
    result = await provider.extract(ctx, "https://example.com/evidence", query="test relevance")

    assert result.status == "extracted"
    assert len(ctx.evidence) == 1
    assert ctx.evidence[0].relevance == "test relevance"
    assert len(ctx.artifacts) == 1
    assert ctx.artifacts[0].evidence_ids == [ctx.evidence[0].id]


async def test_extract_fails_on_empty_extraction() -> None:
    ctx = WorkflowContext()
    ctx.pages["https://example.com/empty"] = FetchedPage(
        url="https://example.com/empty",
        body="<html><body><script>no text content</script></body></html>",
        content_type="text/html",
    )

    provider = ExtractProvider()
    result = await provider.extract(ctx, "https://example.com/empty")

    assert result.status == "failed"
