from __future__ import annotations

import re

from models import Hit

_FETCH = re.compile(
    r"""fetch\(\s*[`"']([^`"']+)[`"']"""
    r"""(?:\s*,\s*\{[^}]*?method\s*:\s*[`"'](\w+)[`"'])?""",
    re.I,
)


def extract(js: str) -> list[Hit]:
    hits = []
    for m in _FETCH.finditer(js):
        method = (m.group(2) or "").upper() or None
        hits.append(Hit(url=m.group(1), method=method))
    return hits
