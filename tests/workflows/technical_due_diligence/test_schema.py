from __future__ import annotations

import json
from importlib.resources import files

from jsonschema import Draft202012Validator

from webresearch.workflows.technical_due_diligence import TechnicalDueDiligenceReport

PACKAGE = "webresearch.workflows.technical_due_diligence"


def test_schema_json_is_valid_json_schema() -> None:
    schema = json.loads(files(PACKAGE).joinpath("schema.json").read_text(encoding="utf-8"))

    Draft202012Validator.check_schema(schema)


def test_schema_matches_report_model_schema() -> None:
    schema = json.loads(files(PACKAGE).joinpath("schema.json").read_text(encoding="utf-8"))

    assert schema == TechnicalDueDiligenceReport.model_json_schema()
