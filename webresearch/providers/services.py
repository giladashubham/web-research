from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from webresearch.providers.errors import SearchProviderError
from webresearch.providers.search import default_search_provider
from webresearch.types import SourceInput

if TYPE_CHECKING:
    from webresearch.context import WorkflowContext
    from webresearch.providers.search import SearchProvider
    from webresearch.types import SourceRecord

RECENCY_WEIGHT = 0.2
EVIDENCE_BONUS = 0.1


def domain_reliability_score(url: str) -> float:
    from urllib.parse import urlsplit

    MAJOR_NEWS_DOMAINS = {
        "apnews.com", "bbc.com", "nytimes.com", "reuters.com", "washingtonpost.com",
    }
    BLOG_HINTS = ("blog", "medium.com", "substack.com", "wordpress.com")

    host = (urlsplit(url).hostname or "").casefold()
    if host.endswith(".gov") or host.endswith(".edu"):
        return 1.0
    if _is_vendor_official(host, BLOG_HINTS):
        return 0.85
    if _is_major_news(host, MAJOR_NEWS_DOMAINS):
        return 0.75
    if any(hint in host for hint in BLOG_HINTS):
        return 0.25
    return 0.5


def _is_vendor_official(host: str, blog_hints: tuple[str, ...]) -> bool:
    return host.startswith(("www.", "docs.", "developer.")) and not any(
        hint in host for hint in blog_hints
    )


def _is_major_news(host: str, major_domains: set[str]) -> bool:
    return any(
        host == domain or host.endswith(f".{domain}") for domain in major_domains
    )


class SearchService:
    def __init__(self, provider: SearchProvider | None = None) -> None:
        self._provider = provider or default_search_provider()
        self._query_cache: dict[str, object] = {}

    async def search_web(
        self, ctx: WorkflowContext, query: str, limit: int = 10
    ) -> object:
        from pydantic import BaseModel, ConfigDict

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

        cache_key = query.strip().lower()
        if cache_key in self._query_cache:
            return self._query_cache[cache_key]

        try:
            provider_results = await self._provider.search(query, limit=limit)
        except SearchProviderError as exc:
            warning = f"Search provider {self._provider.id} failed: {exc}"
            ctx.warnings.append(warning)
            result = SearchResults(
                query=query, results=[], provider_id=self._provider.id, warning=warning
            )
            self._query_cache[cache_key] = result
            return result

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

        result = SearchResults(
            query=query, results=results, provider_id=self._provider.id
        )
        self._query_cache[cache_key] = result
        return result

    async def rank_sources(
        self,
        ctx: WorkflowContext,
        source_ids: list[str] | None = None,
        top_k: int = 10,
    ) -> object:
        from pydantic import BaseModel, ConfigDict

        class RankedSource(BaseModel):
            model_config = ConfigDict(extra="forbid")
            source_id: str
            url: str
            score: float

        class RankedSources(BaseModel):
            model_config = ConfigDict(extra="forbid")
            sources: list[RankedSource]

        sources = _selected_sources(ctx, source_ids)
        ranked = sorted(
            (
                RankedSource(source_id=s.id, url=s.url, score=_score_source(ctx, s))
                for s in sources
            ),
            key=lambda rs: rs.score,
            reverse=True,
        )
        return RankedSources(sources=ranked[:top_k])


def _selected_sources(
    ctx: WorkflowContext, source_ids: list[str] | None
) -> list[SourceRecord]:
    if source_ids is None:
        return list(ctx.sources.list())
    selected: list[SourceRecord] = []
    for source_id in source_ids:
        source = ctx.sources.get(source_id)
        if source is not None:
            selected.append(source)
    return selected


def _score_source(ctx: WorkflowContext, source: SourceRecord) -> float:
    score = domain_reliability_score(source.url)
    score += _recency_score(source) * RECENCY_WEIGHT
    if _has_evidence_artifact(ctx, source.id):
        score += EVIDENCE_BONUS
    return round(score, 6)


def _recency_score(source: SourceRecord) -> float:
    timestamp = source.published_at or source.accessed_at
    if timestamp is None:
        return 0
    now = datetime.now(UTC)
    age_days = max((now - timestamp).days, 0)
    return max(0.0, 1.0 - (age_days / 365.0))


def _has_evidence_artifact(ctx: WorkflowContext, source_id: str) -> bool:
    return any(evidence.source_id == source_id for evidence in ctx.evidence)
