# apipie

Point it at a web app and let it do the work. apipie crawls pages, tears apart JavaScript, and surfaces every API endpoint it can find — REST, GraphQL, and RPC — without touching a single network socket beyond the target. Walk away with a structured Markdown or JSON report, curl examples included.

---

## How it works

apipie performs a BFS crawl of the target, fetches external JS files concurrently, and runs static analysis across everything it collects. No browser, no proxy, no instrumentation.

**JS patterns detected:** `fetch`, `axios` (including `axios.create` instances), `XMLHttpRequest`, jQuery (`$.ajax`/`$.get`/`$.post`), Angular `$http`/`HttpClient`, `superagent`, hardcoded REST path strings, GraphQL (Apollo, urql, `graphql-request`, `gql` templates, React hooks), JSON-RPC, tRPC, gRPC-web, Socket.IO.

**HTML signals:** `<form action>`, `data-url`, `data-endpoint` attributes.

Duplicate endpoints are merged. If a URL appears as both REST and GraphQL, it is promoted to GraphQL. Endpoints with no explicit method are assigned one via path-keyword inference.

---

## Requirements

- Python 3.9+
- `requests`, `beautifulsoup4`
- `lxml` (optional, significantly faster HTML parsing)

---

## Installation

```bash
git clone https://github.com/ni5arga/apipie.git
cd apipie
pip install -r requirements.txt
```

---

## Usage

```
python3 apipie.py --url <target> [options]
```

| Argument | Default | Description |
|---|---|---|
| `--url` | *(required)* | Target URL |
| `--output` / `-o` | `<domain>_results.md` | Output file |
| `--max-depth` | `5` | Crawl depth |
| `--max-pages` | `300` | Page cap |
| `--format` | `md` | `md` or `json` |
| `--header` / `-H` | — | Extra request header, repeatable |
| `--ua` | — | UA preset: `chrome`, `mobile`, `firefox`, `safari`, `bot` |
| `--user-agent` | — | Custom User-Agent string |
| `--rate-limit` | `0` | Seconds between requests |
| `--workers` | `6` | Threads for JS fetching |
| `--verbose` / `-v` | off | Log each crawled URL to stderr |
| `--no-color` | off | Disable ANSI output |

---

## Examples

```bash
# Basic
python3 apipie.py --url https://app.example.com

# Deeper crawl, JSON output
python3 apipie.py --url https://app.example.com --max-depth 8 --format json -o endpoints.json

# Authenticated scan
python3 apipie.py --url https://app.example.com \
  -H "Cookie: session=abc123" \
  -H "Authorization: Bearer eyJhbGc..."

# Bypass 403 with a browser UA
python3 apipie.py --url https://app.example.com --ua mobile

# Throttle requests
python3 apipie.py --url https://app.example.com --rate-limit 0.5
```

---

## Output

Reports are split into REST, GraphQL, and RPC sections.

REST endpoints are grouped by path prefix. Each entry includes URL, method, source page/script, and a ready `curl` command.

GraphQL entries list the endpoint URL alongside all detected operations (query/mutation/subscription names). RPC entries list discovered method names (JSON-RPC, tRPC procedures, Socket.IO events).

Pass `--format json` to get a flat JSON array instead, useful for piping into other tools.

---

## Project Structure

```
apipie/
├── apipie.py           # entry point
├── cli.py              # argument parsing, terminal output
├── crawler.py          # BFS walker, JS ingestion, endpoint registration
├── client.py           # HTTP session, UA presets, response size cap
├── infer.py            # method inference from URL path keywords
├── models.py           # Hit, Endpoint, EndpointStore
├── reporter.py         # Markdown and JSON rendering
├── resolve.py          # URL normalization, template variable handling
├── color.py            # ANSI helpers, banner
├── requirements.txt
└── extractors/
    ├── __init__.py     # runs all JS extractors
    ├── html.py         # form actions, data-url attrs, script tags
    ├── fetch.py
    ├── axios.py
    ├── xhr.py
    ├── jquery.py
    ├── angular.py
    ├── superagent.py
    ├── paths.py        # hardcoded path strings
    ├── graphql.py
    └── rpc.py
```

---

## Method Inference

When a source provides no explicit HTTP method, apipie falls back to path-keyword matching:

| Method | Keywords |
|---|---|
| `DELETE` | `delete`, `remove`, `destroy`, `purge`, `revoke` |
| `PATCH` | `update`, `edit`, `patch`, `modify`, `change`, `rename` |
| `POST` | `create`, `add`, `submit`, `login`, `register`, `upload`, `save`, `generate`, `otp`, `verify`, `validate`, `authenticate`, `token`, `search`, `query`, `subscribe`, `checkout` |
| `GET` | everything else |

---

## Extending

Each extractor exposes one function:

```python
def extract(js: str) -> list[Hit]: ...
```

To add support for a new library (e.g. `ky`):

1. Create `extractors/ky.py` implementing `extract(js: str) -> list[Hit]`.
2. Add it to `_JS_EXTRACTORS` in `extractors/__init__.py`.

---

## License

MIT
