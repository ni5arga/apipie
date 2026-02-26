from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

_TEMPLATE_RE = re.compile(r"\$\{[^}]+\}|\{\{[^}]+\}\}|\{[^}]+\}")


def is_template_only(raw: str) -> bool:
    stripped = _TEMPLATE_RE.sub("", raw)
    return stripped in ("", "/", "//")


def clean_templates(raw: str) -> str:
    return _TEMPLATE_RE.sub("{param}", raw)


def resolve(raw: str, base_url: str, source_url: str) -> str | None:
    if raw.startswith(("http://", "https://")):
        return raw
    if raw.startswith("/"):
        return urljoin(base_url, raw)
    if raw.startswith("./") or not raw.startswith("//"):
        return urljoin(source_url, raw)
    return None


def normalize(url: str) -> tuple[str, dict]:
    p = urlparse(url)
    path_url = f"{p.scheme}://{p.netloc}{p.path}"
    params = {}
    if p.query:
        from urllib.parse import parse_qs
        params = parse_qs(p.query)
    return path_url, params


def same_origin(url: str, domain: str) -> bool:
    return urlparse(url).netloc == domain
