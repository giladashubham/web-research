from __future__ import annotations

import httpx
import respx

from webresearch.context import WorkflowContext
from webresearch.tools.fetch_url import BODY_SIZE_LIMIT_BYTES, USER_AGENT, fetch_url
from webresearch.types import FetchStatus, SourceInput


@respx.mock
async def test_successful_fetch_records_body_and_content_type() -> None:
    route = respx.get("https://example.com/article").mock(
        return_value=httpx.Response(200, html="<html><body>Article</body></html>")
    )
    ctx = WorkflowContext()

    result = await fetch_url(ctx, "https://example.com/article")

    assert route.calls.last.request.headers["user-agent"] == USER_AGENT
    assert result.status == "fetched"
    assert ctx.pages["https://example.com/article"].body == "<html><body>Article</body></html>"
    assert ctx.pages["https://example.com/article"].content_type == "text/html"
    assert ctx.sources.get(result.source_id or "").fetch_status == FetchStatus.FETCHED


@respx.mock
async def test_http_error_marks_failed_and_adds_warning() -> None:
    respx.get("https://example.com/missing").mock(return_value=httpx.Response(404, text="missing"))
    ctx = WorkflowContext()

    result = await fetch_url(ctx, "https://example.com/missing")

    assert result.status == "failed"
    assert ctx.sources.get(result.source_id or "").fetch_status == FetchStatus.FAILED
    assert ctx.warnings


@respx.mock
async def test_disallowed_content_type_marks_blocked_and_adds_warning() -> None:
    source_url = "https://example.com/file.pdf"
    respx.get(source_url).mock(
        return_value=httpx.Response(
            200,
            content=b"%PDF",
            headers={"content-type": "application/pdf"},
        )
    )
    ctx = WorkflowContext()
    source = ctx.sources.add(SourceInput(url=source_url))

    result = await fetch_url(ctx, source_url)

    assert result.status == "blocked"
    assert ctx.sources.get(source.id).fetch_status == FetchStatus.BLOCKED
    assert source_url not in ctx.pages
    assert ctx.warnings


@respx.mock
async def test_body_over_size_limit_is_truncated_with_warning() -> None:
    source_url = "https://example.com/large"
    body = b"a" * (BODY_SIZE_LIMIT_BYTES + 1)
    respx.get(source_url).mock(
        return_value=httpx.Response(200, content=body, headers={"content-type": "text/plain"})
    )
    ctx = WorkflowContext()

    result = await fetch_url(ctx, source_url)

    assert result.status == "fetched"
    assert result.truncated is True
    assert result.byte_size == BODY_SIZE_LIMIT_BYTES
    assert len(ctx.pages[source_url].body) == BODY_SIZE_LIMIT_BYTES
    assert ctx.warnings
