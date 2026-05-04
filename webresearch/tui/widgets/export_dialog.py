from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Select, Static

from webresearch.cli.formats import format_result
from webresearch.types import WorkflowResult


class ExportDialog(ModalScreen[bool]):
    def __init__(self, result: WorkflowResult) -> None:
        super().__init__()
        self.result = result

    def compose(self) -> ComposeResult:
        yield Vertical(
            Static("Export"),
            Select([("JSON", "json"), ("Markdown", "md")], value="json", id="export-format"),
            Input(placeholder="Path", id="export-path"),
            Button("Export", id="export-confirm"),
            Static("", id="export-error"),
            id="export-dialog",
        )

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id != "export-confirm":
            return
        path = Path(self.query_one("#export-path", Input).value)
        if path.exists():
            self.query_one("#export-error", Static).update("File exists; refusing to overwrite.")
            return
        output_format = self.query_one("#export-format", Select).value
        path.write_text(format_result(self.result, output_format), encoding="utf-8")
        self.dismiss(True)
