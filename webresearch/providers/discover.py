from __future__ import annotations

import urllib.parse
from html.parser import HTMLParser
from typing import TYPE_CHECKING

import defusedxml.ElementTree as ET  # type: ignore[import-untyped]
from pydantic import BaseModel, ConfigDict, Field

from webresearch.providers.fetch import FetchProvider
from webresearch.sources.url_normalize import normalize_url

if TYPE_CHECKING:
    from webresearch.context import WorkflowContext


class UrlsByCategory(BaseModel):
    model_config = ConfigDict(extra="forbid")

    docs: list[str] = Field(default_factory=list)
    api: list[str] = Field(default_factory=list)
    changelog: list[str] = Field(default_factory=list)
    pricing: list[str] = Field(default_factory=list)
    security: list[str] = Field(default_factory=list)
    customers: list[str] = Field(default_factory=list)
    blog: list[str] = Field(default_factory=list)
    careers: list[str] = Field(default_factory=list)
    other: list[str] = Field(default_factory=list)


_SITEMAP_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

CATEGORY_PATTERNS: dict[str, list[str]] = {
    "docs": [
        "docs",
        "documentation",
        "reference",
        "developers",
        "developer",
        "guides",
        "guide",
        "tutorials",
        "sdk",
    ],
    "api": ["api", "api-reference", "openapi", "swagger", "graphql"],
    "changelog": ["changelog", "release-notes", "releases", "whats-new", "updates"],
    "pricing": ["pricing", "plans", "packages"],
    "security": ["security", "trust", "compliance"],
    "customers": ["customers", "case-studies", "success-stories", "testimonials"],
    "blog": ["blog", "engineering", "tech", "news"],
    "careers": ["careers", "jobs", "hiring"],
}

COMMON_SECOND_LEVEL_DOMAINS = {"ac", "co", "com", "edu", "gov", "net", "org"}

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
CATEGORY_LIMITS = {
    "docs": 50,
    "api": 30,
    "changelog": 40,
    "pricing": 20,
    "security": 30,
    "customers": 20,
    "blog": 20,
    "careers": 20,
    "other": 40,
}
URL_PRIORITY_TERMS: dict[str, list[str]] = {
    "docs": [
        "current/index.html",
        "getting-started/architecture",
        "getting-started/components",
        "installation-guide/index",
        "user-manual/capabilities",
        "cloud-service/index",
    ],
    "api": [
        "user-manual/api/index",
        "user-manual/api/reference",
        "user-manual/api/getting-started",
        "cloud-service/apis/index",
        "cloud-service/apis/reference",
    ],
    "changelog": [
        "release-notes/index.html",
        "release-notes/index-4x",
        "release-4-14",
        "release-4-13",
        "github.com/wazuh/wazuh/releases",
    ],
    "security": [
        "security",
        "compliance/index",
        "compliance/nist/index",
        "compliance/pci-dss/index",
        "compliance/hipaa/index",
        "compliance/gdpr/index",
    ],
}


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
    parsed = urllib.parse.urlparse(url)
    path = parsed.path.lower()
    segments = [s for s in path.split("/") if s]
    for category, patterns in CATEGORY_PATTERNS.items():
        for segment in segments:
            if segment in patterns:
                return category
        for pattern in patterns:
            if path.startswith("/" + pattern):
                return category
    host_segments = [s for s in parsed.netloc.lower().split(".") if s and s != "www"]
    for category, patterns in CATEGORY_PATTERNS.items():
        for segment in host_segments:
            if segment in patterns:
                return category
    return "other"


def _same_origin(base: str, url: str) -> bool:
    b = urllib.parse.urlparse(base)
    u = urllib.parse.urlparse(url)
    if u.scheme and u.netloc:
        return u.netloc == b.netloc
    return True


def _registrable_domain(host: str) -> str:
    labels = [label for label in host.lower().split(".") if label]
    if len(labels) <= 2:
        return ".".join(labels)
    if (
        len(labels[-1]) == 2
        and labels[-2] in COMMON_SECOND_LEVEL_DOMAINS
        and len(labels) >= 3
    ):
        return ".".join(labels[-3:])
    return ".".join(labels[-2:])


def _same_site(base: str, url: str) -> bool:
    b = urllib.parse.urlparse(base)
    u = urllib.parse.urlparse(url)
    if not u.scheme and not u.netloc:
        return True
    if not b.netloc or not u.netloc:
        return False
    return _registrable_domain(b.netloc) == _registrable_domain(u.netloc)


def _base(url: str) -> str:
    p = urllib.parse.urlparse(url)
    return f"{p.scheme}://{p.netloc}"


def _try_normalize(url: str) -> str | None:
    try:
        return normalize_url(url)
    except ValueError:
        return None


def _github_releases_url(url: str) -> str | None:
    p = urllib.parse.urlparse(url)
    if p.netloc not in ("github.com", "www.github.com"):
        return None
    segments = [s for s in p.path.split("/") if s]
    if len(segments) < 2:
        return None
    org, repo = segments[0], segments[1]
    return f"https://github.com/{org}/{repo}/releases"


def _is_high_value_same_site_link(seed: str, url: str) -> bool:
    return _same_site(seed, url) and _categorize(url) != "other"


def _sort_key(category: str, url: str) -> tuple[int, int, str]:
    lower_url = url.lower()
    terms = URL_PRIORITY_TERMS.get(category, [])
    priority = next(
        (index for index, term in enumerate(terms) if term in lower_url),
        len(terms),
    )
    path_depth = len([s for s in urllib.parse.urlparse(url).path.split("/") if s])
    return priority, path_depth, url


