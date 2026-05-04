from __future__ import annotations

from textual.widgets import Static

from webresearch.tui.app import WebResearchApp


async def test_app_opens_and_help_toggles() -> None:
    app = WebResearchApp()
    async with app.run_test() as pilot:
        assert app.screen is not None
        await pilot.press("?")
        assert app.query_one("#help-overlay", Static).has_class("visible")


async def test_q_exits_when_no_run_active() -> None:
    app = WebResearchApp()
    async with app.run_test() as pilot:
        await pilot.press("q")
        assert app.return_code == 0


async def test_q_does_not_exit_when_run_active() -> None:
    app = WebResearchApp()
    async with app.run_test() as pilot:
        app.run_active = True
        await pilot.press("q")
        assert app.return_code is None
