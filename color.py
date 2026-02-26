from __future__ import annotations

import os
import re
import sys

_TTY = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None
_ANSI_RE = re.compile(r"\033\[[0-9;]*m")

def _c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _TTY else text

def _vlen(s: str) -> int:
    return len(_ANSI_RE.sub("", s))

def rpad(s: str, width: int) -> str:
    return s + " " * max(0, width - _vlen(s))

def bold(t: str)           -> str: return _c("1", t)
def dim(t: str)            -> str: return _c("2", t)
def red(t: str)            -> str: return _c("31", t)
def green(t: str)          -> str: return _c("32", t)
def yellow(t: str)         -> str: return _c("33", t)
def blue(t: str)           -> str: return _c("34", t)
def magenta(t: str)        -> str: return _c("35", t)
def cyan(t: str)           -> str: return _c("36", t)
def white(t: str)          -> str: return _c("37", t)
def bright_red(t: str)     -> str: return _c("91", t)
def bright_green(t: str)   -> str: return _c("92", t)
def bright_yellow(t: str)  -> str: return _c("93", t)
def bright_blue(t: str)    -> str: return _c("94", t)
def bright_magenta(t: str) -> str: return _c("95", t)
def bright_cyan(t: str)    -> str: return _c("96", t)

_METHOD_COLORS = {
    "GET":     bright_green,
    "POST":    bright_yellow,
    "PUT":     bright_blue,
    "PATCH":   cyan,
    "DELETE":  bright_red,
    "HEAD":    dim,
    "OPTIONS": dim,
}

_KIND_COLORS = {
    "graphql": bright_magenta,
    "rpc":     bright_cyan,
}

def method_tag(methods: set[str]) -> str:
    if not methods:
        return dim("?")
    parts = []
    for m in sorted(methods):
        fn = _METHOD_COLORS.get(m, white)
        parts.append(fn(m))
    return dim(",").join(parts)

def kind_tag(kind: str) -> str:
    if kind == "rest":
        return ""
    fn = _KIND_COLORS.get(kind, white)
    return " " + dim("[") + fn(kind) + dim("]")

def url_str(url: str) -> str:
    try:
        from urllib.parse import urlparse
        p = urlparse(url)
        base = dim(f"{p.scheme}://{p.netloc}")
        path = white(p.path)
        qs   = dim("?" + p.query) if p.query else ""
        return base + path + qs
    except Exception:
        return url

BANNER = r"""
              _       _
   __ _ _ __ (_)_ __ (_) ___
  / _` | '_ \| | '_ \| |/ _ \
 | (_| | |_) | | |_) | |  __/
  \__,_| .__/|_| .__/|_|\___|
       |_|     |_|
"""

def print_banner():
    if not _TTY:
        return
    lines = BANNER.splitlines()
    palette = [bright_cyan, cyan, bright_blue, blue]
    for i, line in enumerate(lines):
        print("  " + palette[i % len(palette)](line))
    print()
