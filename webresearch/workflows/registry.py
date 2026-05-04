from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from webresearch.workflows.standard import run_standard

WORKFLOWS = {"standard": run_standard}


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
    )
]


def workflow_entries() -> list[WorkflowEntry]:
    return list(WORKFLOW_ENTRIES)
