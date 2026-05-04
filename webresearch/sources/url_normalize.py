from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

TRACKING_PARAM_NAMES = {
    "_hsenc",
    "_hsmi",
    "fbclid",
    "gclid",
    "ref",
    "ref_src",
}
DEFAULT_HTTP_PORT = 80
DEFAULT_HTTPS_PORT = 443


def normalize_url(raw: str) -> str:
    parsed = urlsplit(raw.strip())
    scheme = parsed.scheme.lower()
    if scheme not in {"http", "https"}:
        msg = f"Unsupported URL scheme: {parsed.scheme}"
        raise ValueError(msg)

    hostname = parsed.hostname
    if hostname is None:
        msg = "URL must include a host"
        raise ValueError(msg)

    host = hostname.lower()
    port = _normalized_port(scheme, parsed.port)
    netloc = f"{host}:{port}" if port is not None else host
    path = _normalized_path(parsed.path)
    query = _normalized_query(parsed.query)

    return urlunsplit((scheme, netloc, path, query, ""))


def _normalized_port(scheme: str, port: int | None) -> int | None:
    if port is None:
        return None
    if scheme == "http" and port == DEFAULT_HTTP_PORT:
        return None
    if scheme == "https" and port == DEFAULT_HTTPS_PORT:
        return None
    return port


def _normalized_path(path: str) -> str:
    if path in {"", "/"}:
        return "/"
    return path.rstrip("/")


def _normalized_query(query: str) -> str:
    kept_params = [
        (name, value)
        for name, value in parse_qsl(query, keep_blank_values=True)
        if not _is_tracking_param(name)
    ]
    return urlencode(sorted(kept_params))


def _is_tracking_param(name: str) -> bool:
    lowered = name.lower()
    return lowered in TRACKING_PARAM_NAMES or lowered.startswith(("utm_", "mc_"))
