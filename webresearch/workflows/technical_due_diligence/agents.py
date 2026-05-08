from __future__ import annotations

from importlib.resources import files
from typing import cast
from urllib.parse import urlparse

from webresearch.pipeline.hooks import HookSignal
from webresearch.pipeline.state import PipelineState
from webresearch.pipeline.step import AgentStep
from webresearch.providers.discover import UrlsByCategory
from webresearch.sources.url_normalize import normalize_url
from webresearch.workflows.technical_due_diligence.config import CONFIG
from webresearch.workflows.technical_due_diligence.models import (
    ClaimExtraction,
    DiligenceGapResearch,
    EvidenceResearch,
    FinalMemoOutput,
    IntakePlan,
    SelectedPriorityUrls,
    TechnicalSubstanceReview,
)
from webresearch.workflows.technical_due_diligence.tools import RESEARCH_TOOLS

_URL_CATEGORIES = (
    "docs", "api", "changelog", "security", "customers",
    "blog", "careers", "other",
)
_MIN_COVERAGE_CATEGORIES = ("docs", "api", "changelog", "security")


def _prompt(name: str) -> str:
    return (
        files("webresearch.workflows.technical_due_diligence")
        / "prompts"
        / f"{name}.j2"
    ).read_text(encoding="utf-8")


# --- URL validation helpers ---

def _all_priority_urls(cat: UrlsByCategory) -> list[str]:
    return (
        cat.docs + cat.api + cat.changelog + cat.security
        + cat.customers + cat.blog + cat.careers + cat.other
    )


def _urls_for_category(cat: UrlsByCategory, category: str) -> list[str]:
    return cast("list[str]", getattr(cat, category))


def _urls_by_category(cat: UrlsByCategory) -> dict[str, list[str]]:
    return {c: _urls_for_category(cat, c) for c in _URL_CATEGORIES}


def _normalize_or_none(url: str) -> str | None:
    try:
        return normalize_url(url)
    except ValueError:
        return None


def _fallback_priority_urls(candidate_urls: UrlsByCategory) -> UrlsByCategory:
    return UrlsByCategory(
        **{
            category: _urls_for_category(candidate_urls, category)[
                : CONFIG.url_budgets[category]
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
    selected_by_category = _urls_by_category(selected.evidence_urls_by_category)
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
            if (
                normalized is None
                or normalized not in candidate_lookup
                or normalized in seen
            ):
                continue
            seen.add(normalized)
            valid.append(candidate_lookup[normalized])
            if len(valid) >= CONFIG.url_budgets[category]:
                break
        updates[category] = valid

    if not any(updates.values()):
        return fallback

    fallback_by_category = _urls_by_category(fallback)
    for category in _MIN_COVERAGE_CATEGORIES:
        if not updates[category] and fallback_by_category[category]:
            updates[category] = fallback_by_category[category][:1]

    return UrlsByCategory(**updates)


def _merge_gap_into_review(
    review: TechnicalSubstanceReview,
    gap: DiligenceGapResearch,
) -> TechnicalSubstanceReview:
    resolved_by_id: set[str] = set()
    resolved_by_text: set[str] = set()
    for a in gap.additional_claim_assessments:
        if a.assessment in (
            "supported", "partially_supported", "unsupported", "contradicted",
        ):
            if a.claim_id is not None:
                resolved_by_id.add(a.claim_id)
            else:
                resolved_by_text.add(a.claim)
    remaining = [
        c
        for c in review.unresolved_claims
        if c.claim_id not in resolved_by_id
        and c.claim_text not in resolved_by_text
    ]
    return review.model_copy(update={"unresolved_claims": remaining})


# --- Hooks ---

async def _url_selector_pre_hook(state: PipelineState) -> HookSignal:
    plan: IntakePlan | None = state.outputs.get("intake_planner")
    if plan is None or not _all_priority_urls(plan.evidence_urls_by_category):
        return HookSignal.SKIP
    return HookSignal.CONTINUE


async def _url_selector_post_hook(state: PipelineState) -> HookSignal:
    plan = state.outputs.get("intake_planner")
    selected = state.outputs.get("url_selector")
    if plan is not None and selected is not None:
        state.outputs["url_selector"] = _validated_priority_urls(
            plan.evidence_urls_by_category, selected
        )
    return HookSignal.CONTINUE


async def _gap_post_hook(state: PipelineState) -> HookSignal:
    review = state.outputs.get("technical_substance_reviewer")
    gap = state.outputs.get("gap_researcher")
    if review is not None and gap is not None:
        state.outputs["technical_substance_reviewer"] = _merge_gap_into_review(
            review, gap
        )
    return HookSignal.CONTINUE


# --- Agents ---

intake_planner = AgentStep(
    name="intake_planner",
    prompt=_prompt("intake_planner"),
    tools=RESEARCH_TOOLS,
    output_type=IntakePlan,
    max_turns=CONFIG.research_max_turns,
)

url_selector = AgentStep(
    name="url_selector",
    prompt=_prompt("url_selector"),
    output_type=SelectedPriorityUrls,
    pre_hook=_url_selector_pre_hook,
    post_hook=_url_selector_post_hook,
)

claim_extractor = AgentStep(
    name="claim_extractor",
    prompt=_prompt("claim_extractor"),
    tools=RESEARCH_TOOLS,
    output_type=ClaimExtraction,
    max_turns=CONFIG.research_max_turns,
)

evidence_researcher = AgentStep(
    name="evidence_researcher",
    prompt=_prompt("evidence_researcher"),
    tools=RESEARCH_TOOLS,
    output_type=EvidenceResearch,
    max_turns=CONFIG.research_max_turns,
)

technical_substance_reviewer = AgentStep(
    name="technical_substance_reviewer",
    prompt=_prompt("technical_substance_reviewer"),
    output_type=TechnicalSubstanceReview,
)

gap_researcher = AgentStep(
    name="gap_researcher",
    prompt=_prompt("gap_researcher"),
    tools=RESEARCH_TOOLS,
    output_type=DiligenceGapResearch,
    max_turns=CONFIG.research_max_turns,
    post_hook=_gap_post_hook,
)

final_memo = AgentStep(
    name="final_memo",
    prompt=_prompt("final_memo"),
    output_type=FinalMemoOutput,
)
