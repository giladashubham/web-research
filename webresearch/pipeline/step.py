"""Pipeline step types.

Defines the four step primitives that workflows compose into a pipeline:

* :class:`AgentStep` — single LLM agent call.
* :class:`Parallel` — run multiple agents concurrently.
* :class:`FanOut` — run one agent per item in a dynamic list.
* :class:`Loop` — repeat steps until a condition is met.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

    from pydantic import BaseModel

    from webresearch.pipeline.hooks import PostHook, PreHook
    from webresearch.pipeline.state import PipelineState


@dataclass
class AgentStep:
    """A single LLM agent step in a pipeline.

    Parameters:
        name: Unique step identifier (used in ``state.outputs``).
        prompt: Jinja2 template string rendered with pipeline state.
        output_type: Pydantic model for structured output parsing.
        tools: List of ``function_tool``-decorated async functions.
        pre_hook: Called before execution; can return ``SKIP``.
        post_hook: Called after execution; can return ``REPEAT``.
        max_turns: Maximum LLM turns (tool calls + responses).
        strict_schema: Whether to enforce strict JSON schema on output.
    """

    name: str
    prompt: str
    output_type: type[BaseModel]
    tools: list[Any] = field(default_factory=list)
    pre_hook: PreHook | None = None
    post_hook: PostHook | None = None
    max_turns: int = 50
    strict_schema: bool = True


@dataclass
class Parallel:
    """Run multiple :class:`AgentStep` instances concurrently.

    All steps must complete before the pipeline continues.
    """

    steps: list[AgentStep]


@dataclass
class FanOut:
    """Run one agent per item in a dynamic list.

    ``over`` is a callable that receives :class:`PipelineState` and returns
    a list of items.  One agent instance is launched per item; all run
    concurrently.  Results are collected into a list under the step name.
    """

    step: AgentStep
    over: Callable[[PipelineState], list[Any]]


@dataclass
class Loop:
    """Repeat a sequence of steps until a condition is met.

    ``until`` is called after every iteration.  When it returns ``True``
    the loop exits.  ``max_iterations`` defaults to
    ``input.depth.max_rounds`` if not set.
    """

    steps: list[AgentStep]
    until: Callable[[PipelineState], bool]
    max_iterations: int | None = None
