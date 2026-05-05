from __future__ import annotations

from webresearch.workflows.shared.prompt_loader import load_workflow_prompt
from webresearch.workflows.technical_due_diligence.workflow import WORKFLOW_ID


def test_diligence_prompts_label_evidence_inference_and_unknowns() -> None:
    prompt_names = [
        "intake_planner.md",
        "claim_extractor.md",
        "evidence_researcher.md",
        "competitor_mapper.md",
        "technical_substance_reviewer.md",
        "gap_researcher.md",
        "final_memo.md",
    ]

    combined = "\n".join(load_workflow_prompt(WORKFLOW_ID, name) for name in prompt_names).lower()

    assert "public evidence" in combined
    assert "inference" in combined
    assert "unknown" in combined
    assert "code-review" in combined or "code review" in combined
