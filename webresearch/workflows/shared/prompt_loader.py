from __future__ import annotations

from functools import cache
from importlib.resources import files


@cache
def load_shared_prompt(name: str, workflow_id: str) -> str:
    path = files("webresearch.workflows.shared") / "prompts" / name
    if not path.is_file():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    return path.read_text(encoding="utf-8").replace(
        "{depth_extras}", load_depth_extras(workflow_id)
    )


@cache
def load_workflow_prompt(workflow_id: str, name: str) -> str:
    path = files(f"webresearch.workflows.{workflow_id}") / "prompts" / name
    if not path.is_file():
        raise FileNotFoundError(f"Workflow prompt file not found: {path}")
    return path.read_text(encoding="utf-8").strip()


@cache
def load_depth_extras(workflow_id: str) -> str:
    return load_workflow_prompt(workflow_id, "depth_extras.md")
