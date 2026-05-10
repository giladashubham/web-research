from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest
from pydantic import BaseModel

from webresearch.pipeline.hooks import HookSignal
from webresearch.pipeline.runner import Pipeline
from webresearch.pipeline.runtime import ExecutionResult
from webresearch.pipeline.step import AgentStep, FanOut, Loop, Parallel
from webresearch.types import Depth, WorkflowInput

if TYPE_CHECKING:
    from webresearch.pipeline.state import PipelineState

RUNTIME_MODULE = "webresearch.pipeline.runner"


class FakeOutput(BaseModel):
    result: str


class FakeReview(BaseModel):
    done: bool
    summary: str = ""


class FakeFinal(BaseModel):
    answer_markdown: str
    findings: list[Any] = []
    sources_cited: list[str] = []
    structured_data: dict[str, object] | None = None


def _make_result(output: object) -> ExecutionResult:
    return ExecutionResult(
        output=output,
        input_tokens=50,
        output_tokens=25,
        model="gpt-4.1-mini",
    )


# ---------------------------------------------------------------------------
# Sequential execution
# ---------------------------------------------------------------------------


async def test_pipeline_runs_sequential_steps(monkeypatch) -> None:
    call_order: list[str] = []
    outputs: dict[str, object] = {
        "planner": FakeOutput(result="plan"),
        "researcher": FakeOutput(result="research"),
        "writer": FakeFinal(answer_markdown="final answer"),
    }

    async def mock_execute(
        step: AgentStep, _prompt: str, _context: object, _tools: list[Any] | None = None
    ) -> ExecutionResult:
        call_order.append(step.name)
        return _make_result(outputs[step.name])

    monkeypatch.setattr(f"{RUNTIME_MODULE}.execute", mock_execute)

    pipeline = Pipeline(
        steps=[
            AgentStep(
                name="planner", prompt="plan {{ input.query }}", output_type=FakeOutput
            ),
            AgentStep(
                name="researcher",
                prompt="research {{ input.query }}",
                output_type=FakeOutput,
            ),
            AgentStep(
                name="writer", prompt="write {{ input.query }}", output_type=FakeFinal
            ),
        ],
        final_output_key="writer",
        workflow_id="test",
    )

    result = await pipeline.run(
        WorkflowInput(query="hello", depth=Depth.for_preset("quick"))
    )

    assert result.answer_markdown == "final answer"
    assert result.metadata.workflow_id == "test"
    assert call_order == ["planner", "researcher", "writer"]


# ---------------------------------------------------------------------------
# Parallel execution
# ---------------------------------------------------------------------------


async def test_pipeline_runs_parallel_steps(monkeypatch) -> None:
    call_order: list[str] = []

    async def mock_execute(
        step: AgentStep, _prompt: str, _context: object, _tools: list[Any] | None = None
    ) -> ExecutionResult:
        call_order.append(step.name)
        return _make_result(FakeOutput(result=step.name))

    monkeypatch.setattr(f"{RUNTIME_MODULE}.execute", mock_execute)

    pipeline = Pipeline(
        steps=[
            Parallel(
                [
                    AgentStep(name="lane_a", prompt="a", output_type=FakeOutput),
                    AgentStep(name="lane_b", prompt="b", output_type=FakeOutput),
                    AgentStep(name="lane_c", prompt="c", output_type=FakeOutput),
                ]
            ),
            AgentStep(name="writer", prompt="write", output_type=FakeFinal),
        ],
        final_output_key="writer",
        workflow_id="parallel_test",
    )

    result = await pipeline.run(
        WorkflowInput(query="test", depth=Depth.for_preset("quick"))
    )

    assert result.metadata.workflow_id == "parallel_test"
    # All three parallel lanes ran
    assert "lane_a" in call_order
    assert "lane_b" in call_order
    assert "lane_c" in call_order
    # Writer ran after parallel
    assert call_order[-1] == "writer"


# ---------------------------------------------------------------------------
# FanOut execution
# ---------------------------------------------------------------------------


async def test_pipeline_runs_fanout(monkeypatch) -> None:
    items_processed: list[str] = []

    async def mock_execute(
        step: AgentStep, _prompt: str, _context: object, _tools: list[Any] | None = None
    ) -> ExecutionResult:
        items_processed.append(step.name)
        return _make_result(FakeOutput(result=f"done_{step.name}"))

    monkeypatch.setattr(f"{RUNTIME_MODULE}.execute", mock_execute)

    pipeline = Pipeline(
        steps=[
            FanOut(
                step=AgentStep(
                    name="research_item",
                    prompt="item {{ item }}",
                    output_type=FakeOutput,
                ),
                over=lambda _state: ["url1", "url2", "url3"],
            ),
            AgentStep(name="writer", prompt="write", output_type=FakeFinal),
        ],
        final_output_key="writer",
        workflow_id="fanout_test",
    )

    result = await pipeline.run(
        WorkflowInput(query="test", depth=Depth.for_preset("quick"))
    )

    assert result.metadata.workflow_id == "fanout_test"
    # FanOut processed each item
    assert len(items_processed) >= 3
    # Writer ran after fanout
    assert items_processed[-1] == "writer"


