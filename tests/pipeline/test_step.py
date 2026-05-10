from __future__ import annotations

from pydantic import BaseModel

from webresearch.pipeline.hooks import HookSignal
from webresearch.pipeline.step import AgentStep, FanOut, Loop, Parallel


class FakeOutput(BaseModel):
    result: str


def test_agent_step_defaults() -> None:
    step = AgentStep(name="test", prompt="Do {{ input.query }}", output_type=FakeOutput)
    assert step.name == "test"
    assert step.prompt == "Do {{ input.query }}"
    assert step.output_type is FakeOutput
    assert step.tools == []
    assert step.pre_hook is None
    assert step.post_hook is None
    assert step.max_turns == 50
    assert step.strict_schema is True


def test_agent_step_with_tools() -> None:
    step = AgentStep(
        name="test",
        prompt="test",
        output_type=FakeOutput,
        tools=["tool1"],
        max_turns=10,
        strict_schema=False,
    )
    assert step.tools == ["tool1"]
    assert step.max_turns == 10
    assert step.strict_schema is False


def test_parallel_holds_steps() -> None:
    s1 = AgentStep(name="a", prompt="a", output_type=FakeOutput)
    s2 = AgentStep(name="b", prompt="b", output_type=FakeOutput)
    par = Parallel(steps=[s1, s2])
    assert len(par.steps) == 2
    assert par.steps[0].name == "a"
    assert par.steps[1].name == "b"


def test_fanout_holds_step_and_over() -> None:
    inner = AgentStep(name="fan", prompt="item {{ item }}", output_type=FakeOutput)
    fan = FanOut(step=inner, over=lambda _s: [1, 2, 3])
    assert fan.step.name == "fan"
    assert fan.over(None) == [1, 2, 3]


def test_loop_holds_steps_and_condition() -> None:
    s1 = AgentStep(name="step1", prompt="step1", output_type=FakeOutput)
    s2 = AgentStep(name="step2", prompt="step2", output_type=FakeOutput)
    loop = Loop(steps=[s1, s2], until=lambda _s: True, max_iterations=5)
    assert len(loop.steps) == 2
    assert loop.max_iterations == 5
    assert loop.until(None) is True


def test_hook_signal_values() -> None:
    assert HookSignal.CONTINUE.value == "continue"
    assert HookSignal.SKIP.value == "skip"
    assert HookSignal.REPEAT.value == "repeat"
