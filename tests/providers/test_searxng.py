from __future__ import annotations

import pytest
import respx
from httpx import Response

from webresearch.providers.errors import SearchProviderError
from webresearch.providers.search import (
    SearXNGSearchProvider,
    default_search_provider,
)


@pytest.mark.asyncio
@respx.mock
async def test_searxng_search_success() -> None:
    provider = SearXNGSearchProvider(base_url="http://localhost:8080")

    mock_response = {
        "results": [
            {
                "url": "https://example.com",
                "title": "Example Title",
                "content": "Example content snippet.",
                "engine": "google",
                "publishedDate": "2024-01-15T00:00:00Z",
            }
        ]
    }

    respx.get("http://localhost:8080/search").mock(return_value=Response(200, json=mock_response))

    results = await provider.search("test query", limit=5)

    assert len(results) == 1
    assert results[0].url == "https://example.com"
    assert results[0].title == "Example Title"
    assert results[0].snippet == "Example content snippet."
    assert results[0].publisher == "google"
    assert results[0].published_at is not None


@pytest.mark.asyncio
@respx.mock
async def test_searxng_search_respects_limit() -> None:
    provider = SearXNGSearchProvider(base_url="http://localhost:8080")

    mock_response = {
        "results": [
            {"url": "https://a.com", "title": "A", "content": "D1"},
            {"url": "https://b.com", "title": "B", "content": "D2"},
            {"url": "https://c.com", "title": "C", "content": "D3"},
        ]
    }

    respx.get("http://localhost:8080/search").mock(return_value=Response(200, json=mock_response))

    results = await provider.search("test", limit=2)
    assert len(results) == 2


@pytest.mark.asyncio
@respx.mock
async def test_searxng_search_with_secret() -> None:
    provider = SearXNGSearchProvider(base_url="http://localhost:8080", secret="my-secret")  # noqa: S106

    respx.get("http://localhost:8080/search", params={"secret": "my-secret"}).mock(
        return_value=Response(200, json={"results": []})
    )

    results = await provider.search("test", limit=5)
    assert results == []


@pytest.mark.asyncio
@respx.mock
async def test_searxng_search_empty_results() -> None:
    provider = SearXNGSearchProvider(base_url="http://localhost:8080")

    respx.get("http://localhost:8080/search").mock(return_value=Response(200, json={"results": []}))

    results = await provider.search("no results", limit=5)
    assert results == []


@pytest.mark.asyncio
@respx.mock
async def test_searxng_search_missing_results_key() -> None:
    provider = SearXNGSearchProvider(base_url="http://localhost:8080")

    respx.get("http://localhost:8080/search").mock(return_value=Response(200, json={}))

    results = await provider.search("test", limit=5)
    assert results == []


@pytest.mark.asyncio
@respx.mock
async def test_searxng_search_error_response() -> None:
    provider = SearXNGSearchProvider(base_url="http://localhost:8080")

    respx.get("http://localhost:8080/search").mock(
        return_value=Response(500, text="Internal error")
    )

    with pytest.raises(SearchProviderError) as exc_info:
        await provider.search("test", limit=5)
    assert exc_info.value.status == 500


@pytest.mark.asyncio
@respx.mock
async def test_searxng_snippet_fallback_order() -> None:
    """SearXNG puts the snippet in 'content', fallback to 'snippet' or 'description'."""
    provider = SearXNGSearchProvider(base_url="http://localhost:8080")

    mock_response = {
        "results": [{"url": "https://x.com", "title": "T", "snippet": "fallback snippet"}]
    }

    respx.get("http://localhost:8080/search").mock(return_value=Response(200, json=mock_response))

    results = await provider.search("test", limit=5)
    assert results[0].snippet == "fallback snippet"


def test_default_search_provider_searxng(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WEBRESEARCH_SEARCH_PROVIDER", "searxng")
    monkeypatch.setenv("SEARXNG_URL", "http://localhost:9999")

    provider = default_search_provider()
    assert provider.id == "searxng"
    assert isinstance(provider, SearXNGSearchProvider)
