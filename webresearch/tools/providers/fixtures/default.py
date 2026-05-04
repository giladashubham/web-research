from __future__ import annotations

from webresearch.tools.providers.search_provider import SearchResult

DEFAULT_SEARCH_FIXTURES: dict[str, list[SearchResult]] = {
    "research plan": [
        SearchResult(
            url="https://example.edu/research-methods",
            title="Research Methods Overview",
            snippet="A university guide to planning evidence-based research.",
            publisher="Example University",
        ),
        SearchResult(
            url="https://www.example.gov/data-sources",
            title="Public Data Sources",
            snippet="Government datasets and source evaluation guidance.",
            publisher="Example Gov",
        ),
    ],
    "web research": [
        SearchResult(
            url="https://example.com/web-research-guide",
            title="Web Research Guide",
            snippet="Practical techniques for finding and evaluating online sources.",
            publisher="Example",
        )
    ],
    "source reliability": [
        SearchResult(
            url="https://example.edu/source-reliability",
            title="Evaluating Source Reliability",
            snippet="Criteria for assessing source authority, freshness, and relevance.",
            publisher="Example University",
        )
    ],
}
