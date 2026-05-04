from __future__ import annotations

import asyncio

import httpx
import pytest
import respx

from webresearch.tools.providers.errors import SearchProviderError
from webresearch.tools.providers.tavily import TAVILY_SEARCH_URL, TavilySearchProvider


@respx.mock
async def test_successful_response_maps_to_search_results() -> None:
    route = respx.post(TAVILY_SEARCH_URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "url": "https://example.com/a",
                        "title": "A",
                        "content": "Snippet A",
                        "publisher": "Example",
                    }
                ]
            },
        )
    )
    provider = TavilySearchProvider(api_key="test-key")

    results = await provider.search("alpha", limit=3)

    assert route.called
    request = route.calls.last.request
    assert request is not None
    assert b'"max_results":3' in request.content
    assert results[0].url == "https://example.com/a"
    assert results[0].snippet == "Snippet A"


@respx.mock
async def test_http_error_raises_search_provider_error() -> None:
    respx.post(TAVILY_SEARCH_URL).mock(return_value=httpx.Response(500, text="upstream failed"))
    provider = TavilySearchProvider(api_key="test-key")

    with pytest.raises(SearchProviderError) as exc_info:
        await provider.search("alpha")

    assert exc_info.value.status == 500
    assert exc_info.value.body_excerpt == "upstream failed"


async def test_task_cancellation_terminates_in_flight_request() -> None:
    async def slow_handler(_: httpx.Request) -> httpx.Response:
        await asyncio.sleep(10)
        return httpx.Response(200, json={"results": []})

    async with respx.mock:
        respx.post(TAVILY_SEARCH_URL).mock(side_effect=slow_handler)
        provider = TavilySearchProvider(api_key="test-key")
        task = asyncio.create_task(provider.search("alpha"))

        await asyncio.sleep(0)
        task.cancel()

        with pytest.raises(asyncio.CancelledError):
            await task
