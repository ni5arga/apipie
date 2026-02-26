from __future__ import annotations

import re

from models import Hit

_SA = re.compile(
    r"""superagent\s*\.\s*(get|post|put|patch|delete)\s*\(\s*[`"']([^`"']+)[`"']""",
    re.I,
)


def extract(js: str) -> list[Hit]:
    return [Hit(url=m.group(2), method=m.group(1).upper()) for m in _SA.finditer(js)]