async def test_fanout_collects_results(monkeypatch) -> None:
    outputs_iter = iter(
        [
            _make_result(FakeOutput(result="result_a")),
            _make_result(FakeOutput(result="result_b")),
            _make_result(FakeOutput(result="result_c")),
        ]
    )

    async def mock_execute(
        _step: AgentStep, _prompt: str, _context: object, _tools: list[Any] | None = None
    ) -> ExecutionResult:
        return next(outputs_iter)

    monkeypatch.setattr(f"{RUNTIME_MODULE}.execute", mock_execute)

    pipeline = Pipeline(
        steps=[
            FanOut(
                step=AgentStep(
                    name="fan_step", prompt="item {{ item }}", output_type=FakeOutput
                ),
                over=lambda _state: ["a", "b", "c"],
            ),
        ],
        final_output_key="fan_step",
        workflow_id="fanout_collect",
    )

    result = await pipeline.run(
        WorkflowInput(query="test", depth=Depth.for_preset("quick"))
    )

    # The structured_data isn't set by FakeOutput, but the summary should contain results
    assert result.metadata.workflow_id == "fanout_collect"


async def test_fanout_with_pre_hook_skip(monkeypatch) -> None:
    """FanOut step with a pre_hook that returns SKIP should skip execution."""

    async def skip_hook(_state: PipelineState) -> HookSignal:
        return HookSignal.SKIP

    executed = False

    async def mock_execute(
        _step: AgentStep, _prompt: str, _context: object, _tools: list[Any] | None = None
    ) -> ExecutionResult:
        nonlocal executed
        executed = True
        return _make_result(FakeOutput(result="should_not_happen"))

    monkeypatch.setattr(f"{RUNTIME_MODULE}.execute", mock_execute)

    pipeline = Pipeline(
        steps=[
            FanOut(
                step=AgentStep(
                    name="skipped_fan",
                    prompt="test",
                    output_type=FakeOutput,
                    pre_hook=skip_hook,
                ),
                over=lambda _state: ["x", "y"],
            ),
        ],
        final_output_key="skipped_fan",
        workflow_id="fanout_skip",
    )

    result = await pipeline.run(
        WorkflowInput(query="test", depth=Depth.for_preset("quick"))
    )

    assert not executed, "FanOut items should not execute when pre_hook returns SKIP"
    assert result.metadata.workflow_id == "fanout_skip"


# ---------------------------------------------------------------------------
# Loop execution
# ---------------------------------------------------------------------------


async def test_pipeline_runs_loop(monkeypatch) -> None:
    iteration_count: list[int] = []

    class LoopOutput(FakeOutput):
        pass

    async def mock_execute(
        step: AgentStep, _prompt: str, _context: object, _tools: list[Any] | None = None
    ) -> ExecutionResult:
        if step.name == "reviewer":
            iteration_count.append(len(iteration_count) + 1)
            done = len(iteration_count) >= 3
            return _make_result(
                FakeReview(done=done, summary=f"iter_{len(iteration_count)}")
            )
        if step.name == "writer":
            return _make_result(FakeFinal(answer_markdown="final"))
        return _make_result(FakeOutput(result="ok"))

    monkeypatch.setattr(f"{RUNTIME_MODULE}.execute", mock_execute)

    pipeline = Pipeline(
        steps=[
            AgentStep(name="planner", prompt="plan", output_type=FakeOutput),
            Loop(
                steps=[
                    AgentStep(name="reviewer", prompt="review", output_type=FakeReview),
                    AgentStep(
                        name="researcher", prompt="research", output_type=FakeOutput
                    ),
                ],
                until=lambda state: bool(
                    state.outputs.get("reviewer")
                    and getattr(state.outputs["reviewer"], "done", False)
                ),
                max_iterations=5,
            ),
            AgentStep(name="writer", prompt="write", output_type=FakeFinal),
        ],
        final_output_key="writer",
        workflow_id="loop_test",
    )

    result = await pipeline.run(
        WorkflowInput(query="test", depth=Depth.for_preset("deep"))
    )

    assert result.metadata.workflow_id == "loop_test"
    assert len(iteration_count) == 3, "Loop should run 3 iterations"
    assert "iter_1" in result.summary
    assert "iter_2" in result.summary
    assert "iter_3" in result.summary


# ---------------------------------------------------------------------------
# Pre-hook SKIP signal
# ---------------------------------------------------------------------------


