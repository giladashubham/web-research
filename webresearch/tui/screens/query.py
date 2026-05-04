from __future__ import annotations

from textual.app import ComposeResult
from textual.widgets import Button, Footer, Input, Select, TextArea

from webresearch.tui.screen_base import WorkflowAwareScreen
from webresearch.types import Depth, WorkflowInput


class QueryScreen(WorkflowAwareScreen):
    BINDINGS = [("escape", "app.pop_screen", "Back"), ("ctrl+enter", "run", "Run")]

    def __init__(self, workflow_id: str) -> None:
        super().__init__()
        self.workflow_id = workflow_id

    def compose(self) -> ComposeResult:
        state = self.app.query_state.setdefault(self.workflow_id, {})
        yield TextArea(state.get("query", ""), id="query-text")
        yield Input(
            value=state.get("instructions", ""),
            placeholder="Instructions",
            id="instructions",
        )
        yield Select(
            [("quick", "quick"), ("standard", "standard"), ("deep", "deep")],
            value=state.get("depth", "standard"),
            id="depth-select",
        )
        yield Button("Run", id="run-button", disabled=not bool(state.get("query", "").strip()))
        yield Footer()

    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        self.app.query_state.setdefault(self.workflow_id, {})["query"] = event.text_area.text
        self.query_one("#run-button", Button).disabled = not bool(event.text_area.text.strip())

    def on_input_changed(self, event: Input.Changed) -> None:
        self.app.query_state.setdefault(self.workflow_id, {})["instructions"] = event.value

    def on_select_changed(self, event: Select.Changed) -> None:
        self.app.query_state.setdefault(self.workflow_id, {})["depth"] = event.value

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "run-button":
            await self.action_run()

    async def action_run(self) -> None:
        query = self.query_one("#query-text", TextArea).text.strip()
        if not query:
            return
        instructions = self.query_one("#instructions", Input).value or None
        depth = str(self.query_one("#depth-select", Select).value)
        workflow_input = WorkflowInput(
            query=query,
            instructions=instructions,
            depth=Depth.for_preset(depth),
        )
        from webresearch.tui.screens.run import RunScreen

        self.app.push_screen(RunScreen(self.workflow_id, workflow_input))
