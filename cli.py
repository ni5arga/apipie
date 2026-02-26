from __future__ import annotations

import argparse
import sys
from urllib.parse import urlparse

from color import (
    print_banner, bold, dim, green, bright_green, yellow, red, cyan, white,
    method_tag, kind_tag, url_str, rpad,
)
from crawler import Crawler
from reporter import markdown, json_report
from client import UA_PRESETS


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="apipie", description="API endpoint discovery.")
    p.add_argument("--url", required=True)
    p.add_argument("--output", "-o", default=None, help="Output file (default: <domain>_results.md)")
    p.add_argument("--max-depth", type=int, default=5)
    p.add_argument("--max-pages", type=int, default=300,
                   help="Max pages to crawl (default: 300)")
    p.add_argument("--format", choices=["md", "json"], default="md")
    p.add_argument("--header", "-H", action="append", default=[],
                   help="Extra header, e.g. -H 'Cookie: session=abc'")
    p.add_argument("--user-agent", default=None,
                   help="Full User-Agent string (remember to quote it in the shell)")
    p.add_argument("--ua", choices=list(UA_PRESETS), default=None, metavar="PRESET",
                   help="UA preset: " + ", ".join(UA_PRESETS))
    p.add_argument("--rate-limit", type=float, default=0.0,
                   help="Min seconds between requests")
    p.add_argument("--workers", type=int, default=6,
                   help="Concurrent JS fetchers")
    p.add_argument("--verbose", "-v", action="store_true")
    p.add_argument("--no-color", action="store_true", help="Disable colored output")
    return p


def _parse_headers(raw: list[str]) -> dict[str, str]:
    out = {}
    for h in raw:
        if ":" not in h:
            continue
        k, v = h.split(":", 1)
        out[k.strip()] = v.strip()
    return out


def _default_output(url: str, fmt: str) -> str:
    domain = urlparse(url).netloc.replace(":", "_").replace(".", "_")
    ext = "json" if fmt == "json" else "md"
    return f"{domain}_results.{ext}"


def _info(label: str, value: str):
    print(f"  {dim(label + ':')}  {white(value)}")


def entry():
    args = _build_parser().parse_args()

    if args.no_color:
        import os
        os.environ["NO_COLOR"] = "1"
        import color as _col
        _col._TTY = False

    url = args.url if "://" in args.url else f"https://{args.url}"
    output = args.output or _default_output(url, args.format)
    headers = _parse_headers(args.header)
    ua = UA_PRESETS.get(args.ua) if args.ua else args.user_agent

    print_banner()

    print(dim("  " + "─" * 52))
    _info("target", url)
    _info("depth ", str(args.max_depth))
    _info("output", output)
    _info("format", args.format)
    print(dim("  " + "─" * 52) + "\n")

    crawler = Crawler(
        url,
        max_depth=args.max_depth,
        max_pages=args.max_pages,
        headers=headers,
        rate_limit=args.rate_limit,
        workers=args.workers,
        verbose=args.verbose,
        user_agent=ua,
    )
    endpoints = crawler.run()

    if not endpoints:
        print(f"\n  {yellow('!')}  {white('nothing found')}")
        sys.exit(0)

    rest    = [e for e in endpoints if e.kind == "rest"]
    gql     = [e for e in endpoints if e.kind == "graphql"]
    rpc     = [e for e in endpoints if e.kind == "rpc"]

    print(
        f"\n  {bright_green('+')}  {bold(white(str(len(endpoints))))} endpoint(s) found"
        f"  {dim(f'rest={len(rest)} graphql={len(gql)} rpc={len(rpc)}')}\n"
    )

    print(dim("  " + "─" * 52))

    current_kind = None
    for ep in endpoints:
        if ep.kind != current_kind:
            current_kind = ep.kind
            label = {"rest": "REST", "graphql": "GraphQL", "rpc": "RPC"}.get(ep.kind, ep.kind.upper())
            print(f"\n  {cyan(bold(label))}\n")

        mtag = method_tag(ep.methods)
        ktag = kind_tag(ep.kind)
        ustr = url_str(ep.url)
        print(f"    {rpad(mtag, 10)}  {ustr}{ktag}")

    print("\n" + dim("  " + "─" * 52) + "\n")

    if args.format == "json":
        body = json_report(endpoints)
    else:
        body = markdown(endpoints, url)

    with open(output, "w") as f:
        f.write(body)

    print(f"  {bright_green('+')}  {dim('wrote')} {white(output)}\n")
