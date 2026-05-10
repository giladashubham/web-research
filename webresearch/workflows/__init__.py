from __future__ import annotations

from importlib.metadata import entry_points
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

if TYPE_CHECKING:
    from collections.abc import Callable

    from webresearch.types import WorkflowFn


class WorkflowEntry(BaseModel):
    """Metadata for a workflow, discoverable via entry points."""

    model_config = ConfigDict(extra="forbid")
    id: str
    name: str
    description: str


_WORKFLOW_GROUP = "webresearch.workflows"
_METADATA_GROUP = "webresearch.workflows.metadata"


def load_workflows() -> dict[str, WorkflowFn]:
    """Discover and load all installed workflows via entry points."""
    eps = entry_points(group=_WORKFLOW_GROUP)
    result: dict[str, WorkflowFn] = {}
    for ep in eps:
        loaded = ep.load()
        result[ep.name] = loaded
    return result


def load_workflow_entries() -> list[WorkflowEntry]:
    """Collect metadata for all installed workflows.

    Reads from the ``webresearch.workflows.metadata`` entry-point group.
    Each entry must point to a zero-argument callable that returns a
    :class:`WorkflowEntry`.  Workflows registered in ``webresearch.workflows``
    that lack a metadata entry receive a minimal fallback entry.
    """
    entries_by_id: dict[str, WorkflowEntry] = {}

    # Preferred: dedicated metadata entry points.
    meta_eps = entry_points(group=_METADATA_GROUP)
    for ep in meta_eps:
        factory: Callable[[], WorkflowEntry] = ep.load()
        entry = factory()
        entries_by_id[entry.id] = entry

    # Fallback: any workflow entry point without metadata.
    wf_eps = entry_points(group=_WORKFLOW_GROUP)
    for ep in wf_eps:
        if ep.name not in entries_by_id:
            entries_by_id[ep.name] = WorkflowEntry(
                id=ep.name,
                name=ep.name.replace("_", " ").title(),
                description="",
            )

    return list(entries_by_id.values())
