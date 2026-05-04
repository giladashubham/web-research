from __future__ import annotations

import asyncio
from contextlib import suppress

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Footer, Static, TabbedContent, TabPane

from webresearch.events.types import (
    ArtifactAdded,
    LoopIteration,
    OutputTextDelta,
    SourceAdded,
    StepCompleted,
    StepFailed,
    StepSkipped,
    StepStarted,
    ToolCompleted,
    ToolStarted,
    Warning,
    WorkflowCompleted,
    WorkflowFailed,
)
from webresearch.tui.screen_base import WorkflowAwareScreen
from webresearch.tui.widgets.artifacts import ArtifactsWidget
from webresearch.tui.widgets.confirm_cancel import ConfirmCancelDialog
from webresearch.tui.widgets.timeline import TimelineWidget
from webresearch.tui.widgets.warnings import WarningsWidget
from webresearch.types import WorkflowInput, WorkflowResult


class RunScreen(WorkflowAwareScreen):
    BINDINGS = [("ctrl+c", "confirm_cancel", "Cancel"), ("q", "confirm_cancel", "Cancel")]

    def __init__(self, workflow_id: str, workflow_input: WorkflowInput) -> None:
        super().__init__()
        self.workflow_id = workflow_id
        self.workflow_input = workflow_input
        self.run_task: asyncio.Task[None] | None = None
        self.stream = None
        self.cancelled = False
        self.result: WorkflowResult | None = None
        self.deltas: list[str] = []

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield TimelineWidget(id="timeline")
            with Vertical(id="run-side"):
                with TabbedContent(id="run-tabs"):
                    with TabPane("Artifacts", id="artifacts-tab"):
                        yield ArtifactsWidget(id="artifacts")
                    with TabPane("Warnings", id="warnings-tab"):
                        yield WarningsWidget(id="warnings")
                yield Static("", id="run-error")
                yield Button("Return Home", id="return-home")
        yield Footer()

    def on_mount(self) -> None:
        self.app.run_active = True
        self.run_task = asyncio.create_task(self._run())

    async def _run(self) -> None:
        try:
            workflow_fn = self.workflows[self.workflow_id]
            self.result = await workflow_fn(self.workflow_input)
            self.stream = self.stream_run(self.workflow_id, self.workflow_input)
            async for event in self.stream:
                if isinstance(event, StepStarted):
                    self.query_one("#timeline", TimelineWidget).set_status(event.step, "running")
                elif isinstance(event, StepCompleted):
                    self.query_one("#timeline", TimelineWidget).set_status(event.step, "done")
                elif isinstance(event, StepSkipped):
                    self.query_one("#timeline", TimelineWidget).set_status(event.step, "skipped")
                elif isinstance(event, StepFailed):
                    self.query_one("#timeline", TimelineWidget).set_status(event.step, "failed")
                elif isinstance(event, ToolStarted | ToolCompleted):
                    self.query_one("#timeline", TimelineWidget).add_tool(
                        event.step,
                        event.tool_name,
                    )
                elif isinstance(event, LoopIteration):
                    self.query_one("#timeline", TimelineWidget).add_loop(
                        event.loop,
                        event.iteration,
                    )
                elif isinstance(event, ArtifactAdded):
                    await self.query_one("#artifacts", ArtifactsWidget).add_artifact(
                        event.artifact_id,
                        event.artifact_kind,
                    )
                elif isinstance(event, SourceAdded):
                    await self.query_one("#artifacts", ArtifactsWidget).add_artifact(
                        event.source_id,
                        "source",
                    )
                elif isinstance(event, Warning):
                    self.query_one("#warnings", WarningsWidget).add_warning(event.message)
                elif isinstance(event, OutputTextDelta):
                    self.deltas.append(event.delta)
                elif isinstance(event, WorkflowFailed):
                    self.query_one("#run-error", Static).update(event.error)
                elif isinstance(event, WorkflowCompleted) and self.result is not None:
                    from webresearch.tui.screens.result import ResultScreen

                    self.app.push_screen(ResultScreen(self.result, "".join(self.deltas)))
        except asyncio.CancelledError:
            self.cancelled = True
            self.query_one("#timeline", TimelineWidget).set_status("run", "cancelled")
            raise
        finally:
            self.app.run_active = False

    async def action_confirm_cancel(self) -> None:
        confirmed = await self.app.push_screen_wait(ConfirmCancelDialog())
        if confirmed:
            await self.cancel_run()

    async def cancel_run(self) -> None:
        if self.run_task is not None and not self.run_task.done():
            self.run_task.cancel()
            with suppress(asyncio.CancelledError):
                await asyncio.wait_for(self.run_task, timeout=1)
            self.cancelled = True
            self.query_one("#timeline", TimelineWidget).set_status("run", "cancelled")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "return-home":
            self.app.pop_screen()
