from __future__ import annotations

import re

from models import Hit

_GQL_ENDPOINT = re.compile(
    r"""[`"']((?:https?://[^`"'\s]*)?/(?:graphql|api/graphql|gql|query))[`"']""",
    re.I,
)

_GQL_TEMPLATE = re.compile(
    r"""(?:gql|graphql)\s*`\s*(query|mutation|subscription)\s*(\w*)""",
    re.I,
)

_GQL_STRING = re.compile(
    r"""[`"']\s*(query|mutation|subscription)\s+(\w+)""",
    re.I,
)

_APOLLO_OP = re.compile(
    r"""client\s*\.\s*(query|mutate|subscribe)\s*\(""",
    re.I,
)

_HOOKS = re.compile(
    r"""use(Query|Mutation|Subscription|LazyQuery)\s*\(""",
    re.I,
)

_REQUEST = re.compile(
    r"""(?:request|gqlRequest)\s*\(\s*[`"']([^`"']+)[`"']\s*,\s*(?:[`"']|gql\s*`)\s*(query|mutation|subscription)\s*(\w*)""",
    re.I | re.S,
)

_APOLLO_METHOD_MAP = {"query": "query", "mutate": "mutation", "subscribe": "subscription"}


def extract(js: str) -> list[Hit]:
    hits = []

    for m in _REQUEST.finditer(js):
        hits.append(Hit(
            url=m.group(1),
            kind="graphql",
            method="POST",
            gql_op_type=m.group(2).lower(),
            gql_op_name=m.group(3) or None,
        ))

    for m in _GQL_TEMPLATE.finditer(js):
        hits.append(Hit(
            url="__graphql__",
            kind="graphql",
            method="POST",
            gql_op_type=m.group(1).lower(),
            gql_op_name=m.group(2) or None,
        ))

    for m in _GQL_STRING.finditer(js):
        hits.append(Hit(
            url="__graphql__",
            kind="graphql",
            method="POST",
            gql_op_type=m.group(1).lower(),
            gql_op_name=m.group(2) or None,
        ))

    for m in _APOLLO_OP.finditer(js):
        op = _APOLLO_METHOD_MAP.get(m.group(1).lower(), "query")
        hits.append(Hit(url="__graphql__", kind="graphql", method="POST", gql_op_type=op))

    for m in _HOOKS.finditer(js):
        hook = m.group(1).lower()
        op = "mutation" if "mutation" in hook else "subscription" if "subscription" in hook else "query"
        hits.append(Hit(url="__graphql__", kind="graphql", method="POST", gql_op_type=op))

    for m in _GQL_ENDPOINT.finditer(js):
        hits.append(Hit(url=m.group(1), kind="graphql", method="POST"))

    return hits
