# P5-02 — `stream_workflow` async generator

**Phase:** 5 — Event stream
**Depends on:** P5-01, P4-01

## Goal
Wrap a workflow function so callers get an `AsyncIterator[WorkflowEvent]`. Wires the SDK's `Runner.run_streamed` into our event stream.

## Scope
- `async def stream_workflow(workflow_fn, input) -> AsyncIterator[WorkflowEvent]`.
- Internally:
  - Create an `asyncio.Queue[WorkflowEvent]`.
  - The workflow calls a `step(name)` async context manager (defined here) which emits `StepStarted` on enter and `StepCompleted`/`StepFailed` on exit, and replaces `Runner.run` with `Runner.run_streamed` for the duration. SDK events are translated:
    - `tool_call_item` start/end → `ToolStarted` / `ToolCompleted`.
    - `message_output_item` deltas → `OutputTextDelta` only when the active step is `output`.
    - The agent's final structured output is taken from `result.final_output_as(type_)`.
  - Workflow runs as a background task; events drain through the queue to the consumer.
- Iterator ends after `WorkflowCompleted` or `WorkflowFailed`.
- If consumer cancels, the workflow task is cancelled (cooperative cancellation throughout).

## Out of scope
- A non-streaming `run_workflow(...)` aggregator — trivial wrapper, can be added in `webresearch/__init__.py`.

## Files
- `webresearch/events/stream.py`
- `webresearch/events/step.py`  (the `step` context manager)
- `webresearch/__init__.py`  (re-export `stream_workflow`, `run_workflow`)
- `tests/events/test_stream_workflow.py`

## Acceptance
- [ ] Events arrive in the order they are emitted.
- [ ] Iterator ends cleanly on workflow completion.
- [ ] Cancelling the iterator cancels the workflow task within ≤ 1s.
- [ ] `OutputTextDelta` events arrive only during the output step; concatenating them reproduces `final.answer_markdown`.
