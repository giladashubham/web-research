from __future__ import annotations

from unittest.mock import MagicMock

from webresearch.workflows import WorkflowEntry, load_workflow_entries, load_workflows


def test_load_workflows_empty(monkeypatch) -> None:
    monkeypatch.setattr(
        "webresearch.workflows.entry_points",
        lambda **_: [],
    )
    result = load_workflows()
    assert result == {}


def test_load_workflows_discovers_entry_points(monkeypatch) -> None:
    async def my_workflow(_input):
        return None

    ep = MagicMock()
    ep.name = "deep"
    ep.load.return_value = my_workflow

    monkeypatch.setattr(
        "webresearch.workflows.entry_points",
        lambda **_: [ep],
    )
    result = load_workflows()
    assert "deep" in result
    assert result["deep"] is my_workflow


def test_load_workflow_entries_empty(monkeypatch) -> None:
    monkeypatch.setattr(
        "webresearch.workflows.entry_points",
        lambda **_: [],
    )
    result = load_workflow_entries()
    assert result == []


def test_load_workflow_entries_with_metadata(monkeypatch) -> None:
    def get_meta() -> WorkflowEntry:
        return WorkflowEntry(id="deep", name="Deep", description="Deep research.")

    meta_ep = MagicMock()
    meta_ep.load.return_value = get_meta

    wf_ep = MagicMock()
    wf_ep.name = "deep"
    wf_ep.load.return_value = MagicMock()

    def mock_entry_points(group):
        if group == "webresearch.workflows.metadata":
            return [meta_ep]
        if group == "webresearch.workflows":
            return [wf_ep]
        return []

    monkeypatch.setattr("webresearch.workflows.entry_points", mock_entry_points)
    result = load_workflow_entries()
    assert len(result) == 1
    assert result[0].id == "deep"
    assert result[0].name == "Deep"


def test_load_workflow_entries_fallback_without_metadata(monkeypatch) -> None:
    wf_ep = MagicMock()
    wf_ep.name = "my_workflow"
    wf_ep.load.return_value = MagicMock()

    def mock_entry_points(group):
        if group == "webresearch.workflows.metadata":
            return []
        if group == "webresearch.workflows":
            return [wf_ep]
        return []

    monkeypatch.setattr("webresearch.workflows.entry_points", mock_entry_points)
    result = load_workflow_entries()
    assert len(result) == 1
    assert result[0].id == "my_workflow"
    assert result[0].name == "My Workflow"  # auto-title from "my_workflow"
    assert result[0].description == ""


def test_load_workflow_entries_metadata_wins_over_fallback(monkeypatch) -> None:
    def get_meta() -> WorkflowEntry:
        return WorkflowEntry(id="deep", name="Deep Research", description="Desc.")

    meta_ep = MagicMock()
    meta_ep.load.return_value = get_meta

    wf_ep = MagicMock()
    wf_ep.name = "deep"
    wf_ep.load.return_value = MagicMock()

    def mock_entry_points(group):
        if group == "webresearch.workflows.metadata":
            return [meta_ep]
        if group == "webresearch.workflows":
            return [wf_ep]
        return []

    monkeypatch.setattr("webresearch.workflows.entry_points", mock_entry_points)
    result = load_workflow_entries()
    assert len(result) == 1
    assert result[0].name == "Deep Research"  # metadata wins, no duplicate
