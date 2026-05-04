from __future__ import annotations

from functools import cache

from dotenv import find_dotenv, load_dotenv


@cache
def load_environment() -> None:
    load_dotenv(find_dotenv(usecwd=True), override=False)
