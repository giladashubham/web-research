import pytest

from webresearch.sources.url_normalize import normalize_url


def test_tracking_params_collapse_to_same_url():
    tracked = "https://Example.com/report?utm_source=newsletter&b=2&gclid=abc&a=1&mc_cid=campaign"
    clean = "https://example.com/report?a=1&b=2"

    assert normalize_url(tracked) == clean
    assert normalize_url(clean) == clean


def test_trailing_slash_and_fragment_collapse():
    assert (
        normalize_url("https://example.com/articles/research/?a=1#section")
        == "https://example.com/articles/research?a=1"
    )


def test_root_path_is_preserved():
    assert normalize_url("https://example.com/") == "https://example.com/"
    assert normalize_url("https://example.com") == "https://example.com/"


def test_default_ports_are_stripped():
    assert normalize_url("http://example.com:80/path") == "http://example.com/path"
    assert normalize_url("https://example.com:443/path") == "https://example.com/path"


def test_different_schemes_and_hosts_do_not_collapse():
    assert normalize_url("http://example.com/path") != normalize_url(
        "https://example.com/path"
    )
    assert normalize_url("https://example.com/path") != normalize_url(
        "https://example.org/path"
    )


@pytest.mark.parametrize(
    "raw", ["mailto:test@example.com", "javascript:alert(1)", "file:///tmp/a"]
)
def test_non_http_schemes_raise(raw):
    with pytest.raises(ValueError):
        normalize_url(raw)
