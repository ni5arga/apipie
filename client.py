from __future__ import annotations

import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

_DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

UA_PRESETS: dict[str, str] = {
    "chrome": _DEFAULT_UA,
    "mobile": (
        "Mozilla/5.0 (Linux; Android 14; Pixel 8) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Mobile Safari/537.36"
    ),
    "firefox": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) "
        "Gecko/20100101 Firefox/122.0"
    ),
    "safari": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) "
        "Version/17.2 Safari/605.1.15"
    ),
    "bot": "Googlebot/2.1 (+http://www.google.com/bot.html)",
}
_TIMEOUT = 15
_MAX_BODY = 5 * 1024 * 1024  # 5 MB cap per response


class HttpClient:
    def __init__(self, headers=None, rate_limit=0.0, workers=6, user_agent=None):
        self._session = requests.Session()
        self._session.headers["User-Agent"] = user_agent or _DEFAULT_UA
        self._session.headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        self._session.headers["Accept-Language"] = "en-US,en;q=0.5"
        if headers:
            self._session.headers.update(headers)
        self._delay = rate_limit
        self._last_req = 0.0
        self._pool = ThreadPoolExecutor(max_workers=workers)

    def get(self, url) -> str | None:
        self._throttle()
        try:
            r = self._session.get(url, timeout=_TIMEOUT, stream=True)
            r.raise_for_status()
            ct = r.headers.get("content-type", "")
            if not any(t in ct for t in ("text/", "javascript", "json", "xml")):
                r.close()
                return None
            chunks: list[bytes] = []
            total = 0
            for chunk in r.iter_content(chunk_size=65536):
                chunks.append(chunk)
                total += len(chunk)
                if total >= _MAX_BODY:
                    break
            r.close()
            raw = b"".join(chunks)
            enc = r.encoding or "utf-8"
            return raw.decode(enc, errors="replace")
        except requests.RequestException as e:
            print(f"  [!] {url}: {e}", file=sys.stderr)
            return None

    def get_many(self, urls) -> dict[str, str]:
        results = {}
        futs = {self._pool.submit(self.get, u): u for u in urls}
        for fut in as_completed(futs):
            url = futs[fut]
            body = fut.result()
            if body is not None:
                results[url] = body
        return results

    def _throttle(self):
        if self._delay <= 0:
            return
        elapsed = time.monotonic() - self._last_req
        if elapsed < self._delay:
            time.sleep(self._delay - elapsed)
        self._last_req = time.monotonic()

    def close(self):
        self._pool.shutdown(wait=False)
        self._session.close()
