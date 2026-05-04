from __future__ import annotations

from agents import RunContextWrapper, function_tool

from webresearch.context import WorkflowContext  # noqa: TC001
from webresearch.tools.extract_content import ExtractResult, extract_content
from webresearch.tools.fetch_url import FetchResult, fetch_url
from webresearch.tools.rank_sources import RankedSources, rank_sources
from webresearch.tools.search_web import SearchResults, search_web


@function_tool
async def search_web_tool(
    ctx: RunContextWrapper[WorkflowContext],
    query: str,
    limit: int = 10,
) -> SearchResults:
    """Search the web for sources relevant to the query."""
    return await search_web(ctx.context, query, limit)


@function_tool
async def fetch_url_tool(ctx: RunContextWrapper[WorkflowContext], url: str) -> FetchResult:
    """Fetch a URL and store the page body for extraction."""
    return await fetch_url(ctx.context, url)


@function_tool
async def extract_content_tool(
    ctx: RunContextWrapper[WorkflowContext],
    url: str,
    query: str | None = None,
) -> ExtractResult:
    """Extract readable text from a fetched page."""
    return await extract_content(ctx.context, url, query)


@function_tool
async def rank_sources_tool(
    ctx: RunContextWrapper[WorkflowContext],
    source_ids: list[str] | None = None,
    top_k: int = 10,
) -> RankedSources:
    """Rank registered sources by reliability, recency, and evidence coverage."""
    return await rank_sources(ctx.context, source_ids, top_k)


RESEARCH_TOOLS = [
    search_web_tool,
    fetch_url_tool,
    extract_content_tool,
    rank_sources_tool,
]
