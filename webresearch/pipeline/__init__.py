from __future__ import annotations

from agents import RunContextWrapper, function_tool

from webresearch.context import WorkflowContext

# Re-export the LLM framework's tool decorator and context wrapper so
# workflow tools.py files never import from the framework directly.
# Swapping the runtime means changing these re-exports only.

ToolContext = RunContextWrapper[WorkflowContext]

__all__ = ["function_tool", "RunContextWrapper", "ToolContext"]
