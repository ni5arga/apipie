from __future__ import annotations

import re
import sys
from collections import deque
from urllib.parse import urlparse, urlunparse

try:
    import lxml  
    _BS_PARSER = "lxml"
except ImportError:
    _BS_PARSER = "html.parser"

from bs4 import BeautifulSoup

from client import HttpClient
from infer import infer_method
from models import EndpointStore, Hit
from resolve import (
    is_template_only,
    clean_templates,
    resolve,
    normalize,
    same_origin,
)
from extractors import (
    extract_from_js,
    extract_forms,
    extract_data_urls,
    extract_script_srcs,
    extract_inline_js,
    extract_links,
)

_SENTINELS = {
    "__graphql__": "/graphql",
    "__jsonrpc__": "/jsonrpc",
    "__trpc__": "/api/trpc",
    "__socketio__": "/socket.io",
}

_BASEURL_RE = re.compile(r"""baseURL\s*:\s*[`"'](https?://[^`"'\s]+)[`"']""", re.I)

_API_SIGNAL_RE = re.compile(
    r"/(?:api|v\d+|rest|graphql|rpc|oauth|token|auth|endpoints?|services?|query|mutation)(?:/|$)",
    re.I,
)

_API_DOMAIN_RE = re.compile(r"(?:^|\.)api[.\-]|[.\-]api\.", re.I)

MAX_PAGES = 300


def _page_key(url: str) -> str:
    """Normalise a URL for crawl deduplication: strip query string and fragment."""
    p = urlparse(url)
    return urlunparse((p.scheme, p.netloc, p.path.rstrip("/") or "/", "", "", ""))


class Crawler:
    def __init__(self, base_url: str, max_depth=3, max_pages=MAX_PAGES,
                 headers=None, rate_limit=0.0, workers=6,
                 verbose=False, user_agent=None):
        self.base_url = base_url.rstrip("/")
        self.domain = urlparse(self.base_url).netloc
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.verbose = verbose
        self.client = HttpClient(headers=headers, rate_limit=rate_limit,
                                 workers=workers, user_agent=user_agent)
        self.store = EndpointStore()
        self._seen_scripts: set[str] = set()

    def run(self):
        try:
            self._bfs()
        finally:
            self.client.close()
        self._infer_missing_methods()
        return self.store.all()

    def _bfs(self):
        queue: deque[tuple[str, int]] = deque([(self.base_url, 0)])
        seen_keys: set[str] = set()
        seen_keys.add(_page_key(self.base_url))

        while queue:
            if len(seen_keys) >= self.max_pages:
                self._log(f"[page cap {self.max_pages} reached, stopping crawl]")
                break
            url, depth = queue.popleft()
            if depth > self.max_depth:
                continue

            self._log(f"[depth={depth}] {url}")
            html = self.client.get(url)
            if html is None:
                continue

            soup = BeautifulSoup(html, _BS_PARSER)
            self._process_scripts(soup, url)
            self._process_html(soup, url)

            if depth < self.max_depth:
                for link in extract_links(soup, url):
                    if not same_origin(link, self.domain):
                        continue
                    key = _page_key(link)
                    if key not in seen_keys:
                        seen_keys.add(key)
                        queue.append((link, depth + 1))

    def _infer_missing_methods(self):
        for ep in self.store._map.values():
            if not ep.methods:
                ep.methods.add(infer_method(ep.url))

    def _process_scripts(self, soup: BeautifulSoup, page_url: str):
        srcs = extract_script_srcs(soup, page_url)
        new_srcs = [s for s in srcs if s not in self._seen_scripts]
        self._seen_scripts.update(new_srcs)

        if new_srcs:
            for src_url, js in self.client.get_many(new_srcs).items():
                self._ingest_js(js, src_url)

        for js in extract_inline_js(soup):
            self._ingest_js(js, page_url)

    def _process_html(self, soup: BeautifulSoup, page_url: str):
        for url, method in extract_forms(soup, page_url):
            # Skip same-origin form actions that have no API signal in the path.
            # Navigation forms (search pages, help pages, etc.) are not endpoints.
            try:
                p = urlparse(url)
            except Exception:
                continue
            if same_origin(url, self.domain) and not _API_SIGNAL_RE.search(p.path):
                continue
            self._register(Hit(url=url, method=method), page_url)
        for url in extract_data_urls(soup, page_url):
            try:
                p = urlparse(url)
            except Exception:
                continue
            if same_origin(url, self.domain) and not _API_SIGNAL_RE.search(p.path):
                continue
            self._register(Hit(url=url), page_url)

    def _ingest_js(self, js: str, source: str):
        # Collect cross-origin API base URLs declared in this file (e.g. from axios.create)
        extra_bases = [
            m.group(1).rstrip("/")
            for m in _BASEURL_RE.finditer(js)
            if urlparse(m.group(1)).netloc != self.domain
        ]

        for hit in extract_from_js(js):
            if is_template_only(hit.url):
                continue
            raw = self._resolve_sentinel(hit.url)
            cleaned = clean_templates(raw)

            # For relative paths: also resolve against each cross-origin base found in this file.
            # Use the full base for paths that fit under it; use bare origin for others.
            if not cleaned.startswith(("http://", "https://")) and extra_bases:
                seen_joined: set[str] = set()
                for base in extra_bases:
                    base_path = urlparse(base).path.rstrip("/")
                    rel = cleaned.lstrip("/")
                    if base_path and not cleaned.startswith(base_path + "/"):
                        # Path does not belong under this service base – resolve against origin only
                        p = urlparse(base)
                        joined = f"{p.scheme}://{p.netloc}/{rel}"
                    else:
                        joined = base + "/" + rel
                    if joined not in seen_joined:
                        seen_joined.add(joined)
                        self._register(Hit(
                            url=joined,
                            kind=hit.kind,
                            method=hit.method,
                            gql_op_type=hit.gql_op_type,
                            gql_op_name=hit.gql_op_name,
                            rpc_method=hit.rpc_method,
                        ), source)

            absolute = resolve(cleaned, self.base_url, source)
            if absolute:
                self._register(Hit(
                    url=absolute,
                    kind=hit.kind,
                    method=hit.method,
                    gql_op_type=hit.gql_op_type,
                    gql_op_name=hit.gql_op_name,
                    rpc_method=hit.rpc_method,
                ), source)

    def _resolve_sentinel(self, url: str) -> str:
        return _SENTINELS.get(url, url)

    def _should_register(self, url: str, kind: str) -> bool:
        if same_origin(url, self.domain):
            return True
        if kind in ("graphql", "rpc"):
            return True
        try:
            p = urlparse(url)
        except Exception:
            return False
        if _API_DOMAIN_RE.search(p.netloc):
            return True
        return bool(_API_SIGNAL_RE.search(p.path))

    def _register(self, hit: Hit, source: str):
        path_url, params = normalize(hit.url)
        if not self._should_register(path_url, hit.kind):
            return
        self.store.add(path_url, hit=hit, source=source, params=params)

    def _log(self, msg: str):
        if self.verbose:
            from color import dim, cyan
            print(f"  {dim('>')} {cyan(msg)}", file=sys.stderr)
