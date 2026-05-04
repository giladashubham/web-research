from __future__ import annotations

from textual.app import App, ComposeResult
from textual.widgets import Static

from webresearch.tui.screens.home import HomeScreen


class WebResearchApp(App[None]):
    CSS = """
    #help-overlay { dock: top; display: none; background: $boost; padding: 1; }
    #help-overlay.visible { display: block; }
    #timeline { width: 45%; }
    #run-side { width: 55%; }
    """
    BINDINGS = [("q", "quit_or_confirm", "Quit"), ("?", "toggle_help", "Help")]

    def __init__(self) -> None:
        super().__init__()
        self.run_active = False
        self.query_state: dict[str, dict[str, str]] = {}

    def compose(self) -> ComposeResult:
        yield Static("q quit  ? help  s settings  Enter select/run", id="help-overlay")

    def on_mount(self) -> None:
        self.push_screen(HomeScreen())

    def action_toggle_help(self) -> None:
        overlay = self.query_one("#help-overlay", Static)
        overlay.toggle_class("visible")

    def action_quit_or_confirm(self) -> None:
        if self.run_active:
            self.notify("A run is active. Use Ctrl-C on the run screen to cancel.")
            return
        self.exit()


def run() -> None:
    WebResearchApp().run()
