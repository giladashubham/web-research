from __future__ import annotations

from time import perf_counter
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter


def event_timestamp() -> float:
    return perf_counter()


class EventModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    timestamp: float = Field(default_factory=event_timestamp)


class WorkflowStarted(EventModel):
    kind: Literal["workflow_started"] = "workflow_started"
    workflow_id: str


class WorkflowCompleted(EventModel):
    kind: Literal["workflow_completed"] = "workflow_completed"
    workflow_id: str


class WorkflowFailed(EventModel):
    kind: Literal["workflow_failed"] = "workflow_failed"
    workflow_id: str
    error: str


class StepStarted(EventModel):
    kind: Literal["step_started"] = "step_started"
    step: str


class StepCompleted(EventModel):
    kind: Literal["step_completed"] = "step_completed"
    step: str
    cost_usd: float | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None


class StepSkipped(EventModel):
    kind: Literal["step_skipped"] = "step_skipped"
    step: str
    reason: str


class StepFailed(EventModel):
    kind: Literal["step_failed"] = "step_failed"
    step: str
    error: str


class LoopIteration(EventModel):
    kind: Literal["loop_iteration"] = "loop_iteration"
    loop: str
    iteration: int = Field(ge=1)


class AgentStarted(EventModel):
    kind: Literal["agent_started"] = "agent_started"
    step: str
    agent_name: str


class AgentCompleted(EventModel):
    kind: Literal["agent_completed"] = "agent_completed"
    step: str


class AgentFailed(EventModel):
    kind: Literal["agent_failed"] = "agent_failed"
    step: str
    error: str


class ToolCall(EventModel):
    kind: Literal["tool_call"] = "tool_call"
    step: str
    tool_name: str
    call_id: str
    arguments: dict[str, object]


class ToolResult(EventModel):
    kind: Literal["tool_result"] = "tool_result"
    step: str
    tool_name: str
    call_id: str
    result: object


class ToolFailed(EventModel):
    kind: Literal["tool_failed"] = "tool_failed"
    step: str
    tool_name: str
    call_id: str
    error: str


class ArtifactAdded(EventModel):
    kind: Literal["artifact_added"] = "artifact_added"
    artifact_id: str
    artifact_kind: str


class SourceAdded(EventModel):
    kind: Literal["source_added"] = "source_added"
    source_id: str
    url: str


class OutputTextDelta(EventModel):
    kind: Literal["output_text_delta"] = "output_text_delta"
    delta: str


class Warning(EventModel):
    kind: Literal["warning"] = "warning"
    message: str


WorkflowEvent = Annotated[
    WorkflowStarted
    | WorkflowCompleted
    | WorkflowFailed
    | StepStarted
    | StepCompleted
    | StepSkipped
    | StepFailed
    | LoopIteration
    | AgentStarted
    | AgentCompleted
    | AgentFailed
    | ToolCall
    | ToolResult
    | ToolFailed
    | ArtifactAdded
    | SourceAdded
    | OutputTextDelta
    | Warning,
    Field(discriminator="kind"),
]

WorkflowEventAdapter: TypeAdapter[WorkflowEvent] = TypeAdapter(WorkflowEvent)
