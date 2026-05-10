from __future__ import annotations

from typing import Literal

from pydantic import Field

from webresearch.types import WebResearchModel


class IntakePlan(WebResearchModel):
    company_name: str = Field(min_length=1)
    company_url: str = Field(min_length=1)
    period_days: int = Field(ge=1)
    period_start_date: str = Field(min_length=1)
    period_end_date: str = Field(min_length=1)
    search_focus: list[str] = Field(default_factory=list)


class RawNewsItem(WebResearchModel):
    title: str = Field(min_length=1)
    date: str | None = None
    summary: str = Field(min_length=1)
    url: str = Field(min_length=1)
    source_id: str | None = None
    signal_type: str = Field(min_length=1)


class ResearcherOutput(WebResearchModel):
    items: list[RawNewsItem] = Field(default_factory=list)
    queries_used: list[str] = Field(default_factory=list)
    summary: str = ""


class NewsItem(WebResearchModel):
    title: str = Field(min_length=1)
    date: str | None = None
    category: Literal[
        "leadership", "funding", "product_pricing", "partnerships_ma", "other"
    ]
    summary: str = Field(min_length=1)
    url: str = Field(min_length=1)
    source_id: str | None = None
    source_name: str = Field(min_length=1)
    signal_type: str = Field(min_length=1)


class CompanyNewsReport(WebResearchModel):
    company_name: str = Field(min_length=1)
    company_url: str = Field(min_length=1)
    period_days: int = Field(ge=1)
    period_start: str = Field(min_length=1)
    period_end: str = Field(min_length=1)
    total_items: int = Field(ge=0)
    items: list[NewsItem] = Field(default_factory=list)


class NewsFinding(WebResearchModel):
    claim: str = Field(min_length=1)
    evidence_ids: list[str] = Field(default_factory=list)
    confidence: Literal["low", "medium", "high"]


class OutputWriterOutput(WebResearchModel):
    answer_markdown: str = Field(min_length=1)
    report: CompanyNewsReport
    findings: list[NewsFinding] = Field(default_factory=list)
