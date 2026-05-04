from __future__ import annotations

from functools import cache
from importlib.resources import files


@cache
def load_prompt(name: str) -> str:
    path = files("webresearch").joinpath("prompts", name)
    if not path.is_file():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    return path.read_text(encoding="utf-8")
