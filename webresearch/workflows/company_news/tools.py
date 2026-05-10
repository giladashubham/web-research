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
async def search_news_tool(
    ctx: ToolContext,
    query: str,
    limit: int = 15,
) -> object:
    """Search the web for company news. Use site: operators for social media, e.g. site:twitter.com or site:linkedin.com."""
    return await _search_service.search_web(ctx.context, query, limit)


@function_tool
async def fetch_and_extract_tool(
    ctx: ToolContext,
    url: str,
    query: str | None = None,
) -> object:
    """Fetch a URL and return extracted text. Pass the topic being researched as query to focus extraction."""
    fetch_result = await _fetch_provider.fetch(ctx.context, url)
    if fetch_result.status != "fetched":
        return {
            "url": fetch_result.url,
            "status": fetch_result.status,
            "reason": fetch_result.reason,
        }
    extract_result = await _extract_provider.extract(ctx.context, fetch_result.url, query)
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
async def discover_company_pages_tool(
    ctx: ToolContext,
    seed_url: str,
) -> object:
    """Discover pages on a company's domain: blog, newsroom, press releases, changelog."""
    return await _discover_provider.discover(ctx.context, seed_url)


NEWS_TOOLS = [search_news_tool, fetch_and_extract_tool]
COMPANY_TOOLS = [discover_company_pages_tool, search_news_tool, fetch_and_extract_tool]
