"""Pipeline execution engine.

Re-exports :func:`function_tool`, :class:`RunContextWrapper`, and
:class:`ToolContext` so that workflow ``tools.py`` files never import
from the LLM framework directly.  Swapping the runtime means changing
these re-exports only.
"""

from __future__ import annotations

from agents import RunContextWrapper, function_tool

from webresearch.context import WorkflowContext

# Re-export the LLM framework's tool decorator and context wrapper so
# workflow tools.py files never import from the framework directly.
# Swapping the runtime means changing these re-exports only.

ToolContext = RunContextWrapper[WorkflowContext]

__all__ = ["RunContextWrapper", "ToolContext", "function_tool"]
