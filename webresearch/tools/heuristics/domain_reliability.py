from __future__ import annotations

from urllib.parse import urlsplit

MAJOR_NEWS_DOMAINS = {
    "apnews.com",
    "bbc.com",
    "nytimes.com",
    "reuters.com",
    "washingtonpost.com",
}

BLOG_HINTS = ("blog", "medium.com", "substack.com", "wordpress.com")


def domain_reliability_score(url: str) -> float:
    host = (urlsplit(url).hostname or "").casefold()
    if host.endswith(".gov") or host.endswith(".edu"):
        return 1.0
    if _is_vendor_official(host):
        return 0.85
    if _is_major_news(host):
        return 0.75
    if any(hint in host for hint in BLOG_HINTS):
        return 0.25
    return 0.5


def _is_vendor_official(host: str) -> bool:
    return host.startswith(("www.", "docs.", "developer.")) and not any(
        hint in host for hint in BLOG_HINTS
    )


def _is_major_news(host: str) -> bool:
    return any(host == domain or host.endswith(f".{domain}") for domain in MAJOR_NEWS_DOMAINS)
