from __future__ import annotations

import json
from datetime import UTC, datetime
from importlib.resources import files
from typing import TYPE_CHECKING, cast
from urllib.parse import urlparse
from uuid import uuid4

from agents import Agent, Runner
from jsonschema import ValidationError as JsonSchemaValidationError
from jsonschema import validate
from pydantic import BaseModel

from webresearch.agents.settings import model_from_env, no_store_model_settings
from webresearch.agents.tools import RESEARCH_TOOLS
from webresearch.context import WorkflowContext
from webresearch.events.step import (
    current_run_id,
    emit_loop_iteration,
    emit_output_text_delta,
    step,
)
from webresearch.sources.url_normalize import normalize_url
from webresearch.types import (
    ResearchFinding,
    UrlsByCategory,
    WorkflowMetadata,
    WorkflowResult,
)
from webresearch.workflows.shared.prompt_loader import load_workflow_prompt
from webresearch.workflows.technical_due_diligence.models import (
    ClaimExtraction,
    CompetitorMapping,
    DiligenceGapResearch,
    EvidenceResearch,
    FinalMemoOutput,
    IntakePlan,
    SelectedPriorityUrls,
    TechnicalDueDiligenceReport,
    TechnicalSubstanceReview,
)

if TYPE_CHECKING:
    from webresearch.types import WorkflowInput

WORKFLOW_ID = "technical_due_diligence"
# For non-quick depths, enforce a minimum so a real investigation has room to run.
_MIN_MAX_ROUNDS = 5
# Research stages fetch many pages in parallel batches; 10 (SDK default) is too low.
_RESEARCH_MAX_TURNS = 50
_URL_SELECTOR_MODEL_ENV = "WEBRESEARCH_URL_SELECTOR_MODEL"
_URL_SELECTOR_DEFAULT_MODEL = "gpt-4.1-mini"
_URL_CATEGORIES = (
    "docs",
    "api",
    "changelog",
    "pricing",
    "security",
    "customers",
    "blog",
    "careers",
    "other",
)
_URL_SELECTION_BUDGETS = {
    "docs": 8,
    "api": 5,
    "changelog": 5,
    "pricing": 3,
    "security": 4,
    "customers": 3,
    "blog": 3,
    "careers": 2,
    "other": 4,
}
_MIN_COVERAGE_CATEGORIES = ("docs", "api", "changelog", "security")


