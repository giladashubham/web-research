from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field

from webresearch.providers.discover import UrlsByCategory
from webresearch.types import WebResearchModel

UrlString = Annotated[str, Field(min_length=1)]


class DiligenceTarget(WebResearchModel):
    company_name: str = Field(min_length=1)
    product_name: str | None = None
    product_url: UrlString | None = None
    known_urls: list[UrlString] = Field(default_factory=list)
    known_competitors: list[str] = Field(default_factory=list)
    evaluation_prompt: str = Field(min_length=1)


class ChangelogObservations(WebResearchModel):
    source_urls: list[UrlString] = Field(default_factory=list)
    last_release_date: str | None = None
    releases_last_12_months: int | None = None
    notable_releases: list[str] = Field(default_factory=list)
    cadence_description: str | None = None


class CategorizedGap(WebResearchModel):
    claim_id: str = Field(min_length=1)
    gap_type: Literal["documentation_gap", "depth_gap", "private_diligence_needed"]
    description: str = Field(min_length=1)


class ClaimAssessment(WebResearchModel):
    claim_id: str | None = None
    claim: str = Field(min_length=1)
    claim_source_urls: list[UrlString] = Field(default_factory=list)
    public_evidence: str = Field(min_length=1)
    evidence_source_urls: list[UrlString] = Field(default_factory=list)
    assessment: Literal[
        "supported", "partially_supported", "unsupported", "unclear", "contradicted"
    ]
    confidence: Literal["low", "medium", "high"]
    code_review_follow_up_ids: list[str] = Field(default_factory=list)


class CodeReviewFollowUp(WebResearchModel):
    id: str = Field(min_length=1)
    area: str = Field(min_length=1)
    question: str = Field(min_length=1)
    expected_evidence: list[str] = Field(default_factory=list)
    priority: Literal["low", "medium", "high"]


class TechnicalDueDiligenceReport(WebResearchModel):
    target: DiligenceTarget
    claims: list[ClaimAssessment] = Field(default_factory=list)
    release_activity: ChangelogObservations | None = None
    code_review_follow_ups: list[CodeReviewFollowUp] = Field(default_factory=list)
    evidence_gaps: list[str] = Field(default_factory=list)
    source_urls: list[UrlString] = Field(default_factory=list)


class IntakePlan(WebResearchModel):
    target: DiligenceTarget
    research_questions: list[str] = Field(default_factory=list)
    likely_claim_areas: list[str] = Field(default_factory=list)
    claim_source_urls: list[UrlString] = Field(default_factory=list)
    evidence_urls_by_category: UrlsByCategory = Field(default_factory=UrlsByCategory)


class SelectedPriorityUrls(WebResearchModel):
    evidence_urls_by_category: UrlsByCategory = Field(default_factory=UrlsByCategory)
    selection_rationale: list[str] = Field(default_factory=list)
    rejected_patterns: list[str] = Field(default_factory=list)


class ExtractedClaim(WebResearchModel):
    id: str = Field(min_length=1)
    claim: str = Field(min_length=1)
    source_urls: list[UrlString] = Field(default_factory=list)
    category: Literal["product", "architecture", "ai_ml", "integration", "customer", "other"]
    diligence_relevance: Literal["low", "medium", "high"]


class ClaimExtraction(WebResearchModel):
    claims: list[ExtractedClaim] = Field(default_factory=list)
    unknowns: list[str] = Field(default_factory=list)


class EvidenceResearch(WebResearchModel):
    claim_assessments: list[ClaimAssessment] = Field(default_factory=list)
    evidence_gaps: list[CategorizedGap] = Field(default_factory=list)
    source_urls: list[UrlString] = Field(default_factory=list)
    release_activity: ChangelogObservations | None = None


class UnresolvedClaim(WebResearchModel):
    claim_id: str = Field(min_length=1)
    claim_text: str = Field(min_length=1)
    reason_unresolved: str = Field(min_length=1)
    artefact_types_to_chase: list[
        Literal[
            "docs",
            "changelog",
            "api",
            "pricing",
            "security",
            "customers",
            "blog",
            "careers",
        ]
    ] = Field(default_factory=list)
    follow_up_queries: list[str] = Field(default_factory=list)


class TechnicalSubstanceReview(WebResearchModel):
    code_review_follow_ups: list[CodeReviewFollowUp] = Field(default_factory=list)
    unresolved_claims: list[UnresolvedClaim] = Field(default_factory=list)


class DiligenceGapResearch(WebResearchModel):
    summary: str = Field(min_length=1)
    additional_claim_assessments: list[ClaimAssessment] = Field(default_factory=list)
    additional_evidence_gaps: list[CategorizedGap] = Field(default_factory=list)
    source_urls: list[UrlString] = Field(default_factory=list)


class DiligenceFinding(WebResearchModel):
    claim: str = Field(min_length=1)
    evidence_ids: list[str] = Field(default_factory=list)
    source_ids: list[str] = Field(default_factory=list)
    confidence: Literal["low", "medium", "high"]


class FinalMemoOutput(WebResearchModel):
    answer_markdown: str = Field(min_length=1)
    report: TechnicalDueDiligenceReport
    findings: list[DiligenceFinding] = Field(default_factory=list)