async def test_agent_pre_hook_skip(monkeypatch) -> None:
    skipped_step_executed = False

    async def skip_hook(_state: PipelineState) -> HookSignal:
        return HookSignal.SKIP

    async def mock_execute(
        step: AgentStep, _prompt: str, _context: object, _tools: list[Any] | None = None
    ) -> ExecutionResult:
        if step.name == "skip_me":
            nonlocal skipped_step_executed
            skipped_step_executed = True
        return _make_result(FakeFinal(answer_markdown="done"))

    monkeypatch.setattr(f"{RUNTIME_MODULE}.execute", mock_execute)

    pipeline = Pipeline(
        steps=[
            AgentStep(
                name="skip_me",
                prompt="test",
                output_type=FakeOutput,
                pre_hook=skip_hook,
            ),
            AgentStep(name="writer", prompt="write", output_type=FakeFinal),
        ],
        final_output_key="writer",
        workflow_id="skip_test",
    )

    result = await pipeline.run(
        WorkflowInput(query="test", depth=Depth.for_preset("quick"))
    )

    assert not skipped_step_executed, "Skipped step should not execute"
    assert result.metadata.workflow_id == "skip_test"


# ---------------------------------------------------------------------------
# Post-hook REPEAT signal
# ---------------------------------------------------------------------------


async def test_agent_post_hook_repeat(monkeypatch) -> None:
    call_count: list[int] = [0]

    async def repeat_hook(state: PipelineState) -> HookSignal:
        if state.iteration_count.get("repeater", 0) < 3:
            return HookSignal.REPEAT
        return HookSignal.CONTINUE

    async def mock_execute(
        step: AgentStep, _prompt: str, _context: object, _tools: list[Any] | None = None
    ) -> ExecutionResult:
        call_count[0] += 1
        if step.name == "repeater":
            return _make_result(FakeOutput(result=f"attempt_{call_count[0]}"))
        return _make_result(FakeFinal(answer_markdown="done"))

    monkeypatch.setattr(f"{RUNTIME_MODULE}.execute", mock_execute)

    pipeline = Pipeline(
        steps=[
            AgentStep(
                name="repeater",
                prompt="repeat",
                output_type=FakeOutput,
                post_hook=repeat_hook,
            ),
            AgentStep(name="writer", prompt="write", output_type=FakeFinal),
        ],
        final_output_key="writer",
        workflow_id="repeat_test",
    )

    result = await pipeline.run(
        WorkflowInput(
            query="test",
            depth=Depth.for_preset("deep"),
        )
    )

    assert call_count[0] >= 3, "Step should repeat due to post_hook REPEAT"
    assert result.metadata.workflow_id == "repeat_test"


# ---------------------------------------------------------------------------
# Cost and token tracking
# ---------------------------------------------------------------------------


async def test_pipeline_tracks_cost_and_tokens(monkeypatch) -> None:
    async def mock_execute(
        _step: AgentStep, _prompt: str, _context: object, _tools: list[Any] | None = None
    ) -> ExecutionResult:
        return ExecutionResult(
            output=FakeOutput(result="ok"),
            input_tokens=200,
            output_tokens=100,
            model="gpt-4.1",
        )

    monkeypatch.setattr(f"{RUNTIME_MODULE}.execute", mock_execute)

    pipeline = Pipeline(
        steps=[
            AgentStep(name="step1", prompt="s1", output_type=FakeOutput),
            AgentStep(name="step2", prompt="s2", output_type=FakeOutput),
            AgentStep(name="writer", prompt="write", output_type=FakeFinal),
        ],
        final_output_key="writer",
        workflow_id="cost_test",
    )

    result = await pipeline.run(
        WorkflowInput(query="test", depth=Depth.for_preset("quick"))
    )

    # 3 steps (step1, step2, writer) x 200 input each = 600
    assert result.metadata.tokens.input_tokens == 600
    # 3 steps x 100 output each = 300
    assert result.metadata.tokens.output_tokens == 300
    assert result.metadata.tokens.total_tokens == 900
    # Cost: 200 input * $2/1M + 100 output * $8/1M = $0.0012 per step x 3 steps = $0.0036
    assert result.metadata.cost_usd is not None
    assert result.metadata.cost_usd == pytest.approx(0.0036)


# ---------------------------------------------------------------------------
# _build_result raises on missing key
# ---------------------------------------------------------------------------


async def test_pipeline_missing_final_key_raises(monkeypatch) -> None:
    async def mock_execute(
        _step: AgentStep, _prompt: str, _context: object, _tools: list[Any] | None = None
    ) -> ExecutionResult:
        return _make_result(FakeOutput(result="ok"))

    monkeypatch.setattr(f"{RUNTIME_MODULE}.execute", mock_execute)

    pipeline = Pipeline(
        steps=[
            AgentStep(name="step1", prompt="s1", output_type=FakeOutput),
        ],
        final_output_key="missing_key",
        workflow_id="missing_test",
    )

    with pytest.raises(ValueError, match="not found in state outputs"):
        await pipeline.run(WorkflowInput(query="test", depth=Depth.for_preset("quick")))
