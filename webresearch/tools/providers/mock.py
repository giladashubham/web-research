from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from webresearch.tools.providers.fixtures.default import DEFAULT_SEARCH_FIXTURES

if TYPE_CHECKING:
    from webresearch.tools.providers.search_provider import SearchResult


class MockSearchProvider:
    id = "mock"

    def __init__(self, fixtures: dict[str, list[SearchResult]] | None = None) -> None:
        self._fixtures = fixtures if fixtures is not None else DEFAULT_SEARCH_FIXTURES

    async def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        await asyncio.sleep(0.01)
        results = self._match(query)
        return [result.model_copy(deep=True) for result in results[:limit]]

    def _match(self, query: str) -> list[SearchResult]:
        if query in self._fixtures:
            return self._fixtures[query]

        normalized_query = query.casefold()
        for fixture_query, results in self._fixtures.items():
            normalized_fixture_query = fixture_query.casefold()
            query_matches_fixture = normalized_query in normalized_fixture_query
            fixture_matches_query = normalized_fixture_query in normalized_query
            if query_matches_fixture or fixture_matches_query:
                return results

        return []
