from __future__ import annotations

from collections.abc import Awaitable, Callable
from importlib.metadata import entry_points
from typing import Any

from pydantic import BaseModel, ConfigDict

from webresearch.types import WorkflowInput, WorkflowResult

WorkflowFn = Callable[[WorkflowInput], Awaitable[WorkflowResult]]


class WorkflowEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    name: str
    description: str


_WORKFLOW_METADATA: dict[str, WorkflowEntry] = {
    "deep": WorkflowEntry(
        id="deep",
        name="Deep",
        description="Higher-budget deep research with parallel lanes and gap loop.",
    ),
    "technical_due_diligence": WorkflowEntry(
        id="technical_due_diligence",
        name="Technical Due Diligence",
        description=(
            "Public technical claims, release activity, competitors, "
            "and code-review follow-ups."
        ),
    ),
}


def load_workflows() -> dict[str, WorkflowFn]:
    eps = entry_points(group="webresearch.workflows")
    result: dict[str, WorkflowFn] = {}
    for ep in eps:
        loaded = ep.load()
        result[ep.name] = loaded
    return result


def load_workflow_entries() -> list[WorkflowEntry]:
    eps = entry_points(group="webresearch.workflows")
    entries: list[WorkflowEntry] = []
    for ep in eps:
        meta = _WORKFLOW_METADATA.get(ep.name)
        if meta is not None:
            entries.append(meta)
    return entries

