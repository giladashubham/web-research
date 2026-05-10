from __future__ import annotations

import pytest

from webresearch.providers.search import MockSearchProvider, SearchResult


async def test_mock_search_provider_returns_empty() -> None:
    provider = MockSearchProvider()
    results = await provider.search("test query", limit=10)
    assert results == []


async def test_mock_search_provider_ignores_params() -> None:
    provider = MockSearchProvider()
    results = await provider.search("anything", limit=100)
    assert isinstance(results, list)
    assert len(results) == 0


def test_search_result_model() -> None:
    result = SearchResult(
        url="https://example.com",
        title="Example",
        snippet="An example site",
        publisher="Example Corp",
    )
    assert result.url == "https://example.com"
    assert result.title == "Example"
    assert result.publisher == "Example Corp"
    assert result.published_at is None


def test_search_result_extra_forbidden() -> None:
    with pytest.raises(ValueError):
        SearchResult(  # type: ignore[call-arg]
            url="https://example.com",
            title="Test",
            snippet="test",
            extra_field="should_fail",
        )