async def run_technical_due_diligence(input: WorkflowInput) -> WorkflowResult:
    ctx = WorkflowContext()
    run_id = current_run_id()
    started_at = datetime.now(UTC)
    # Preserve quick=0 (no gap rounds). For standard/deep, bump to at least 5.
    effective_max_rounds = (
        max(input.depth.max_rounds, _MIN_MAX_ROUNDS) if input.depth.max_rounds > 0 else 0
    )

    async with step("intake_planner"):
        plan_result = await Runner.run(
            intake_planner_agent(), _input_prompt(input), context=ctx, max_turns=_RESEARCH_MAX_TURNS
        )
        plan = cast("IntakePlan", plan_result.final_output)

    plan = await _run_url_selector(input, ctx, plan)

    async with step("claim_extractor"):
        claims_result = await Runner.run(
            claim_extractor_agent(),
            _stage_prompt(input, plan=plan),
            context=ctx,
            max_turns=_RESEARCH_MAX_TURNS,
        )
        claims = cast("ClaimExtraction", claims_result.final_output)

    async with step("evidence_researcher"):
        evidence_result = await Runner.run(
            evidence_researcher_agent(),
            _stage_prompt(input, plan=plan, claims=claims),
            context=ctx,
            max_turns=_RESEARCH_MAX_TURNS,
        )
        evidence = cast("EvidenceResearch", evidence_result.final_output)

    async with step("competitor_mapper"):
        competitor_result = await Runner.run(
            competitor_mapper_agent(),
            _stage_prompt(input, plan=plan, claims=claims, evidence=evidence),
            context=ctx,
            max_turns=_RESEARCH_MAX_TURNS,
        )
        competitors = cast("CompetitorMapping", competitor_result.final_output)

    async with step("technical_substance_reviewer"):
        review_result = await Runner.run(
            technical_substance_reviewer_agent(),
            _stage_prompt(
                input,
                plan=plan,
                claims=claims,
                evidence=evidence,
                competitors=competitors,
                pages_read_by_domain=_pages_by_domain(ctx),
            ),
            context=ctx,
        )
        review = cast("TechnicalSubstanceReview", review_result.final_output)

    gap_results: list[DiligenceGapResearch] = []
    round_index = 0
    while review.unresolved_claims and round_index < effective_max_rounds:
        round_index += 1
        await emit_loop_iteration("gap", round_index)
        unread_high_value = _unread_high_value_urls(plan, ctx)
        async with step("gap_researcher"):
            gap_result = await Runner.run(
                gap_researcher_agent(),
                _stage_prompt(
                    input,
                    plan=plan,
                    claims=claims,
                    evidence=evidence,
                    competitors=competitors,
                    review=review,
                    gaps=gap_results,
                    unread_high_value_urls=unread_high_value,
                ),
                context=ctx,
                max_turns=_RESEARCH_MAX_TURNS,
            )
            gap_results.append(cast("DiligenceGapResearch", gap_result.final_output))
            # Re-evaluate which claims are still unresolved. If the gap researcher
            # produced no new assessments at all, stop early — further rounds won't
            # help and we've hit a public-evidence ceiling.
            previous_unresolved_count = len(review.unresolved_claims)
            review = _merge_gap_into_review(review, gap_results[-1])
            if not gap_results[-1].additional_claim_assessments and len(
                review.unresolved_claims
            ) == previous_unresolved_count:
                break

    async with step("final_memo"):
        final_result = await Runner.run(
            final_memo_agent(),
            _stage_prompt(
                input,
                plan=plan,
                claims=claims,
                evidence=evidence,
                competitors=competitors,
                review=review,
                gaps=gap_results,
            ),
            context=ctx,
        )
        final = cast("FinalMemoOutput", final_result.final_output)
        if claims.release_activity is not None and final.report.release_activity is None:
            final = final.model_copy(
                update={
                    "report": final.report.model_copy(
                        update={"release_activity": claims.release_activity}
                    )
                }
            )
        await emit_output_text_delta(final.answer_markdown)

    structured_data, validation_errors = _validate_report(final.report.model_dump(mode="json"))
    warnings = [*ctx.warnings, *validation_errors]

    return WorkflowResult(
        answer_markdown=final.answer_markdown,
        structured_data=structured_data,
        summary=_summary(final.report, evidence, gap_results),
        findings=[
            ResearchFinding(
                id=f"finding_{index}",
                claim=finding.claim,
                evidence_ids=finding.evidence_ids,
                confidence=_confidence_score(finding.confidence),
            )
            for index, finding in enumerate(final.findings, 1)
        ],
        sources=list(ctx.sources.list()),
        evidence=list(ctx.evidence),
        artifacts=list(ctx.artifacts),
        warnings=warnings,
        metadata=WorkflowMetadata(
            run_id=run_id if run_id != "run_uninstrumented" else f"run_{uuid4().hex}",
            workflow_id=WORKFLOW_ID,
            started_at=started_at,
            finished_at=datetime.now(UTC),
        ),
    )


def intake_planner_agent() -> Agent:
    return Agent(
        name="Technical Diligence Intake Planner",
        instructions=load_workflow_prompt(WORKFLOW_ID, "intake_planner.md"),
        model_settings=no_store_model_settings(),
        tools=list(RESEARCH_TOOLS),
        output_type=IntakePlan,
    )


def url_selector_agent() -> Agent:
    return Agent(
        name="Technical Diligence URL Selector",
        instructions=load_workflow_prompt(WORKFLOW_ID, "url_selector.md"),
        model=model_from_env(_URL_SELECTOR_MODEL_ENV, _URL_SELECTOR_DEFAULT_MODEL),
        model_settings=no_store_model_settings(),
        output_type=SelectedPriorityUrls,
    )


