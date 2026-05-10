from __future__ import annotations

import pytest

from webresearch.events.types import (
    AgentCompleted,
    AgentFailed,
    AgentStarted,
    ArtifactAdded,
    LoopIteration,
    OutputTextDelta,
    SourceAdded,
    StepCompleted,
    StepFailed,
    StepSkipped,
    StepStarted,
    ToolCall,
    ToolFailed,
    ToolResult,
    Warning,
    WorkflowCompleted,
    WorkflowEventAdapter,
    WorkflowFailed,
    WorkflowStarted,
)


@pytest.mark.parametrize(
    "event",
    [
        WorkflowStarted(run_id="run_1", workflow_id="standard"),
        WorkflowCompleted(run_id="run_1", workflow_id="standard"),
        WorkflowFailed(run_id="run_1", workflow_id="standard", error="failed"),
        StepStarted(run_id="run_1", step="planner"),
        StepCompleted(run_id="run_1", step="planner"),
        StepSkipped(run_id="run_1", step="gap", reason="No critical gaps"),
        StepFailed(run_id="run_1", step="planner", error="failed"),
        LoopIteration(run_id="run_1", loop="gap", iteration=1),
        AgentStarted(run_id="run_1", step="research", agent_name="researcher"),
        AgentCompleted(run_id="run_1", step="research"),
        AgentFailed(run_id="run_1", step="research", error="boom"),
        ToolCall(
            run_id="run_1",
            step="research",
            tool_name="search_web",
            call_id="call_1",
            arguments={"q": "test"},
        ),
        ToolResult(
            run_id="run_1",
            step="research",
            tool_name="search_web",
            call_id="call_1",
            result={"results": []},
        ),
        ToolFailed(
            run_id="run_1",
            step="research",
            tool_name="search_web",
            call_id="call_1",
            error="timeout",
        ),
        ArtifactAdded(run_id="run_1", artifact_id="artifact_1", artifact_kind="evidence"),
        SourceAdded(run_id="run_1", source_id="src_1", url="https://example.com"),
        OutputTextDelta(run_id="run_1", delta="hello"),
        Warning(run_id="run_1", message="warning"),
    ],
)
def test_event_variants_round_trip_via_json(event) -> None:
    parsed = WorkflowEventAdapter.validate_json(event.model_dump_json())

    assert parsed == event


def test_discriminated_parsing_uses_kind() -> None:
    parsed = WorkflowEventAdapter.validate_python(
        {
            "kind": "step_started",
            "run_id": "run_1",
            "timestamp": 1.5,
            "step": "planner",
        }
    )

    assert isinstance(parsed, StepStarted)
    assert parsed.step == "planner"
