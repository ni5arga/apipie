# apipie

Point it at a web app and let it do the work. apipie crawls pages, tears apart JavaScript, and surfaces every API endpoint it can find — REST, GraphQL, and RPC — without touching a single network socket beyond the target. Walk away with a structured Markdown or JSON report, curl examples included.

---

## Features

- Crawls pages up to a configurable depth, staying within the target domain
- Fetches external JavaScript files concurrently
- Extracts API calls from:
  - `fetch()` with optional `{ method }` config
  - `axios`: shorthand (`.get`, `.post`, etc.) and object form
  - `XMLHttpRequest.open()`
  - jQuery `$.ajax`, `$.get`, `$.post`, `$.getJSON`
  - Angular `$http` / `HttpClient`
  - `superagent`
  - Hardcoded REST-style paths (`/api/`, `/v1/`, `/rest/`)
  - HTML `<form action>` and `data-url` / `data-href` / `data-endpoint` attributes
- **GraphQL**: Apollo Client, urql, `graphql-request`, `gql` tagged templates, React hooks (`useQuery`, `useMutation`, `useSubscription`)
- **RPC**: JSON-RPC method names, tRPC procedures + operations, gRPC-web URLs, Socket.IO events
- Template literal cleanup (`${id}` -> `{param}`)
- Deduplication: same endpoint seen across multiple sources is merged
- Kind promotion: if a URL is seen as both REST and GraphQL, it is promoted to GraphQL
- Method inference: endpoints without an explicit HTTP method are assigned one based on URL path keywords
- Output: Markdown (with curl examples) or JSON

---

## Requirements

- Python 3.9+
- `requests`
- `beautifulsoup4`

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
| `--url` | *(required)* | Base URL of the target application |
| `--output` / `-o` | `<domain>_results.md` | Output file path |
| `--max-depth` | `5` | How many link-hops deep to crawl |
| `--max-pages` | `300` | Maximum pages to crawl before stopping |
| `--format` | `md` | Output format: `md` or `json` |
| `--header` / `-H` | - | Extra request header (repeatable) |
| `--ua` | - | UA preset: `chrome`, `mobile`, `firefox`, `safari`, `bot` |
| `--user-agent` | - | Custom User-Agent string (quote in shell) |
| `--rate-limit` | `0` | Minimum seconds between requests |
| `--workers` | `6` | Concurrent threads for JS fetching |
| `--verbose` / `-v` | off | Print each crawled URL to stderr |
| `--no-color` | off | Disable ANSI colored output |

---

## Examples

**Basic scan:**
```bash
python3 apipie.py --url https://app.example.com
```

**Set output file and increase crawl depth:**
```bash
python3 apipie.py --url https://app.example.com --output report.md --max-depth 8
```

**Authenticated scan (pass a session cookie or bearer token):**
```bash
python3 apipie.py --url https://app.example.com \
  -H "Cookie: session=abc123" \
  -H "Authorization: Bearer eyJhbGc..."
```

**Slow down requests to avoid rate limiting:**
```bash
python3 apipie.py --url https://app.example.com --rate-limit 0.5
```

**JSON output (useful for piping into other tools):**
```bash
python3 apipie.py --url https://app.example.com --format json -o endpoints.json
```

**Verbose crawl - see each page as it is visited:**
```bash
python3 apipie.py --url https://app.example.com -v
```

**Bypass 403 with a browser UA preset:**
```bash
python3 apipie.py --url https://app.example.com --ua mobile
```

---

## Output

### Markdown

The Markdown report is split into three sections: REST, GraphQL, and RPC.

**REST section**: groups endpoints by top-level path prefix, e.g. `/api/`, `/v1/`. Each entry shows:

```markdown
#### POST `/api/users`

| | |
|---|---|
| URL | `/api/users` |
| Method | POST |
| Source | https://app.example.com/static/main.js |

\```bash
curl -X POST 'https://app.example.com/api/users'
\```
```

**GraphQL section**: lists each discovered GraphQL endpoint and its detected operations:

