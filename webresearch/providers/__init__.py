"""Raw I/O adapter layer.

Providers handle web search, HTTP fetching, HTML content extraction,
and URL discovery.  They contain no LLM concepts — only network calls
and content processing.
"""

from __future__ import annotations
