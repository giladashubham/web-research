from __future__ import annotations

from webresearch.context import WorkflowContext
from webresearch.tools.providers.errors import SearchProviderError
from webresearch.tools.providers.mock import MockSearchProvider
from webresearch.tools.providers.search_provider import SearchResult
from webresearch.tools.search_web import search_web


def _context_with_fixtures(fixtures: dict[str, list[SearchResult]]) -> WorkflowContext:
    return WorkflowContext(search_provider=MockSearchProvider(fixtures))


async def test_tool_returns_provider_results_with_source_ids() -> None:
    ctx = _context_with_fixtures(
        {
            "alpha": [
                SearchResult(
                    url="https://example.com/a",
                    title="A",
                    snippet="Snippet A",
                    publisher="Example",
                )
            ]
        }
    )

    results = await search_web(ctx, "alpha")

    assert results.provider_id == "mock"
    assert results.results[0].source_id == "src_1"
    assert results.results[0].url == "https://example.com/a"
    assert ctx.sources.get("src_1") is not None


async def test_repeated_calls_overlapping_urls_reuse_source_ids() -> None:
    ctx = _context_with_fixtures(
        {
            "alpha": [SearchResult(url="https://example.com/a/", title="A", snippet="First")],
            "beta": [SearchResult(url="https://EXAMPLE.com/a", title="B", snippet="Second")],
        }
    )

    first = await search_web(ctx, "alpha")
    second = await search_web(ctx, "beta")

    assert first.results[0].source_id == "src_1"
    assert second.results[0].source_id == "src_1"
    assert len(ctx.sources.list()) == 1


async def test_provider_error_returns_empty_results_and_adds_warning() -> None:
    class FailingProvider:
        id = "failing"

        async def search(self, _query: str, limit: int = 10) -> list[SearchResult]:
            _ = limit
            raise SearchProviderError(500, "failed")

    ctx = WorkflowContext(search_provider=FailingProvider())

    results = await search_web(ctx, "alpha")

    assert results.results == []
    assert results.warning is not None
    assert ctx.warnings == [results.warning]
