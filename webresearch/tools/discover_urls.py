from __future__ import annotations

import urllib.parse
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from webresearch.sources.url_normalize import normalize_url
from webresearch.tools.fetch_url import fetch_url
from webresearch.types import UrlsByCategory

if TYPE_CHECKING:
    from webresearch.context import WorkflowContext

_SITEMAP_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

CATEGORY_PATTERNS: dict[str, list[str]] = {
    "docs": ["docs", "documentation", "reference", "developers", "developer", "guides", "guide", "tutorials", "sdk"],
    "api": ["api", "api-reference", "openapi", "swagger", "graphql"],
    "changelog": ["changelog", "release-notes", "releases", "whats-new", "updates"],
    "pricing": ["pricing", "plans", "packages"],
    "security": ["security", "trust", "compliance"],
    "customers": ["customers", "case-studies", "success-stories", "testimonials", "customers"],
    "blog": ["blog", "engineering", "tech", "news"],
    "careers": ["careers", "jobs", "hiring"],
}

CANONICAL_PROBES: dict[str, list[str]] = {
    "docs": ["/docs", "/documentation", "/developers"],
    "api": ["/api", "/api-reference"],
    "changelog": ["/changelog", "/release-notes", "/releases"],
    "pricing": ["/pricing", "/plans"],
    "security": ["/security", "/trust"],
    "customers": ["/customers", "/case-studies"],
    "blog": ["/blog", "/engineering"],
    "careers": ["/careers", "/jobs"],
}

WELL_KNOWN_PATHS = ["/.well-known/security.txt", "/llms.txt", "/robots.txt"]


class DiscoveredUrls(BaseModel):
    model_config = ConfigDict(extra="forbid")

    seed_url: str
    by_category: UrlsByCategory


class _LinkExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            for attr, value in attrs:
                if attr == "href" and value:
                    self.links.append(value)


def _categorize(url: str) -> str:
    path = urllib.parse.urlparse(url).path.lower()
    segments = [s for s in path.split("/") if s]
    for category, patterns in CATEGORY_PATTERNS.items():
        for segment in segments:
            if segment in patterns:
                return category
        for pattern in patterns:
            if path.startswith("/" + pattern):
                return category
    return "other"


def _same_origin(base: str, url: str) -> bool:
    b = urllib.parse.urlparse(base)
    u = urllib.parse.urlparse(url)
    if u.scheme and u.netloc:
        return u.netloc == b.netloc
    return True


def _base(url: str) -> str:
    p = urllib.parse.urlparse(url)
    return f"{p.scheme}://{p.netloc}"


def _try_normalize(url: str) -> str | None:
    try:
        return normalize_url(url)
    except ValueError:
        return None


async def discover_urls(ctx: WorkflowContext, seed_url: str) -> DiscoveredUrls:
    """Expand a seed URL into categorised high-value pages on the same domain.

    Priority: sitemap.xml first (structured), then anchor links from homepage,
    then targeted canonical probes for any still-empty categories.
    """
    normalized_seed = _try_normalize(seed_url)
    if normalized_seed is None:
        return DiscoveredUrls(seed_url=seed_url, by_category=UrlsByCategory())

    base = _base(normalized_seed)
    found: dict[str, set[str]] = {cat: set() for cat in list(CATEGORY_PATTERNS.keys()) + ["other"]}

    # Step 1: sitemap.xml — most reliable structured source
    sitemap_url = base + "/sitemap.xml"
    sitemap_result = await fetch_url(ctx, sitemap_url)
    if sitemap_result.status == "fetched":
        page = ctx.pages.get(sitemap_url) or ctx.pages.get(_try_normalize(sitemap_url) or "")
        if page:
            try:
                root = ET.fromstring(page.body)
                for loc in root.findall(".//sm:loc", _SITEMAP_NS):
                    if loc.text:
                        resolved = _try_normalize(loc.text)
                        if resolved and _same_origin(normalized_seed, loc.text):
                            found[_categorize(resolved)].add(resolved)
            except ET.ParseError:
                pass

    # Step 2: anchor links from the seed page itself
    seed_result = await fetch_url(ctx, normalized_seed)
    if seed_result.status == "fetched":
        page = ctx.pages.get(normalized_seed)
        if page:
            parser = _LinkExtractor()
            parser.feed(page.body)
            for href in parser.links:
                if not href or href.startswith(("#", "mailto:", "javascript:")):
                    continue
                resolved_raw = urllib.parse.urljoin(normalized_seed, href)
                if not _same_origin(normalized_seed, resolved_raw):
                    continue
                resolved = _try_normalize(resolved_raw)
                if resolved:
                    found[_categorize(resolved)].add(resolved)

    # Step 3: canonical path probes for categories still empty after steps 1-2
    for category, paths in CANONICAL_PROBES.items():
        if found.get(category):
            continue
        for path in paths:
            probe_url = _try_normalize(base + path)
            if probe_url is None:
                continue
            result = await fetch_url(ctx, probe_url)
            if result.status == "fetched":
                found[category].add(probe_url)
                break

    # Step 4: well-known paths always worth checking
    for path in WELL_KNOWN_PATHS:
        probe_url = _try_normalize(base + path)
        if probe_url:
            result = await fetch_url(ctx, probe_url)
            if result.status == "fetched":
                found["other"].add(probe_url)

    return DiscoveredUrls(
        seed_url=normalized_seed,
        by_category=UrlsByCategory(
            docs=sorted(found["docs"]),
            api=sorted(found["api"]),
            changelog=sorted(found["changelog"]),
            pricing=sorted(found["pricing"]),
            security=sorted(found["security"]),
            customers=sorted(found["customers"]),
            blog=sorted(found["blog"]),
            careers=sorted(found["careers"]),
            other=sorted(found["other"]),
        ),
    )