def _limited_sorted(category: str, urls: set[str]) -> list[str]:
    return sorted(urls, key=lambda url: _sort_key(category, url))[
        : CATEGORY_LIMITS[category]
    ]


class UrlDiscoverProvider:
    def __init__(self) -> None:
        self._fetch = FetchProvider()

    async def discover(self, ctx: WorkflowContext, seed_url: str) -> DiscoveredUrls:
        normalized_seed = _try_normalize(seed_url)
        if normalized_seed is None:
            return DiscoveredUrls(seed_url=seed_url, by_category=UrlsByCategory())

        base = _base(normalized_seed)
        found: dict[str, set[str]] = {
            cat: set() for cat in [*CATEGORY_PATTERNS, "other"]
        }

        if gh := _github_releases_url(normalized_seed):
            found["changelog"].add(gh)

        await self._collect_from_sitemap(ctx, base, normalized_seed, found)
        await self._collect_from_homepage(ctx, normalized_seed, found)
        await self._collect_from_high_value_same_site_pages(ctx, normalized_seed, found)
        await self._probe_canonical_paths(ctx, base, found)
        await self._probe_well_known(ctx, base, found)

        return DiscoveredUrls(
            seed_url=normalized_seed,
            by_category=UrlsByCategory(
                docs=_limited_sorted("docs", found["docs"]),
                api=_limited_sorted("api", found["api"]),
                changelog=_limited_sorted("changelog", found["changelog"]),
                pricing=_limited_sorted("pricing", found["pricing"]),
                security=_limited_sorted("security", found["security"]),
                customers=_limited_sorted("customers", found["customers"]),
                blog=_limited_sorted("blog", found["blog"]),
                careers=_limited_sorted("careers", found["careers"]),
                other=_limited_sorted("other", found["other"]),
            ),
        )

    async def _collect_from_sitemap(
        self, ctx: WorkflowContext, base: str, seed: str, found: dict[str, set[str]]
    ) -> None:
        sitemap_url = base + "/sitemap.xml"
        result = await self._fetch.fetch(ctx, sitemap_url)
        if result.status != "fetched":
            return
        page = ctx.pages.get(sitemap_url) or ctx.pages.get(
            _try_normalize(sitemap_url) or ""
        )
        if not page:
            return
        try:
            root = ET.fromstring(page.body)
            for loc in root.findall(".//sm:loc", _SITEMAP_NS):
                if loc.text:
                    resolved = _try_normalize(loc.text)
                    if resolved and _same_origin(seed, loc.text):
                        found[_categorize(resolved)].add(resolved)
        except ET.ParseError:
            pass

    async def _collect_from_homepage(
        self, ctx: WorkflowContext, seed: str, found: dict[str, set[str]]
    ) -> None:
        result = await self._fetch.fetch(ctx, seed)
        if result.status != "fetched":
            return
        page = ctx.pages.get(seed)
        if not page:
            return
        parser = _LinkExtractor()
        parser.feed(page.body)
        for href in parser.links:
            if not href or href.startswith(("#", "mailto:", "javascript:")):
                continue
            resolved_raw = urllib.parse.urljoin(seed, href)
            if not _same_origin(seed, resolved_raw):
                if gh := _github_releases_url(resolved_raw):
                    found["changelog"].add(gh)
                elif _is_high_value_same_site_link(seed, resolved_raw):
                    resolved = _try_normalize(resolved_raw)
                    if resolved:
                        found[_categorize(resolved)].add(resolved)
                continue
            resolved = _try_normalize(resolved_raw)
            if resolved:
                found[_categorize(resolved)].add(resolved)

    async def _collect_from_high_value_same_site_pages(
        self, ctx: WorkflowContext, seed: str, found: dict[str, set[str]]
    ) -> None:
        seed_host = urllib.parse.urlparse(seed).netloc
        candidates = sorted(
            {
                url
                for category in ("docs", "api", "changelog", "security")
                for url in found[category]
                if urllib.parse.urlparse(url).netloc != seed_host
                and _same_site(seed, url)
            }
        )
        for candidate in candidates[:8]:
            result = await self._fetch.fetch(ctx, candidate)
            if result.status != "fetched":
                continue
            page = ctx.pages.get(result.url)
            if not page:
                continue
            parser = _LinkExtractor()
            parser.feed(page.body)
            for href in parser.links:
                if not href or href.startswith(("#", "mailto:", "javascript:")):
                    continue
                resolved_raw = urllib.parse.urljoin(candidate, href)
                if not _same_origin(candidate, resolved_raw):
                    if gh := _github_releases_url(resolved_raw):
                        found["changelog"].add(gh)
                    continue
                resolved = _try_normalize(resolved_raw)
                if resolved:
                    category = _categorize(resolved)
                    if category != "other":
                        found[category].add(resolved)

    async def _probe_canonical_paths(
        self, ctx: WorkflowContext, base: str, found: dict[str, set[str]]
    ) -> None:
        for category, paths in CANONICAL_PROBES.items():
            if found.get(category):
                continue
            for path in paths:
                probe_url = _try_normalize(base + path)
                if probe_url is None:
                    continue
                result = await self._fetch.fetch(ctx, probe_url)
                if result.status == "fetched":
                    found[category].add(probe_url)
                    break

    async def _probe_well_known(
        self, ctx: WorkflowContext, base: str, found: dict[str, set[str]]
    ) -> None:
        for path in WELL_KNOWN_PATHS:
            probe_url = _try_normalize(base + path)
            if probe_url:
                result = await self._fetch.fetch(ctx, probe_url)
                if result.status == "fetched":
                    found["other"].add(probe_url)
