from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

from webresearch.pipeline.hooks import PostHook, PreHook

if TYPE_CHECKING:
    from webresearch.pipeline.state import PipelineState


@dataclass
class AgentStep:
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
    steps: list[AgentStep]


@dataclass
class FanOut:
    step: AgentStep
    over: Callable[["PipelineState"], list[Any]]


@dataclass
class Loop:
    steps: list[AgentStep]
    until: Callable[["PipelineState"], bool]
    max_iterations: int | None = None
