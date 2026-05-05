from __future__ import annotations

from typing import Literal

from pydantic import Field, HttpUrl

from webresearch.types import WebResearchModel


class DiligenceTarget(WebResearchModel):
    company_name: str = Field(min_length=1)
    product_name: str | None = None
    product_url: HttpUrl | None = None
    known_urls: list[HttpUrl] = Field(default_factory=list)
    known_competitors: list[str] = Field(default_factory=list)
    evaluation_prompt: str = Field(min_length=1)


class ExecutiveJudgment(WebResearchModel):
    technical_substance: Literal["real_asset", "mixed", "thin", "unclear"]
    confidence: Literal["low", "medium", "high"]
    summary: str = Field(min_length=1)
    key_risks: list[str] = Field(default_factory=list)
    key_strengths: list[str] = Field(default_factory=list)


class ClaimAssessment(WebResearchModel):
    claim: str = Field(min_length=1)
    claim_source_urls: list[HttpUrl] = Field(default_factory=list)
    public_evidence: str = Field(min_length=1)
    evidence_source_urls: list[HttpUrl] = Field(default_factory=list)
    assessment: Literal["supported", "partially_supported", "unsupported", "unclear"]
    confidence: Literal["low", "medium", "high"]
    code_review_follow_up_ids: list[str] = Field(default_factory=list)


class TechnicalSubstanceAssessment(WebResearchModel):
    product_depth: Literal["deep", "moderate", "thin", "unclear"]
    proprietary_architecture: Literal["clear", "partial", "commodity", "unclear"]
    wrapper_risk: Literal["low", "medium", "high", "unclear"]
    evidence: list[str] = Field(default_factory=list)
    reasoning: str = Field(min_length=1)


class CompetitorAssessment(WebResearchModel):
    competitor_name: str = Field(min_length=1)
    competitor_url: HttpUrl | None = None
    similar_capabilities: list[str] = Field(default_factory=list)
    differentiation_notes: str = Field(min_length=1)
    source_urls: list[HttpUrl] = Field(default_factory=list)


class ReplicabilityAssessment(WebResearchModel):
    estimated_replication_time: Literal[
        "under_3_months",
        "3_to_6_months",
        "6_to_12_months",
        "over_12_months",
        "unclear",
    ]
    competitor_replication_risk: Literal["low", "medium", "high", "unclear"]
    drivers: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)


class CodeReviewFollowUp(WebResearchModel):
    id: str = Field(min_length=1)
    area: str = Field(min_length=1)
    question: str = Field(min_length=1)
    expected_evidence: list[str] = Field(default_factory=list)
    priority: Literal["low", "medium", "high"]


class TechnicalDueDiligenceReport(WebResearchModel):
    target: DiligenceTarget
    executive_judgment: ExecutiveJudgment
    claims: list[ClaimAssessment] = Field(default_factory=list)
    technical_substance: TechnicalSubstanceAssessment
    competitors: list[CompetitorAssessment] = Field(default_factory=list)
    replicability: ReplicabilityAssessment
    code_review_follow_ups: list[CodeReviewFollowUp] = Field(default_factory=list)
    evidence_gaps: list[str] = Field(default_factory=list)
    source_urls: list[HttpUrl] = Field(default_factory=list)


class IntakePlan(WebResearchModel):
    target: DiligenceTarget
    research_questions: list[str] = Field(default_factory=list)
    likely_claim_areas: list[str] = Field(default_factory=list)
    competitor_names: list[str] = Field(default_factory=list)
    priority_urls: list[HttpUrl] = Field(default_factory=list)


class ExtractedClaim(WebResearchModel):
    claim: str = Field(min_length=1)
    source_urls: list[HttpUrl] = Field(default_factory=list)
    category: Literal["product", "architecture", "ai_ml", "integration", "customer", "other"]
    diligence_relevance: Literal["low", "medium", "high"]


class ClaimExtraction(WebResearchModel):
    claims: list[ExtractedClaim] = Field(default_factory=list)
    unknowns: list[str] = Field(default_factory=list)


class EvidenceResearch(WebResearchModel):
    claim_assessments: list[ClaimAssessment] = Field(default_factory=list)
    evidence_gaps: list[str] = Field(default_factory=list)
    source_urls: list[HttpUrl] = Field(default_factory=list)


class CompetitorMapping(WebResearchModel):
    competitors: list[CompetitorAssessment] = Field(default_factory=list)
    comparison_summary: str = Field(min_length=1)


class TechnicalSubstanceReview(WebResearchModel):
    executive_judgment: ExecutiveJudgment
    technical_substance: TechnicalSubstanceAssessment
    replicability: ReplicabilityAssessment
    code_review_follow_ups: list[CodeReviewFollowUp] = Field(default_factory=list)
    has_critical_gaps: bool = False
    follow_up_queries: list[str] = Field(default_factory=list)


class DiligenceGapResearch(WebResearchModel):
    summary: str = Field(min_length=1)
    additional_claim_assessments: list[ClaimAssessment] = Field(default_factory=list)
    additional_evidence_gaps: list[str] = Field(default_factory=list)
    source_urls: list[HttpUrl] = Field(default_factory=list)


class DiligenceFinding(WebResearchModel):
    claim: str = Field(min_length=1)
    evidence_ids: list[str] = Field(default_factory=list)
    source_ids: list[str] = Field(default_factory=list)
    confidence: Literal["low", "medium", "high"]


class FinalMemoOutput(WebResearchModel):
    answer_markdown: str = Field(min_length=1)
    report: TechnicalDueDiligenceReport
    findings: list[DiligenceFinding] = Field(default_factory=list)
