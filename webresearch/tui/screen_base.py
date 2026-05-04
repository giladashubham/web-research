from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable

from textual.screen import Screen

from webresearch.events.stream import stream_workflow
from webresearch.events.types import WorkflowEvent
from webresearch.types import WorkflowInput, WorkflowResult
from webresearch.workflows.registry import WORKFLOWS, WorkflowEntry, workflow_entries

WorkflowFn = Callable[[WorkflowInput], Awaitable[WorkflowResult]]


class WorkflowAwareScreen(Screen[object]):
    @property
    def workflows(self) -> dict[str, WorkflowFn]:
        return WORKFLOWS

    @property
    def workflow_entries(self) -> list[WorkflowEntry]:
        return workflow_entries()

    def stream_run(
        self,
        workflow_id: str,
        workflow_input: WorkflowInput,
    ) -> AsyncIterator[WorkflowEvent]:
        return stream_workflow(self.workflows[workflow_id], workflow_input)
