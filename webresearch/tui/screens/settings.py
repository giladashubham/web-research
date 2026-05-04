from __future__ import annotations

import os

from textual.app import ComposeResult
from textual.widgets import Footer, Static

from webresearch.tui.screen_base import WorkflowAwareScreen


class SettingsScreen(WorkflowAwareScreen):
    BINDINGS = [("escape", "app.pop_screen", "Back")]

    def compose(self) -> ComposeResult:
        model = os.getenv("OPENAI_MODEL", "default")
        openai = "✓" if os.getenv("OPENAI_API_KEY") else "✗"
        tavily = "✓" if os.getenv("TAVILY_API_KEY") else "✗"
        yield Static(
            "\n".join(
                [
                    f"Resolved model: {model}",
                    f"OPENAI_API_KEY: {openai}",
                    f"TAVILY_API_KEY: {tavily}",
                    f"Workflows: {len(self.workflow_entries)}",
                ]
            ),
            id="settings-content",
        )
        yield Footer()
