from __future__ import annotations

import json
from importlib.resources import files

from jsonschema import Draft202012Validator

from webresearch.workflows.registry import WORKFLOWS
from webresearch.workflows.technical_due_diligence import (
    TechnicalDueDiligenceReport,
    run_technical_due_diligence,
)

PACKAGE = "webresearch.workflows.technical_due_diligence"


def _json_resource(*parts: str) -> dict[str, object]:
    path = files(PACKAGE).joinpath(*parts)
    return json.loads(path.read_text(encoding="utf-8"))


def test_package_imports_cleanly() -> None:
    assert run_technical_due_diligence is not None
    assert TechnicalDueDiligenceReport.__name__ == "TechnicalDueDiligenceReport"


def test_schema_json_is_valid_json_schema() -> None:
    schema = _json_resource("schema.json")

    Draft202012Validator.check_schema(schema)


def test_example_output_validates_against_report_model() -> None:
    example_output = _json_resource("examples", "output.example.json")

    report = TechnicalDueDiligenceReport.model_validate(example_output)

    assert report.target.company_name == "Example Robotics"
    assert report.executive_judgment.technical_substance == "mixed"


def test_example_input_is_valid_json() -> None:
    example_input = _json_resource("examples", "input.example.json")

    assert example_input["company_name"] == "Example Robotics"


def test_workflow_is_not_registered_until_runnable() -> None:
    assert "technical_due_diligence" not in WORKFLOWS
