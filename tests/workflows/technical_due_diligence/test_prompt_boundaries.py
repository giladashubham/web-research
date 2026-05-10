from __future__ import annotations

from importlib.resources import files


def test_diligence_prompts_label_evidence_inference_and_unknowns() -> None:
    prompt_names = [
        "intake_planner.j2",
        "url_selector.j2",
        "claim_extractor.j2",
        "evidence_researcher.j2",
        "technical_substance_reviewer.j2",
        "gap_researcher.j2",
        "final_memo.j2",
    ]

    pkg = "webresearch.workflows.technical_due_diligence"
    combined = "\n".join(
        (files(pkg) / "prompts" / name).read_text(encoding="utf-8")
        for name in prompt_names
    ).lower()

    assert "public evidence" in combined
    assert "inference" in combined
    assert "unknown" in combined
    assert "code-review" in combined or "code review" in combined
