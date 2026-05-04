from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Static


class ConfirmCancelDialog(ModalScreen[bool]):
    def compose(self) -> ComposeResult:
        yield Vertical(
            Static("Cancel running workflow? y/N"),
            Button("Yes", id="confirm-cancel"),
            Button("No", id="dismiss-cancel"),
            id="cancel-dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "confirm-cancel")
