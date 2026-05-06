from __future__ import annotations

from webresearch.context import FetchedPage, WorkflowContext
from webresearch.sources.url_normalize import normalize_url
from webresearch.tools.discover_urls import _categorize, _github_releases_url, discover_urls
from webresearch.tools.fetch_url import FetchResult


def test_categorize_docs_subdomain_as_docs() -> None:
    assert _categorize("https://documentation.wazuh.com/current/index.html") == "docs"


def test_github_releases_url_repo_root() -> None:
    assert (
        _github_releases_url("https://github.com/wazuh/wazuh")
        == "https://github.com/wazuh/wazuh/releases"
    )


def test_github_releases_url_already_releases() -> None:
    assert (
        _github_releases_url("https://github.com/wazuh/wazuh/releases")
        == "https://github.com/wazuh/wazuh/releases"
    )


def test_github_releases_url_deep_path() -> None:
    assert (
        _github_releases_url("https://github.com/wazuh/wazuh/tree/main")
        == "https://github.com/wazuh/wazuh/releases"
    )


def test_github_releases_url_not_github() -> None:
    assert _github_releases_url("https://example.com/org/repo") is None


def test_github_releases_url_org_only() -> None:
    assert _github_releases_url("https://github.com/wazuh") is None


def test_github_releases_url_www_prefix() -> None:
    assert (
        _github_releases_url("https://www.github.com/wazuh/wazuh")
        == "https://github.com/wazuh/wazuh/releases"
    )


async def test_discover_urls_follows_high_value_same_site_docs_subdomain(monkeypatch) -> None:
    pages = {
        "https://wazuh.com/": (
            '<a href="https://documentation.wazuh.com/current/index.html">Documentation</a>'
        ),
        "https://documentation.wazuh.com/current/index.html": (
            '<a href="release-notes/index.html">Release notes</a>'
            '<a href="user-manual/api/reference.html">API reference</a>'
        ),
    }

    async def fake_fetch_url(ctx: WorkflowContext, url: str) -> FetchResult:
        normalized = normalize_url(url)
        body = pages.get(normalized)
        if body is None:
            return FetchResult(url=normalized, status="failed", reason="not mocked")
        ctx.pages[normalized] = FetchedPage(
            url=normalized,
            body=body,
            content_type="text/html",
            truncated=False,
        )
        return FetchResult(
            url=normalized,
            status="fetched",
            byte_size=len(body),
            content_type="text/html",
        )

    monkeypatch.setattr("webresearch.tools.discover_urls.fetch_url", fake_fetch_url)

    result = await discover_urls(WorkflowContext(), "https://wazuh.com/")

    assert "https://documentation.wazuh.com/current/index.html" in result.by_category.docs
    assert (
        "https://documentation.wazuh.com/current/release-notes/index.html"
        in result.by_category.changelog
    )
    assert (
        "https://documentation.wazuh.com/current/user-manual/api/reference.html"
        in result.by_category.api
    )
