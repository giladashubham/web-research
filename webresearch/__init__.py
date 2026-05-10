"""Web Research — Python SDK for LLM-powered web research workflows.

Usage::

    from webresearch import WorkflowInput, Depth, load_workflows, run_workflow

    workflows = load_workflows()
    result = await run_workflow(
        workflows["deep"],
        WorkflowInput(query="What is the current Node.js LTS version?"),
    )
    print(result.answer_markdown)
"""

from __future__ import annotations

from webresearch.env import load_environment
from webresearch.events.stream import run_workflow, stream_workflow
from webresearch.types import (
    Depth,
    DepthPreset,
    WorkflowFn,
    WorkflowInput,
    WorkflowResult,
)
from webresearch.workflows import WorkflowEntry, load_workflows

__all__ = [
    "Depth",
    "DepthPreset",
    "WorkflowEntry",
    "WorkflowFn",
    "WorkflowInput",
    "WorkflowResult",
    "load_environment",
    "load_workflows",
    "run_workflow",
    "stream_workflow",
]
