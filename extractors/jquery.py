from __future__ import annotations

import re

from models import Hit

_AJAX = re.compile(
    r"""\$\.\s*ajax\s*\(\s*\{[^}]*?url\s*:\s*[`"']([^`"']+)[`"'][^}]*?(?:type|method)\s*:\s*[`"'](\w+)[`"']""",
    re.I | re.S,
)
_SHORT = re.compile(
    r"""\$\.\s*(get|post|getJSON|put|delete)\s*\(\s*[`"']([^`"']+)[`"']""",
    re.I,
)
_METHOD_MAP = {"get": "GET", "post": "POST", "getjson": "GET", "put": "PUT", "delete": "DELETE"}


def extract(js: str) -> list[Hit]:
    hits = []
    for m in _AJAX.finditer(js):
        hits.append(Hit(url=m.group(1), method=m.group(2).upper()))
    for m in _SHORT.finditer(js):
        hits.append(Hit(url=m.group(2), method=_METHOD_MAP.get(m.group(1).lower())))
    return hits
