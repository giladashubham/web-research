from __future__ import annotations

from textual.app import ComposeResult
from textual.widgets import Footer, Label, ListItem, ListView, Static

from webresearch.tui.screen_base import WorkflowAwareScreen


class HomeScreen(WorkflowAwareScreen):
    BINDINGS = [("s", "settings", "Settings")]

    def compose(self) -> ComposeResult:
        yield Label("Web Research", id="home-title")
        entries = self.workflow_entries
        if not entries:
            yield Static("No workflows registered.", id="empty-workflows")
        else:
            items: list[ListItem] = []
            for entry in entries:
                item = ListItem(
                    Static(f"{entry.id}  {entry.name}  {entry.description}"),
                    id=f"workflow-{entry.id}",
                )
                item.workflow_id = entry.id
                items.append(item)
            yield ListView(*items, id="workflow-list")
        yield Static("↑/↓ select  Enter run  s settings  q quit", id="home-footer")
        yield Footer()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        workflow_id = getattr(event.item, "workflow_id", "standard")
        from webresearch.tui.screens.query import QueryScreen

        self.app.push_screen(QueryScreen(workflow_id))

    def action_settings(self) -> None:
        from webresearch.tui.screens.settings import SettingsScreen

        self.app.push_screen(SettingsScreen())
