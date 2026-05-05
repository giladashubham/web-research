from __future__ import annotations

from functools import cache
from importlib.resources import files


@cache
def load_prompt(name: str, depth: str = "standard") -> str:
    path = files("webresearch.workflows.shared").joinpath("prompts", name)
    if not path.is_file():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    return path.read_text(encoding="utf-8").replace("{depth_extras}", load_depth_extras(depth))


@cache
def load_depth_extras(depth: str) -> str:
    path = files("webresearch").joinpath("prompts", "depth_extras", f"{depth}.md")
    if not path.is_file():
        raise FileNotFoundError(f"Depth prompt extras file not found: {path}")
    return path.read_text(encoding="utf-8").strip()
