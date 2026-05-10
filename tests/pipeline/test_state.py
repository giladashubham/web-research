from __future__ import annotations

from datetime import UTC, datetime

from webresearch.context import WorkflowContext
from webresearch.pipeline.state import PipelineState
from webresearch.types import Depth, WorkflowInput


def test_pipeline_state_defaults() -> None:
    wf_input = WorkflowInput(query="test query", depth=Depth.for_preset("standard"))
    now = datetime.now(UTC)
    state = PipelineState(
        input=wf_input,
        run_id="run_abc123",
        started_at=now,
        context=WorkflowContext(),
    )
    assert state.input.query == "test query"
    assert state.run_id == "run_abc123"
    assert state.started_at == now
    assert state.outputs == {}
    assert state.iteration_count == {}
    assert state.warnings == []


def test_pipeline_state_with_outputs() -> None:
    wf_input = WorkflowInput(query="q", depth=Depth.for_preset("quick"))
    state = PipelineState(
        input=wf_input,
        run_id="run_xyz",
        started_at=datetime.now(UTC),
        context=WorkflowContext(),
        outputs={"step1": {"result": "ok"}},
        iteration_count={"step1": 1},
        warnings=["test warning"],
    )
    assert state.outputs["step1"] == {"result": "ok"}
    assert state.iteration_count["step1"] == 1
    assert state.warnings == ["test warning"]


def test_pipeline_state_tracks_context() -> None:
    wf_input = WorkflowInput(query="q", depth=Depth.for_preset("deep"))
    ctx = WorkflowContext()
    ctx.cost_usd = 0.05
    ctx.input_tokens = 100
    ctx.output_tokens = 50
    state = PipelineState(
        input=wf_input,
        run_id="run_cost",
        started_at=datetime.now(UTC),
        context=ctx,
    )
    assert state.context.cost_usd == 0.05
    assert state.context.input_tokens == 100
    assert state.context.output_tokens == 50
