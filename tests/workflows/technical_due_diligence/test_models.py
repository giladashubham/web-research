from __future__ import annotations

import json
from importlib.resources import files

from webresearch.workflows.technical_due_diligence import TechnicalDueDiligenceReport

PACKAGE = "webresearch.workflows.technical_due_diligence"


def test_report_model_validates_example_output() -> None:
    example = json.loads(
        files(PACKAGE)
        .joinpath("examples", "output.example.json")
        .read_text(encoding="utf-8")
    )

    report = TechnicalDueDiligenceReport.model_validate(example)

    assert report.target.company_name == "Example Robotics"
    assert report.release_activity is not None
    assert report.release_activity.releases_last_12_months == 24
    assert report.code_review_follow_ups[0].priority == "high"


def test_example_input_is_valid_json() -> None:
    example_input = json.loads(
        files(PACKAGE)
        .joinpath("examples", "input.example.json")
        .read_text(encoding="utf-8")
    )

    assert example_input["company_name"] == "Example Robotics"
    assert "known_urls" in example_input
