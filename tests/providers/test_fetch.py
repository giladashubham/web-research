from __future__ import annotations

from unittest.mock import AsyncMock

from webresearch.context import FetchedPage, WorkflowContext
from webresearch.providers.fetch import FetchProvider
from webresearch.types import FetchStatus, SourceInput


async def test_fetch_returns_cached_page() -> None:
    ctx = WorkflowContext()
    ctx.pages["https://example.com"] = FetchedPage(
        url="https://example.com",
        body="<html>cached</html>",
        content_type="text/html",
    )
    ctx.sources.add(SourceInput(url="https://example.com"))

    provider = FetchProvider()
    result = await provider.fetch(ctx, "https://example.com")

    assert result.status == "fetched"
    assert result.source_id is not None


async def test_fetch_creates_source_for_new_url(monkeypatch) -> None:
    ctx = WorkflowContext()

    async def mock_get(self, url: str, **kwargs: object) -> object:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "text/html"}
        mock_response.content = b"<html>new page</html>"
        mock_response.encoding = "utf-8"
        mock_response.is_error = False
        return mock_response

    monkeypatch.setattr("httpx.AsyncClient.get", mock_get)

    provider = FetchProvider()
    result = await provider.fetch(ctx, "https://example.com/new-page")

    assert result.status == "fetched"
    assert result.url == "https://example.com/new-page"


async def test_fetch_blocks_disallowed_content_type(monkeypatch) -> None:
    ctx = WorkflowContext()

    async def mock_get(self, url: str, **kwargs: object) -> object:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/octet-stream"}
        mock_response.content = b"binary data"
        mock_response.encoding = "utf-8"
        mock_response.is_error = False
        return mock_response

    monkeypatch.setattr("httpx.AsyncClient.get", mock_get)

    provider = FetchProvider()
    result = await provider.fetch(ctx, "https://example.com/binary")

    assert result.status == "blocked"
    assert "blocked" in (result.reason or "").lower()


async def test_fetch_fails_on_http_error(monkeypatch) -> None:
    ctx = WorkflowContext()

    async def mock_get(self, url: str, **kwargs: object) -> object:
        mock_response = AsyncMock()
        mock_response.status_code = 404
        mock_response.headers = {"content-type": "text/html"}
        mock_response.content = b"not found"
        mock_response.encoding = "utf-8"
        mock_response.is_error = True
        return mock_response

    monkeypatch.setattr("httpx.AsyncClient.get", mock_get)

    provider = FetchProvider()
    result = await provider.fetch(ctx, "https://example.com/not-found")

    assert result.status == "failed"
    assert "404" in (result.reason or "")


async def test_fetch_truncates_large_body(monkeypatch) -> None:
    ctx = WorkflowContext()

    async def mock_get(self, url: str, **kwargs: object) -> object:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "text/html"}
        mock_response.content = b"x" * (6 * 1024 * 1024)  # 6MB
        mock_response.encoding = "utf-8"
        mock_response.is_error = False
        return mock_response

    monkeypatch.setattr("httpx.AsyncClient.get", mock_get)

    provider = FetchProvider(body_limit_bytes=1024)  # very small limit
    result = await provider.fetch(ctx, "https://example.com/large")

    assert result.status == "fetched"
    assert result.truncated is True


async def test_fetch_normalizes_url(monkeypatch) -> None:
    ctx = WorkflowContext()

    async def mock_get(self, url: str, **kwargs: object) -> object:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "text/html"}
        mock_response.content = b"<html>ok</html>"
        mock_response.encoding = "utf-8"
        mock_response.is_error = False
        return mock_response

    monkeypatch.setattr("httpx.AsyncClient.get", mock_get)

    provider = FetchProvider()
    # URL with trailing slash and tracking params
    result = await provider.fetch(
        ctx, "https://Example.COM/Page/?utm_source=test&fbclid=abc"
    )

    assert result.status == "fetched"
    assert result.url == "https://example.com/Page"


async def test_fetch_marks_source_status(monkeypatch) -> None:
    ctx = WorkflowContext()
    ctx.sources.add(SourceInput(url="https://example.com/status-test"))

    async def mock_get(self, url: str, **kwargs: object) -> object:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "text/html"}
        mock_response.content = b"<html>status test</html>"
        mock_response.encoding = "utf-8"
        mock_response.is_error = False
        return mock_response

    monkeypatch.setattr("httpx.AsyncClient.get", mock_get)

    provider = FetchProvider()
    result = await provider.fetch(ctx, "https://example.com/status-test")

    assert result.status == "fetched"
    source = ctx.sources.get_by_url("https://example.com/status-test")
    assert source is not None
    assert source.fetch_status == FetchStatus.FETCHED
