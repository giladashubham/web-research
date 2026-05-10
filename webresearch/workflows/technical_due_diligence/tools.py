from __future__ import annotations

from webresearch.pipeline import ToolContext, function_tool
from webresearch.providers.discover import UrlDiscoverProvider
from webresearch.providers.extract import ExtractProvider
from webresearch.providers.fetch import FetchProvider
from webresearch.providers.services import SearchService

_fetch_provider = FetchProvider()
_extract_provider = ExtractProvider()
_discover_provider = UrlDiscoverProvider()
_search_service = SearchService()


@function_tool
async def search_web_tool(
    ctx: ToolContext,
    query: str,
    limit: int = 10,
) -> object:
    """Search the web for technical evidence. Prefer official docs, changelogs, security advisories."""
    return await _search_service.search_web(ctx.context, query, limit)


@function_tool
async def fetch_and_extract_tool(
    ctx: ToolContext,
    url: str,
    query: str | None = None,
) -> object:
    """
    Fetch a URL and return extracted text. Pass the specific claim being investigated
    as query to focus extraction on the most relevant content.
    """
    fetch_result = await _fetch_provider.fetch(ctx.context, url)
    if fetch_result.status != "fetched":
        return {
            "url": fetch_result.url,
            "status": fetch_result.status,
            "reason": fetch_result.reason,
        }
    extract_result = await _extract_provider.extract(
        ctx.context, fetch_result.url, query
    )
    return {
        "url": fetch_result.url,
        "status": extract_result.status,
        "text": extract_result.text,
        "char_count": extract_result.char_count,
        "truncated": extract_result.truncated,
        "reason": extract_result.reason,
        "source_id": fetch_result.source_id,
        "artifact_id": extract_result.artifact_id,
    }


@function_tool
async def discover_urls_tool(
    ctx: ToolContext,
    seed_url: str,
) -> object:
    """
    Discover high-value URLs from a domain: docs, API reference, changelog, security pages.
    Use this on the target company's primary domain before searching.
    """
    return await _discover_provider.discover(ctx.context, seed_url)


RESEARCH_TOOLS = [discover_urls_tool, search_web_tool, fetch_and_extract_tool]
