from __future__ import annotations

from pathlib import Path

from webresearch.context import FetchedPage, WorkflowContext
from webresearch.tools.extract_content import MAX_EXTRACTED_CHARS, extract_content
from webresearch.types import SourceInput


def _fixture(name: str) -> str:
    return Path("tests/fixtures/html", name).read_text()


async def test_extracts_main_content_from_article_fixture() -> None:
    url = "https://example.com/article"
    ctx = WorkflowContext()
    source = ctx.sources.add(SourceInput(url=url))
    ctx.pages[url] = FetchedPage(url=url, body=_fixture("article.html"), content_type="text/html")

    result = await extract_content(ctx, url)

    assert result.status == "extracted"
    assert result.source_id == source.id
    assert "central article text" in result.text
    assert result.artifact_id == "artifact_1"
    assert ctx.evidence[0].id == "ev_1"
    assert ctx.evidence[0].source_id == source.id
    assert "central article text" in ctx.evidence[0].note
    assert len(ctx.artifacts) == 1


async def test_skips_boilerplate_from_article_fixture() -> None:
    url = "https://example.com/article"
    ctx = WorkflowContext()
    ctx.sources.add(SourceInput(url=url))
    ctx.pages[url] = FetchedPage(url=url, body=_fixture("article.html"), content_type="text/html")

    result = await extract_content(ctx, url)

    assert "Subscribe Login Menu" not in result.text
    assert "Privacy policy" not in result.text


async def test_no_body_returns_failure_and_no_artifact() -> None:
    ctx = WorkflowContext()

    result = await extract_content(ctx, "https://example.com/missing")

    assert result.status == "failed"
    assert result.reason == "No fetched page body found"
    assert ctx.evidence == []
    assert ctx.artifacts == []


async def test_truncation_reported_when_content_exceeds_limit() -> None:
    url = "https://example.com/long"
    paragraph = " ".join(["evidence"] * 1200)
    html = f"<html><body><main><article><p>{paragraph}</p></article></main></body></html>"
    ctx = WorkflowContext()
    ctx.sources.add(SourceInput(url=url))
    ctx.pages[url] = FetchedPage(url=url, body=html, content_type="text/html")

    result = await extract_content(ctx, url)

    assert result.status == "extracted"
    assert result.truncated is True
    assert result.char_count == MAX_EXTRACTED_CHARS
