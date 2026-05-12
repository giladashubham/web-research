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
SEARXNG_DEFAULT_URL = "http://localhost:8080"
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


class SearXNGSearchProvider:
    id = "searxng"

    def __init__(
        self,
        base_url: str | None = None,
        secret: str | None = None,
    ) -> None:
        self._base_url = (
            base_url.rstrip("/")
            if base_url
            else os.getenv("SEARXNG_URL", SEARXNG_DEFAULT_URL).rstrip("/")
        )
        self._secret = secret if secret is not None else os.getenv("SEARXNG_SECRET")
        self._client: httpx.AsyncClient | None = None

    async def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        params: dict[str, object] = {
            "q": query,
            "format": "json",
            "categories": "general",
            "pageno": 1,
        }
        if self._secret:
            params["secret"] = self._secret

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self._base_url}/search",
                params=params,  # type: ignore[arg-type]
                timeout=15.0,
            )

        if response.is_error:
            raise SearchProviderError(response.status_code, response.text[:BODY_EXCERPT_LENGTH])

        data = response.json()
        results = data.get("results", [])
        if not isinstance(results, list):
            return []

        return [_searxng_map_result(r) for r in results[:limit] if isinstance(r, dict)]


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
    raw_provider_id = os.getenv("WEBRESEARCH_SEARCH_PROVIDER")
    provider_id = (raw_provider_id or "tavily").lower()

    if provider_id == "tavily":
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            if raw_provider_id:
                raise ValueError("TAVILY_API_KEY is required for Tavily provider")
            return MockSearchProvider()
        return TavilySearchProvider(api_key=api_key)

    if provider_id == "brightdata":
        api_key = os.getenv("BRIGHTDATA_API_KEY")
        zone = os.getenv("BRIGHTDATA_ZONE")
        if not api_key or not zone:
            if raw_provider_id:
                raise ValueError(
                    "BRIGHTDATA_API_KEY and BRIGHTDATA_ZONE are required for BrightData provider"
                )
            return MockSearchProvider()
        return BrightDataSearchProvider(api_key=api_key, zone=zone)

    if provider_id == "searxng":
        base_url = os.getenv("SEARXNG_URL", SEARXNG_DEFAULT_URL)
        secret = os.getenv("SEARXNG_SECRET")
        if raw_provider_id and not base_url:
            raise ValueError("SEARXNG_URL is required for SearXNG provider")
        return SearXNGSearchProvider(base_url=base_url, secret=secret)

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


def _searxng_map_result(result: dict[object, object]) -> SearchResult:
    return SearchResult.model_validate(
        {
            "url": str(result.get("url", "")),
            "title": str(result.get("title", "")),
            "snippet": str(
                result.get("content") or result.get("snippet") or result.get("description") or ""
            ),
            "publisher": _optional_str(result.get("engine")),
            "published_at": result.get("publishedDate"),
        }
    )


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    return str(value)
