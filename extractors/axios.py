from __future__ import annotations

import re
from urllib.parse import urlparse

from models import Hit

# var e = n.create({ ..., baseURL: 'https://...' }) -- any obj.create, handles minified imports
_CREATE = re.compile(
    r"""(\w+)\s*=\s*(?:\w+\.)+create\s*\([\s\S]{0,300}?baseURL\s*:\s*[`"'](https?://[^`"']+)[`"']""",
    re.I,
)

_CALL = re.compile(
    r"""(\w+)\s*\.\s*(get|post|put|patch|delete|head|options|request)\s*\(\s*[`"']([^`"'\s]+)[`"']""",
    re.I,
)

_OBJ = re.compile(
    r"""axios\s*\(\s*\{[^}]*?url\s*:\s*[`"']([^`"']+)[`"'][^}]*?method\s*:\s*[`"'](\w+)[`"']""",
    re.I | re.S,
)


def _join_base(base: str, path: str) -> str:
    """Combine an axios baseURL with a path the way axios does.
    Root-relative paths (/foo) resolve against the origin only.
    Relative paths (foo) are appended to the full baseURL.
    """
    if path.startswith(("http://", "https://")):
        return path
    base = base.rstrip("/")
    if path.startswith("/"):
        p = urlparse(base)
        return f"{p.scheme}://{p.netloc}{path}"
    return base + "/" + path


def extract(js: str) -> list[Hit]:
    bases: dict[str, str] = {}
    for m in _CREATE.finditer(js):
        bases[m.group(1)] = m.group(2).rstrip("/")

    hits: list[Hit] = []

    for m in _CALL.finditer(js):
        obj = m.group(1)
        method = m.group(2).upper()
        path = m.group(3)
        method_val = None if method == "REQUEST" else method

        if obj == "axios":
            hits.append(Hit(url=path, method=method_val))
        elif obj in bases:
            hits.append(Hit(url=_join_base(bases[obj], path), method=method_val))

    for m in _OBJ.finditer(js):
        hits.append(Hit(url=m.group(1), method=m.group(2).upper()))

    return hits
