from __future__ import annotations

from agents import RunContextWrapper, function_tool

# Re-export the LLM framework's tool decorator and context wrapper so
# workflow tools.py files never import from the framework directly.
# Swapping the runtime means changing these re-exports only.

__all__ = ["function_tool", "RunContextWrapper"]
