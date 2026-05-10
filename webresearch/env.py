"""Environment-variable loading via python-dotenv.

Call :func:`load_environment` once (it is cached) to load ``.env`` files.
The CLI entry point calls this automatically; library consumers may call it
explicitly when needed.
"""

from __future__ import annotations

from functools import cache

from dotenv import find_dotenv, load_dotenv


@cache
def load_environment() -> None:
    """Load ``.env`` file from the current working directory (or parents).

    Existing shell environment variables take precedence (``override=False``).
    The result is cached so repeated calls are cheap.
    """
    load_dotenv(find_dotenv(usecwd=True), override=False)