def claim_extractor_agent() -> Agent:
    return Agent(
        name="Technical Diligence Claim Extractor",
        instructions=load_workflow_prompt(WORKFLOW_ID, "claim_extractor.md"),
        model_settings=no_store_model_settings(),
        tools=list(RESEARCH_TOOLS),
        output_type=ClaimExtraction,
    )


def evidence_researcher_agent() -> Agent:
    return Agent(
        name="Technical Diligence Evidence Researcher",
        instructions=load_workflow_prompt(WORKFLOW_ID, "evidence_researcher.md"),
        model_settings=no_store_model_settings(),
        tools=list(RESEARCH_TOOLS),
        output_type=EvidenceResearch,
    )


def competitor_mapper_agent() -> Agent:
    return Agent(
        name="Technical Diligence Competitor Mapper",
        instructions=load_workflow_prompt(WORKFLOW_ID, "competitor_mapper.md"),
        model_settings=no_store_model_settings(),
        tools=list(RESEARCH_TOOLS),
        output_type=CompetitorMapping,
    )


def technical_substance_reviewer_agent() -> Agent:
    return Agent(
        name="Technical Diligence Substance Reviewer",
        instructions=load_workflow_prompt(WORKFLOW_ID, "technical_substance_reviewer.md"),
        model_settings=no_store_model_settings(),
        output_type=TechnicalSubstanceReview,
    )


def gap_researcher_agent() -> Agent:
    return Agent(
        name="Technical Diligence Gap Researcher",
        instructions=load_workflow_prompt(WORKFLOW_ID, "gap_researcher.md"),
        model_settings=no_store_model_settings(),
        tools=list(RESEARCH_TOOLS),
        output_type=DiligenceGapResearch,
    )


def final_memo_agent() -> Agent:
    return Agent(
        name="Technical Diligence Final Memo Writer",
        instructions=load_workflow_prompt(WORKFLOW_ID, "final_memo.md"),
        model_settings=no_store_model_settings(),
        output_type=FinalMemoOutput,
    )


def _input_prompt(input: WorkflowInput) -> str:
    return "\n".join(
        [
            f"Evaluation prompt: {input.query}",
            f"Instructions: {input.instructions or ''}",
            "Use only public evidence. Clearly label public evidence, inference, and unknowns.",
        ]
    )


def _stage_prompt(input: WorkflowInput, **values: object) -> str:
    return "\n".join(
        [
            _input_prompt(input),
            "Prior stage outputs:",
            _json(values),
        ]
    )


def _json(value: object) -> str:
    return json.dumps(_to_jsonable(value), sort_keys=True, indent=2)


def _to_jsonable(value: object) -> object:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, list):
        return [_to_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: _to_jsonable(item) for key, item in value.items()}
    return value


def _pages_by_domain(ctx: WorkflowContext) -> dict[str, int]:
    counts: dict[str, int] = {}
    for url in ctx.pages:
        domain = urlparse(url).netloc
        counts[domain] = counts.get(domain, 0) + 1
    return counts


def _all_priority_urls(cat: UrlsByCategory) -> list[str]:
    return (
        cat.docs
        + cat.api
        + cat.changelog
        + cat.pricing
        + cat.security
        + cat.customers
        + cat.blog
        + cat.careers
        + cat.other
    )


async def _run_url_selector(
    input: WorkflowInput,
    ctx: WorkflowContext,
    plan: IntakePlan,
) -> IntakePlan:
    candidate_urls = plan.priority_urls_by_category
    if not _all_priority_urls(candidate_urls):
        return plan

    async with step("url_selector"):
        try:
            selection_result = await Runner.run(
                url_selector_agent(),
                _stage_prompt(
                    input,
                    target=plan.target,
                    research_questions=plan.research_questions,
                    candidate_urls_by_category=candidate_urls,
                    budgets=_URL_SELECTION_BUDGETS,
                ),
                context=ctx,
            )
            selected = cast("SelectedPriorityUrls", selection_result.final_output)
            priority_urls = _validated_priority_urls(candidate_urls, selected)
        except Exception as exc:
            ctx.warnings.append(
                f"url_selector failed; using deterministic URL selection: {exc}"
            )
            priority_urls = _fallback_priority_urls(candidate_urls)
    return plan.model_copy(update={"priority_urls_by_category": priority_urls})


