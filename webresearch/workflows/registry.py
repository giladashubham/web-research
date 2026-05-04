from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from webresearch.workflows.deep import run_deep
from webresearch.workflows.quick import run_quick
from webresearch.workflows.standard import run_standard

WORKFLOWS = {"standard": run_standard, "quick": run_quick, "deep": run_deep}


class WorkflowEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    description: str


WORKFLOW_ENTRIES = [
    WorkflowEntry(
        id="standard",
        name="Standard",
        description="Planner, parallel research, review, gap loop, and final answer.",
    ),
    WorkflowEntry(
        id="quick",
        name="Quick",
        description="Planner, lean parallel research, and final answer.",
    ),
    WorkflowEntry(
        id="deep",
        name="Deep",
        description="Higher-budget standard workflow with extra gap follow-up.",
    ),
]


def workflow_entries() -> list[WorkflowEntry]:
    return list(WORKFLOW_ENTRIES)
