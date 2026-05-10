from __future__ import annotations

import os
from typing import Protocol
from urllib.parse import quote

import httpx
from pydantic import AwareDatetime, BaseModel, ConfigDict

from webresearch.providers.errors import SearchProviderError


class SearchResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    url: str
    title: str
    snippet: str
    publisher: str | None = None
    published_at: AwareDatetime | None = None


class SearchProvider(Protocol):
    id: str

    async def search(self, query: str, limit: int = 10) -> list[SearchResult]: ...


TAVILY_SEARCH_URL = "https://api.tavily.com/search"
BRIGHTDATA_SEARCH_URL = "https://api.brightdata.com/request"
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


class BrightDataSearchProvider:
    id = "brightdata"

    def __init__(self, api_key: str | None = None, zone: str | None = None) -> None:
        self._api_key = api_key if api_key is not None else os.getenv("BRIGHTDATA_API_KEY")
        self._zone = zone if zone is not None else os.getenv("BRIGHTDATA_ZONE")

    async def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        # Build Google search URL (could be parameterized later)
        search_url = f"https://www.google.com/search?q={quote(query)}&hl=en&gl=us&num={limit}"

        payload = {
            "zone": self._zone,
            "url": search_url,
            "format": "raw",
            "data_format": "parsed_light",
        }
        headers = {"Authorization": f"Bearer {self._api_key}"}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                BRIGHTDATA_SEARCH_URL, json=payload, headers=headers, timeout=30.0
            )

        if response.is_error:
            raise SearchProviderError(response.status_code, response.text[:BODY_EXCERPT_LENGTH])

        data = response.json()
        results = data.get("organic", [])
        if not isinstance(results, list):
            return []

        # Parsed light returns up to 10 results, we might need to slice if limit is less
        return [_map_result(result) for result in results[:limit] if isinstance(result, dict)]


class MockSearchProvider:
    id = "mock"

    async def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        _ = (query, limit)
        return []


def default_search_provider() -> SearchProvider:
    provider_id = os.getenv("WEBRESEARCH_SEARCH_PROVIDER", "tavily").lower()

    if provider_id == "tavily":
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            raise ValueError("TAVILY_API_KEY is required for Tavily provider")
        return TavilySearchProvider(api_key=api_key)

    if provider_id == "brightdata":
        api_key = os.getenv("BRIGHTDATA_API_KEY")
        zone = os.getenv("BRIGHTDATA_ZONE")
        if not api_key or not zone:
            raise ValueError(
                "BRIGHTDATA_API_KEY and BRIGHTDATA_ZONE are required for BrightData provider"
            )
        return BrightDataSearchProvider(api_key=api_key, zone=zone)

    if provider_id == "mock":
        return MockSearchProvider()

    raise ValueError(f"Unknown search provider: {provider_id}")


def _map_result(result: dict[object, object]) -> SearchResult:
    return SearchResult.model_validate(
        {
            "url": str(result.get("url") or result.get("link") or ""),
            "title": str(result.get("title", "")),
            "snippet": str(
                result.get("content") or result.get("snippet") or result.get("description") or ""
            ),
            "publisher": _optional_str(result.get("publisher")),
            "published_at": result.get("published_at"),
        }
    )


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    return str(value)
