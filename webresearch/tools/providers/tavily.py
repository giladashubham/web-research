from __future__ import annotations

import os

import httpx

from webresearch.tools.providers.errors import SearchProviderError
from webresearch.tools.providers.search_provider import SearchResult

TAVILY_SEARCH_URL = "https://api.tavily.com/search"
BODY_EXCERPT_LENGTH = 500


class TavilySearchProvider:
    id = "tavily"

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key if api_key is not None else os.getenv("TAVILY_API_KEY")

    async def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        payload = {
            "api_key": self._api_key,
            "query": query,
            "max_results": limit,
            "search_depth": "basic",
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(TAVILY_SEARCH_URL, json=payload)

        if response.is_error:
            raise SearchProviderError(response.status_code, response.text[:BODY_EXCERPT_LENGTH])

        data = response.json()
        results = data.get("results", [])
        if not isinstance(results, list):
            return []

        return [_map_result(result) for result in results if isinstance(result, dict)]


def _map_result(result: dict[object, object]) -> SearchResult:
    return SearchResult.model_validate(
        {
            "url": str(result.get("url", "")),
            "title": str(result.get("title", "")),
            "snippet": str(result.get("content") or result.get("snippet") or ""),
            "publisher": _optional_str(result.get("publisher")),
            "published_at": result.get("published_at"),
        }
    )


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    return str(value)
