from __future__ import annotations

import re

from models import Hit

_JSONRPC_METHOD = re.compile(
    r"""(?:jsonrpc|json_rpc)[^}]*?method\s*:\s*[`"']([^`"']+)[`"']"""
    r"""|method\s*:\s*[`"']([^`"']+)[`"'][^}]*?jsonrpc""",
    re.I | re.S,
)

_JSONRPC_ENDPOINT = re.compile(
    r"""[`"']((?:https?://[^`"'\s]*)?/(?:jsonrpc|json[_-]rpc|rpc))[`"']""",
    re.I,
)

_TRPC_CALL = re.compile(
    r"""trpc\s*\.\s*([\w.]+)\s*\.\s*(query|mutate|subscribe)\s*\(""",
    re.I,
)

_TRPC_HOOK = re.compile(
    r"""(?:api|trpc)\s*\.\s*([\w.]+)\s*\.\s*use(Query|Mutation|Subscription)\s*\(""",
    re.I,
)

_GRPC_URL = re.compile(
    r"""[`"']((?:https?://[^`"'\s]*/)?[A-Za-z][A-Za-z0-9_.]*\.[A-Z][A-Za-z0-9_]*/[A-Z][A-Za-z0-9_]+)[`"']""",
)

_SOCKETIO_EMIT = re.compile(
    r"""socket\.emit\s*\(\s*[`"']([^`"']+)[`"']""",
    re.I,
)

_SOCKETIO_ON = re.compile(
    r"""socket\.on\s*\(\s*[`"']([^`"']+)[`"']""",
    re.I,
)

_TRPC_OP_MAP = {"query": "query", "mutate": "mutation", "subscribe": "subscription"}
_HOOK_OP_MAP = {"query": "query", "mutation": "mutation", "subscription": "subscription"}


def extract(js: str) -> list[Hit]:
    hits = []

    for m in _JSONRPC_METHOD.finditer(js):
        method_name = m.group(1) or m.group(2)
        hits.append(Hit(url="__jsonrpc__", kind="rpc", method="POST", rpc_method=method_name))

    for m in _JSONRPC_ENDPOINT.finditer(js):
        hits.append(Hit(url=m.group(1), kind="rpc", method="POST"))

    for m in _TRPC_CALL.finditer(js):
        proc = m.group(1)
        op = _TRPC_OP_MAP.get(m.group(2).lower(), "query")
        hits.append(Hit(url="__trpc__", kind="rpc", method="POST", rpc_method=f"{proc}.{op}"))

    for m in _TRPC_HOOK.finditer(js):
        proc = m.group(1)
        op = _HOOK_OP_MAP.get(m.group(2).lower(), "query")
        hits.append(Hit(url="__trpc__", kind="rpc", method="POST", rpc_method=f"{proc}.{op}"))

    for m in _GRPC_URL.finditer(js):
        hits.append(Hit(url=m.group(1), kind="rpc", method="POST"))

    for m in _SOCKETIO_EMIT.finditer(js):
        hits.append(Hit(url="__socketio__", kind="rpc", rpc_method=f"emit:{m.group(1)}"))

    for m in _SOCKETIO_ON.finditer(js):
        hits.append(Hit(url="__socketio__", kind="rpc", rpc_method=f"on:{m.group(1)}"))

    return hits