```markdown
### `https://app.example.com/graphql`

| | |
|---|---|
| URL | `https://app.example.com/graphql` |
| Method | POST |

**Operations:**

| Type | Name |
|------|------|
| mutation | CreateUser |
| query | GetUser |
| query | ListPosts |
```

**RPC section**: lists JSON-RPC endpoints with method names, tRPC procedures, Socket.IO events:

```markdown
### `https://app.example.com/api/trpc`

**Methods:**

- `posts.create.mutation`
- `posts.list.query`
- `users.getById.query`
```

### JSON

With `--format json`, the output is a JSON array:

```json
[
  {
    "url": "https://app.example.com/api/users",
    "kind": "rest",
    "methods": ["GET", "POST"],
    "params": {},
    "sources": ["https://app.example.com/static/main.js"]
  },
  {
    "url": "https://app.example.com/graphql",
    "kind": "graphql",
    "methods": ["POST"],
    "params": {},
    "sources": ["https://app.example.com/static/app.chunk.js"],
    "gql_operations": [
      { "type": "mutation", "name": "CreateUser" },
      { "type": "query", "name": "GetUser" }
    ]
  },
  {
    "url": "https://app.example.com/api/trpc",
    "kind": "rpc",
    "methods": ["POST"],
    "params": {},
    "sources": ["https://app.example.com/static/app.js"],
    "rpc_methods": ["posts.create.mutation", "posts.list.query"]
  }
]
```

---

## Project Structure

```
apipie/
├── apipie.py                   # entry point shim
├── requirements.txt
├── cli.py                      # argument parsing, output routing
├── crawler.py                  # BFS page walker, script orchestration
├── client.py                   # requests session, UA presets, rate limiting, parallel fetch
├── infer.py                    # URL-based HTTP method inference
├── models.py                   # Hit, Endpoint, EndpointStore
├── reporter.py                 # markdown + json rendering
├── resolve.py                  # URL normalization, template cleaning
├── color.py                    # ANSI terminal colors, banners, padding
└── extractors/
    ├── __init__.py             # barrel: runs all extractors
    ├── html.py                 # forms, data-* attrs, script srcs, links
    ├── fetch.py                # fetch() calls
    ├── axios.py                # axios.create() + shorthand + object form
    ├── xhr.py                  # XMLHttpRequest.open()
    ├── jquery.py               # $.ajax, $.get, $.post
    ├── angular.py              # $http, HttpClient
    ├── superagent.py           # superagent.*
    ├── paths.py                # hardcoded API paths, absolute URL strings
    ├── graphql.py              # Apollo, urql, gql templates, hooks
    └── rpc.py                  # JSON-RPC, tRPC, gRPC-web, Socket.IO
```

---

## Method Inference

When no HTTP method can be determined from the source code directly, apipie infers one from the URL path using keyword matching:

| Inferred method | URL path keywords |
|---|---|
| `POST` | `send`, `create`, `add`, `submit`, `login`, `register`, `upload`, `save`, `generate`, `otp`, `verify`, `validate`, `authenticate`, `token`, `captcha`, `search`, `query`, `subscribe`, `checkout` |
| `DELETE` | `delete`, `remove`, `destroy`, `purge`, `revoke` |
| `PATCH` | `update`, `edit`, `patch`, `modify`, `change`, `rename` |
| `GET` | everything else |

---

## Extending

Each extractor in `apipie/extractors/` exposes a single function:

```python
def extract(js: str) -> list[Hit]:
    ...
```

A `Hit` is:

```python
@dataclass
class Hit:
    url: str
    kind: str = "rest"            # "rest" | "graphql" | "rpc"
    method: str | None = None
    gql_op_type: str | None = None
    gql_op_name: str | None = None
    rpc_method: str | None = None
```

To add a new extractor (e.g. for `test`):

1. Create `extractors/test.py` with an `extract(js: str) -> list[Hit]` function.
2. Import it in `extractors/__init__.py` and add it to `_JS_EXTRACTORS`.

---

## License

MIT
