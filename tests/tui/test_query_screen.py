from __future__ import annotations

from textual.widgets import Button, TextArea

from webresearch.tui.app import WebResearchApp
from webresearch.tui.screens.query import QueryScreen
from webresearch.tui.screens.run import RunScreen


async def test_empty_query_disables_run() -> None:
    app = WebResearchApp()
    async with app.run_test():
        await app.push_screen(QueryScreen("standard"))
        assert app.screen.query_one("#run-button", Button).disabled is True


async def test_run_button_enabled_and_pushes_run_screen() -> None:
    app = WebResearchApp()
    async with app.run_test() as pilot:
        await app.push_screen(QueryScreen("standard"))
        app.screen.query_one("#query-text", TextArea).text = "query"
        await pilot.pause()
        assert app.screen.query_one("#run-button", Button).disabled is False
        await app.screen.action_run()
        assert isinstance(app.screen, RunScreen)


async def test_esc_returns_home_preserving_text() -> None:
    app = WebResearchApp()
    async with app.run_test() as pilot:
        await app.push_screen(QueryScreen("standard"))
        app.screen.query_one("#query-text", TextArea).text = "saved query"
        await pilot.pause()
        await pilot.press("escape")
        await app.push_screen(QueryScreen("standard"))
        assert app.screen.query_one("#query-text", TextArea).text == "saved query"
