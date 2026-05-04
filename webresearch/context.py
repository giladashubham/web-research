from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from webresearch.sources.registry import SourceRegistry
from webresearch.tools.providers.mock import MockSearchProvider
from webresearch.tools.providers.tavily import TavilySearchProvider

if TYPE_CHECKING:
    from webresearch.tools.providers.search_provider import SearchProvider
    from webresearch.types import Artifact, EvidenceNote


@dataclass
class FetchedPage:
    url: str
    body: str
    content_type: str
    truncated: bool = False


def default_search_provider() -> SearchProvider:
    if os.getenv("TAVILY_API_KEY"):
        return TavilySearchProvider()
    return MockSearchProvider()


@dataclass
class WorkflowContext:
    search_provider: SearchProvider = field(default_factory=default_search_provider)
    sources: SourceRegistry = field(default_factory=SourceRegistry)
    pages: dict[str, FetchedPage] = field(default_factory=dict)
    evidence: list[EvidenceNote] = field(default_factory=list)
    artifacts: list[Artifact] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
