from __future__ import annotations

from webresearch.tools.providers.fixtures.default import DEFAULT_SEARCH_FIXTURES
from webresearch.tools.providers.mock import MockSearchProvider
from webresearch.tools.providers.search_provider import SearchResult


async def test_same_query_returns_identical_results_across_runs() -> None:
    provider = MockSearchProvider(
        {
            "alpha": [
                SearchResult(url="https://example.com/a", title="A", snippet="First result"),
            ]
        }
    )

    first = await provider.search("alpha")
    second = await provider.search("alpha")

    assert first == second
    assert first is not second


async def test_substring_fallback_when_no_exact_key_matches() -> None:
    provider = MockSearchProvider(
        {
            "source reliability": [
                SearchResult(
                    url="https://example.edu/reliability",
                    title="Reliability",
                    snippet="How to evaluate sources.",
                ),
            ]
        }
    )

    results = await provider.search("latest source reliability research")

    assert [result.url for result in results] == ["https://example.edu/reliability"]


def test_default_fixtures_load_without_errors() -> None:
    provider = MockSearchProvider()

    assert DEFAULT_SEARCH_FIXTURES
    assert provider.id == "mock"
