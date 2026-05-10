from __future__ import annotations

import pytest
import respx
from httpx import Response

from webresearch.providers.search import (
    BrightDataSearchProvider,
    TavilySearchProvider,
    default_search_provider,
)


@pytest.mark.asyncio
@respx.mock
async def test_brightdata_search_success() -> None:
    provider = BrightDataSearchProvider(api_key="test_key", zone="test_zone")

    mock_response = {
        "organic": [
            {
                "link": "https://example.com",
                "title": "Example",
                "description": "Snippet text",
            }
        ]
    }

    respx.post("https://api.brightdata.com/request").mock(
        return_value=Response(200, json=mock_response)
    )

    results = await provider.search("test query", limit=1)

    assert len(results) == 1
    assert results[0].url == "https://example.com"
    assert results[0].title == "Example"
    assert results[0].snippet == "Snippet text"


@pytest.mark.asyncio
@respx.mock
async def test_brightdata_search_respects_limit() -> None:
    provider = BrightDataSearchProvider(api_key="test_key", zone="test_zone")

    mock_response = {
        "organic": [
            {"link": "https://e1.com", "title": "T1", "description": "D1"},
            {"link": "https://e2.com", "title": "T2", "description": "D2"},
        ]
    }

    respx.post("https://api.brightdata.com/request").mock(
        return_value=Response(200, json=mock_response)
    )

    results = await provider.search("test", limit=1)
    assert len(results) == 1
    assert results[0].url == "https://e1.com"


def test_default_search_provider_selection(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WEBRESEARCH_SEARCH_PROVIDER", "brightdata")
    monkeypatch.setenv("BRIGHTDATA_API_KEY", "key")
    monkeypatch.setenv("BRIGHTDATA_ZONE", "zone")

    provider = default_search_provider()
    assert provider.id == "brightdata"
    assert isinstance(provider, BrightDataSearchProvider)


def test_default_search_provider_tavily_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("WEBRESEARCH_SEARCH_PROVIDER", raising=False)
    monkeypatch.setenv("TAVILY_API_KEY", "test_key")

    provider = default_search_provider()
    assert provider.id == "tavily"
    assert isinstance(provider, TavilySearchProvider)


def test_default_search_provider_missing_creds(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WEBRESEARCH_SEARCH_PROVIDER", "brightdata")
    monkeypatch.delenv("BRIGHTDATA_API_KEY", raising=False)

    with pytest.raises(ValueError, match="BRIGHTDATA_API_KEY and BRIGHTDATA_ZONE are required"):
        default_search_provider()


def test_default_search_provider_fallback_to_mock(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("WEBRESEARCH_SEARCH_PROVIDER", raising=False)
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)

    provider = default_search_provider()
    assert provider.id == "mock"


def test_default_search_provider_unknown(monkeypatch: pytest.MonkeyPatch) -> None:

    monkeypatch.setenv("WEBRESEARCH_SEARCH_PROVIDER", "unsupported")

    with pytest.raises(ValueError, match="Unknown search provider: unsupported"):
        default_search_provider()
