from __future__ import annotations

from agents import RunContextWrapper, function_tool

from webresearch.context import WorkflowContext  # noqa: TC001
from webresearch.tools.discover_urls import DiscoveredUrls, discover_urls
from webresearch.tools.fetch_and_extract import FetchAndExtractResult, fetch_and_extract
from webresearch.tools.rank_sources import RankedSources, rank_sources
from webresearch.tools.search_web import SearchResults, search_web


@function_tool
async def discover_urls_tool(
    ctx: RunContextWrapper[WorkflowContext],
    seed_url: str,
) -> DiscoveredUrls:
    """Expand a seed URL into categorised high-value pages on the site.

    Use this before search_web_tool. Fetches sitemap.xml, parses anchor links,
    follows high-value same-site docs/API subdomains one hop, and probes canonical
    paths (/docs, /changelog, /api, /pricing, /security, /customers, /blog,
    /careers). Returns zero Tavily calls.
    """
    return await discover_urls(ctx.context, seed_url)


@function_tool
async def search_web_tool(
    ctx: RunContextWrapper[WorkflowContext],
    query: str,
    limit: int = 10,
) -> SearchResults:
    """Search the web for sources relevant to the query."""
    return await search_web(ctx.context, query, limit)


@function_tool
async def fetch_and_extract_tool(
    ctx: RunContextWrapper[WorkflowContext],
    url: str,
    query: str | None = None,
) -> FetchAndExtractResult:
    """Fetch a URL and return its extracted text in one step.

    Prefer this over separate fetch+extract calls. Pass query to focus extraction
    on the most relevant content. Returns the full readable text, source_id for
    citation, and whether the content was truncated.
    """
    return await fetch_and_extract(ctx.context, url, query)


@function_tool
async def rank_sources_tool(
    ctx: RunContextWrapper[WorkflowContext],
    source_ids: list[str] | None = None,
    top_k: int = 10,
) -> RankedSources:
    """Rank registered sources by reliability, recency, and evidence coverage."""
    return await rank_sources(ctx.context, source_ids, top_k)


RESEARCH_TOOLS = [
    discover_urls_tool,
    search_web_tool,
    fetch_and_extract_tool,
    rank_sources_tool,
]
