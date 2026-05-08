from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict


class AgentOutputModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PlanOutput(AgentOutputModel):
    questions: list[str]
    risks: list[str]
    search_strategy: str


class ResearcherOutput(AgentOutputModel):
    summary: str
    source_ids: list[str]
    evidence_ids: list[str]
    confidence: Literal["high", "medium", "low"]


class Coverage(AgentOutputModel):
    topic: str
    status: Literal["covered", "partial", "missing"]
    notes: str


class Conflict(AgentOutputModel):
    claim: str
    source_ids: list[str]
    notes: str


class ReviewOutput(AgentOutputModel):
    coverage: list[Coverage]
    conflicts: list[Conflict]
    has_critical_gaps: bool
    follow_up_queries: list[str]


class GapResearchOutput(ResearcherOutput):
    pass


class ResearchFindingRef(AgentOutputModel):
    claim: str
    evidence_ids: list[str]
    source_ids: list[str]
    confidence: Literal["high", "medium", "low"]


class FinalAnswer(AgentOutputModel):
    answer_markdown: str
    findings: list[ResearchFindingRef]
    sources_cited: list[str]
    structured_data: dict[str, object] | None = None
