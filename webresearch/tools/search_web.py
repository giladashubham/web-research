from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from webresearch.tools.providers.errors import SearchProviderError
from webresearch.types import SourceInput

if TYPE_CHECKING:
    from webresearch.context import WorkflowContext


class SearchWebResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str
    url: str
    title: str
    snippet: str
    publisher: str | None = None


class SearchResults(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str
    results: list[SearchWebResult]
    provider_id: str
    warning: str | None = None


# TODO(P3-01): decorate with openai-agents `@function_tool` once the SDK is installed.
async def search_web(ctx: WorkflowContext, query: str, limit: int = 10) -> SearchResults:
    try:
        provider_results = await ctx.search_provider.search(query, limit=limit)
    except SearchProviderError as exc:
        warning = f"Search provider {ctx.search_provider.id} failed: {exc}"
        ctx.warnings.append(warning)
        return SearchResults(
            query=query,
            results=[],
            provider_id=ctx.search_provider.id,
            warning=warning,
        )

    results: list[SearchWebResult] = []
    for provider_result in provider_results:
        source = ctx.sources.add(
            SourceInput(
                url=provider_result.url,
                title=provider_result.title,
                snippet=provider_result.snippet,
                publisher=provider_result.publisher,
                published_at=provider_result.published_at,
            )
        )
        results.append(
            SearchWebResult(
                source_id=source.id,
                url=source.url,
                title=provider_result.title,
                snippet=provider_result.snippet,
                publisher=provider_result.publisher,
            )
        )

    return SearchResults(query=query, results=results, provider_id=ctx.search_provider.id)