def _urls_for_category(cat: UrlsByCategory, category: str) -> list[str]:
    return cast("list[str]", getattr(cat, category))


def _urls_by_category(cat: UrlsByCategory) -> dict[str, list[str]]:
    return {category: _urls_for_category(cat, category) for category in _URL_CATEGORIES}


def _normalize_or_none(url: str) -> str | None:
    try:
        return normalize_url(url)
    except ValueError:
        return None


def _fallback_priority_urls(candidate_urls: UrlsByCategory) -> UrlsByCategory:
    return UrlsByCategory(
        **{
            category: _urls_for_category(candidate_urls, category)[
                : _URL_SELECTION_BUDGETS[category]
            ]
            for category in _URL_CATEGORIES
        }
    )


def _validated_priority_urls(
    candidate_urls: UrlsByCategory,
    selected: SelectedPriorityUrls,
) -> UrlsByCategory:
    fallback = _fallback_priority_urls(candidate_urls)
    candidates_by_category = _urls_by_category(candidate_urls)
    selected_by_category = _urls_by_category(selected.priority_urls_by_category)
    updates: dict[str, list[str]] = {}

    for category in _URL_CATEGORIES:
        candidate_lookup = {
            normalized: url
            for url in candidates_by_category[category]
            if (normalized := _normalize_or_none(url)) is not None
        }
        seen: set[str] = set()
        valid: list[str] = []
        for url in selected_by_category[category]:
            normalized = _normalize_or_none(url)
            if normalized is None or normalized not in candidate_lookup or normalized in seen:
                continue
            seen.add(normalized)
            valid.append(candidate_lookup[normalized])
            if len(valid) >= _URL_SELECTION_BUDGETS[category]:
                break
        updates[category] = valid

    if not any(updates.values()):
        return fallback

    fallback_by_category = _urls_by_category(fallback)
    for category in _MIN_COVERAGE_CATEGORIES:
        if not updates[category] and fallback_by_category[category]:
            updates[category] = fallback_by_category[category][:1]

    return UrlsByCategory(**updates)


def _unread_high_value_urls(plan: IntakePlan, ctx: WorkflowContext) -> list[str]:
    fetched = set(ctx.pages.keys())
    high_value = (
        plan.priority_urls_by_category.docs
        + plan.priority_urls_by_category.api
        + plan.priority_urls_by_category.changelog
        + plan.priority_urls_by_category.security
    )
    return [u for u in high_value if u not in fetched]


def _merge_gap_into_review(
    review: TechnicalSubstanceReview,
    gap: DiligenceGapResearch,
) -> TechnicalSubstanceReview:
    resolved_claim_ids = {
        a.claim for a in gap.additional_claim_assessments if a.assessment != "unclear"
    }
    remaining = [c for c in review.unresolved_claims if c.claim_text not in resolved_claim_ids]
    return review.model_copy(update={"unresolved_claims": remaining})


def _validate_report(
    structured_data: dict[str, object],
) -> tuple[dict[str, object] | None, list[str]]:
    schema = json.loads(
        files("webresearch.workflows.technical_due_diligence")
        .joinpath("schema.json")
        .read_text(encoding="utf-8")
    )
    try:
        validate(instance=structured_data, schema=schema)
    except JsonSchemaValidationError as exc:
        return None, [f"Structured data invalid: {exc.message}"]
    return structured_data, []


def _summary(
    report: TechnicalDueDiligenceReport,
    evidence: EvidenceResearch,
    gaps: list[DiligenceGapResearch],
) -> str:
    parts: list[str] = []
    supported = next(
        (a for a in report.claims if a.assessment == "supported"),
        evidence.claim_assessments[0] if evidence.claim_assessments else None,
    )
    if supported:
        parts.append(supported.public_evidence)
    elif report.evidence_gaps:
        parts.append(report.evidence_gaps[0])
    parts.extend(gap.summary for gap in gaps)
    return "\n".join(part for part in parts if part)


def _confidence_score(confidence: str) -> float:
    return {"low": 0.33, "medium": 0.66, "high": 1.0}[confidence]
