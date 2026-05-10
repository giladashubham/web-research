from __future__ import annotations

from collections.abc import Awaitable, Callable
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

# Shared type alias for all workflow entry points.
WorkflowFn = Callable[["WorkflowInput"], Awaitable["WorkflowResult"]]


class WebResearchModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DepthPreset(StrEnum):
    QUICK = "quick"
    STANDARD = "standard"
    DEEP = "deep"


class ToolBudgets(WebResearchModel):
    search_queries: int = Field(ge=0)
    fetch_urls: int = Field(ge=0)
    extract_pages: int = Field(ge=0)


class Depth(WebResearchModel):
    preset: DepthPreset
    max_rounds: int = Field(ge=0)
    max_sources: int = Field(ge=1)
    tool_budgets: ToolBudgets

    @classmethod
    def for_preset(cls, name: str) -> Depth:
        presets = {
            DepthPreset.QUICK: cls(
                preset=DepthPreset.QUICK,
                max_rounds=0,
                max_sources=5,
                tool_budgets=ToolBudgets(search_queries=2, fetch_urls=5, extract_pages=5),
            ),
            DepthPreset.STANDARD: cls(
                preset=DepthPreset.STANDARD,
                max_rounds=1,
                max_sources=10,
                tool_budgets=ToolBudgets(search_queries=5, fetch_urls=10, extract_pages=10),
            ),
            DepthPreset.DEEP: cls(
                preset=DepthPreset.DEEP,
                max_rounds=3,
                max_sources=20,
                tool_budgets=ToolBudgets(search_queries=10, fetch_urls=25, extract_pages=25),
            ),
        }
        return presets[DepthPreset(name)]


class WorkflowInput(WebResearchModel):
    query: str = Field(min_length=1)
    instructions: str | None = None
    depth: Depth = Field(default_factory=lambda: Depth.for_preset("standard"))
    max_sources: int | None = Field(default=None, ge=1)
    output_schema: dict[str, object] | None = None


class TokenUsage(WebResearchModel):
    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)


class WorkflowMetadata(WebResearchModel):
    run_id: str
    workflow_id: str
    started_at: AwareDatetime
    finished_at: AwareDatetime | None = None
    cost_usd: float | None = Field(default=None, ge=0)
    tokens: TokenUsage = Field(default_factory=TokenUsage)


class FetchStatus(StrEnum):
    PENDING = "pending"
    FETCHED = "fetched"
    FAILED = "failed"
    BLOCKED = "blocked"


class SourceInput(WebResearchModel):
    url: str
    title: str | None = None
    snippet: str | None = None
    publisher: str | None = None
    published_at: AwareDatetime | None = None
    accessed_at: AwareDatetime | None = None
    is_primary: bool = False


class SourceRecord(WebResearchModel):
    id: str
    url: str
    title: str | None = None
    snippet: str | None = None
    publisher: str | None = None
    published_at: AwareDatetime | None = None
    accessed_at: AwareDatetime | None = None
    is_primary: bool = False
    fetch_status: FetchStatus | None = None


class EvidenceNote(WebResearchModel):
    id: str
    source_id: str
    quote: str | None = None
    note: str
    relevance: str | None = None


class ResearchFinding(WebResearchModel):
    id: str
    claim: str
    evidence_ids: list[str] = Field(default_factory=list)
    confidence: float | None = Field(default=None, ge=0, le=1)


class Artifact(WebResearchModel):
    id: str
    title: str
    created_at: AwareDatetime


class PlanArtifact(Artifact):
    kind: Literal["plan"] = "plan"
    steps: list[str]


class SourceArtifact(Artifact):
    kind: Literal["source"] = "source"
    source_ids: list[str]


class EvidenceArtifact(Artifact):
    kind: Literal["evidence"] = "evidence"
    evidence_ids: list[str]


class ReviewArtifact(Artifact):
    kind: Literal["review"] = "review"
    reviewer_notes: list[str]
    has_critical_gaps: bool = False


class AnswerArtifact(Artifact):
    kind: Literal["answer"] = "answer"
    answer_markdown: str


class WarningArtifact(Artifact):
    kind: Literal["warning"] = "warning"
    message: str


WorkflowArtifact = Annotated[
    PlanArtifact
    | SourceArtifact
    | EvidenceArtifact
    | ReviewArtifact
    | AnswerArtifact
    | WarningArtifact,
    Field(discriminator="kind"),
]


class WorkflowResult(WebResearchModel):
    answer_markdown: str
    structured_data: dict[str, object] | None = None
    summary: str
    findings: list[ResearchFinding] = Field(default_factory=list)
    sources: list[SourceRecord] = Field(default_factory=list)
    evidence: list[EvidenceNote] = Field(default_factory=list)
    artifacts: list[WorkflowArtifact] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    metadata: WorkflowMetadata
