from __future__ import annotations

import json
from collections import defaultdict
from urllib.parse import urlparse, urlencode

from models import Endpoint


def markdown(endpoints: list[Endpoint], target: str) -> str:
    rest = [e for e in endpoints if e.kind == "rest"]
    graphql = [e for e in endpoints if e.kind == "graphql"]
    rpc = [e for e in endpoints if e.kind == "rpc"]

    buf = [
        f"# API Endpoints — {target}\n",
        f"| Kind | Count |",
        f"|------|-------|",
        f"| REST | {len(rest)} |",
        f"| GraphQL | {len(graphql)} |",
        f"| RPC | {len(rpc)} |",
        f"| **Total** | **{len(endpoints)}** |",
        "",
    ]

    if rest:
        buf.append("## REST\n")
        for prefix, eps in _group(rest).items():
            buf.append(f"### {prefix}\n")
            for ep in eps:
                buf.extend(_render_rest(ep))
        buf.append("---\n")

    if graphql:
        buf.append("## GraphQL\n")
        for ep in graphql:
            buf.extend(_render_graphql(ep))
        buf.append("---\n")

    if rpc:
        buf.append("## RPC\n")
        for ep in rpc:
            buf.extend(_render_rpc(ep))
        buf.append("---\n")

    return "\n".join(buf)


def json_report(endpoints: list[Endpoint]) -> str:
    records = []
    for ep in endpoints:
        rec: dict = {
            "url": ep.url,
            "kind": ep.kind,
            "methods": sorted(ep.methods) or ["UNKNOWN"],
            "params": dict(ep.params),
            "sources": sorted(ep.sources),
        }
        if ep.gql_ops:
            rec["gql_operations"] = [
                {"type": t, "name": n} for t, n in sorted(ep.gql_ops)
            ]
        if ep.rpc_methods:
            rec["rpc_methods"] = sorted(ep.rpc_methods)
        records.append(rec)
    return json.dumps(records, indent=2)


def _group(endpoints: list[Endpoint]) -> dict[str, list[Endpoint]]:
    groups: dict[str, list[Endpoint]] = defaultdict(list)
    for ep in endpoints:
        parts = [p for p in urlparse(ep.url).path.split("/") if p]
        prefix = f"/{parts[0]}/" if parts else "/"
        groups[prefix].append(ep)
    return dict(sorted(groups.items()))


def _render_rest(ep: Endpoint) -> list[str]:
    methods = sorted(ep.methods) if ep.methods else ["UNKNOWN"]
    method_tag = ", ".join(methods)
    primary = methods[0] if methods[0] != "UNKNOWN" else "GET"

    lines = [
        f"#### {method_tag} `{ep.url}`\n",
        "| | |",
        "|---|---|",
        f"| URL | `{ep.url}` |",
        f"| Method | {method_tag} |",
    ]

    if ep.params:
        rendered = ", ".join(
            f"`{k}`={v[0]!r}" if v else f"`{k}`"
            for k, v in sorted(ep.params.items())
        )
        lines.append(f"| Params | {rendered} |")

    if ep.sources:
        lines.append(f"| Source | {', '.join(sorted(ep.sources))} |")

    curl_url = ep.url
    if ep.params:
        qs = urlencode({k: v[0] if v else "" for k, v in ep.params.items()})
        curl_url += f"?{qs}"

    xflag = f" -X {primary}" if primary != "GET" else ""
    lines += ["", f"```bash\ncurl{xflag} '{curl_url}'\n```\n"]
    return lines


def _render_graphql(ep: Endpoint) -> list[str]:
    lines = [
        f"### `{ep.url}`\n",
        "| | |",
        "|---|---|",
        f"| URL | `{ep.url}` |",
        "| Method | POST |",
    ]

    if ep.sources:
        lines.append(f"| Source | {', '.join(sorted(ep.sources))} |")

    if ep.gql_ops:
        lines.append("\n**Operations:**\n")
        lines.append("| Type | Name |")
        lines.append("|------|------|")
        for op_type, op_name in sorted(ep.gql_ops):
            lines.append(f"| {op_type} | `{op_name}` |")

    lines += [
        "",
        "```bash",
        f"curl -X POST '{ep.url}' \\",
        "  -H 'Content-Type: application/json' \\",
        """  -d '{"query": "{ __typename }"}'""",
        "```\n",
    ]
    return lines


def _render_rpc(ep: Endpoint) -> list[str]:
    lines = [
        f"### `{ep.url}`\n",
        "| | |",
        "|---|---|",
        f"| URL | `{ep.url}` |",
        "| Method | POST |",
    ]

    if ep.sources:
        lines.append(f"| Source | {', '.join(sorted(ep.sources))} |")

    if ep.rpc_methods:
        lines.append("\n**Methods:**\n")
        for m in sorted(ep.rpc_methods):
            lines.append(f"- `{m}`")

    lines += ["", "```bash", f"curl -X POST '{ep.url}' \\",
              "  -H 'Content-Type: application/json' \\",
              """  -d '{"jsonrpc":"2.0","method":"<method>","params":[],"id":1}'""",
              "```\n"]
    return lines
