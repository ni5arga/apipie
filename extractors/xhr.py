from __future__ import annotations

import re

from models import Hit, HTTP_METHODS

_XHR = re.compile(
    r"""\.open\(\s*[`"'](\w+)[`"']\s*,\s*[`"']([^`"']+)[`"']""",
    re.I,
)


def extract(js: str) -> list[Hit]:
    hits = []
    for m in _XHR.finditer(js):
        method = m.group(1).upper()
        hits.append(Hit(url=m.group(2), method=method if method in HTTP_METHODS else None))
    return hits
