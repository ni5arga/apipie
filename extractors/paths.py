from __future__ import annotations

import re
from urllib.parse import urlparse

from models import Hit

_ABS = re.compile(
    r"""[`"'](https?://[^`"'\s<>{}]+/[a-zA-Z0-9_./-]+)[`"']""",
    re.I,
)

_REL = re.compile(
    r"""[`"']((?:/[a-zA-Z0-9_.-]+){1,}/(?:api|v\d+|rest|oauth|token|auth|graphql|rpc)/[^`"'\s{}<>]*)[`"']""",
    re.I,
)

_SKIP_EXT = re.compile(
    r"\.(?:js|css|html|htm|png|jpg|jpeg|gif|svg|ico|woff2?|ttf|eot|map|pdf|docx?|zip|tar|gz)(?:[?#]|$)",
    re.I,
)

_NOISE_DOMAINS: frozenset[str] = frozenset({
    "www.google.com", "google.com",
    "pagead2.googlesyndication.com", "adservice.google.com",
    "www.googleadservices.com", "googleadservices.com",
    "googleads.g.doubleclick.net", "ad.doubleclick.net", "stats.g.doubleclick.net",
    "www.googletagmanager.com", "googletagmanager.com",
    "www.facebook.com", "connect.facebook.net",
    "www.youtube.com", "youtu.be", "i.ytimg.com",
    "cdn.jsdelivr.net", "unpkg.com", "cdnjs.cloudflare.com",
    "addons.mozilla.org", "chrome.google.com",
    "www.w3.org", "w3.org",
    "get.adobe.com",
})

_NOISE_PATH_RE = re.compile(r"^https?://[^/]+/(?:static|assets|public|dist)/", re.I)


def _is_noise(url: str) -> bool:
    try:
        host = urlparse(url).netloc.lower()
    except Exception:
        return False
    return host in _NOISE_DOMAINS


def extract(js: str) -> list[Hit]:
    hits: list[Hit] = []
    for m in _ABS.finditer(js):
        url = m.group(1)
        if _SKIP_EXT.search(url):
            continue
        if _is_noise(url):
            continue
        if _NOISE_PATH_RE.search(url):
            continue
        hits.append(Hit(url=url))
    for m in _REL.finditer(js):
        hits.append(Hit(url=m.group(1)))
    return hits
