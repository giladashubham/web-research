from __future__ import annotations

import asyncio

from tests.tui.helpers import fake_workflow
from webresearch.tui.app import WebResearchApp
from webresearch.tui.screens.result import ResultScreen
from webresearch.tui.screens.run import RunScreen
from webresearch.tui.widgets.timeline import TimelineWidget
from webresearch.tui.widgets.warnings import WarningsWidget
from webresearch.types import WorkflowInput
from webresearch.workflows.registry import WORKFLOWS


async def test_run_screen_timeline_and_completion(monkeypatch) -> None:
    monkeypatch.setitem(WORKFLOWS, "fake", fake_workflow)
    app = WebResearchApp()
    async with app.run_test() as pilot:
        await app.push_screen(RunScreen("fake", WorkflowInput(query="query")))
        await pilot.pause(0.2)
        assert isinstance(app.screen, ResultScreen)


async def test_run_screen_widgets_populate(monkeypatch) -> None:
    monkeypatch.setitem(WORKFLOWS, "fake", fake_workflow)
    app = WebResearchApp()
    async with app.run_test() as pilot:
        screen = RunScreen("fake", WorkflowInput(query="query"))
        await app.push_screen(screen)
        await pilot.pause(0.1)
        assert "planner" in screen.query_one("#timeline", TimelineWidget).text


async def test_cancelled_run_shows_cancelled(monkeypatch) -> None:
    async def slow_workflow(input_: WorkflowInput):
        _ = input_
        await asyncio.sleep(10)

    monkeypatch.setitem(WORKFLOWS, "slow", slow_workflow)
    app = WebResearchApp()
    async with app.run_test() as pilot:
        screen = RunScreen("slow", WorkflowInput(query="query"))
        await app.push_screen(screen)
        await pilot.pause(0.05)
        await screen.cancel_run()
        assert screen.cancelled is True
        assert "cancelled" in screen.query_one("#timeline", TimelineWidget).text


async def test_warnings_widget_populates_directly() -> None:
    widget = WarningsWidget()
    widget.add_warning("warning")
    assert "warning" in widget.text
