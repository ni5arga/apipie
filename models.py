from __future__ import annotations

from dataclasses import dataclass, field


HTTP_METHODS = frozenset({"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"})


@dataclass
class Hit:
    url: str
    kind: str = "rest"
    method: str | None = None
    gql_op_type: str | None = None
    gql_op_name: str | None = None
    rpc_method: str | None = None


@dataclass
class Endpoint:
    url: str
    kind: str = "rest"
    methods: set = field(default_factory=set)
    params: dict = field(default_factory=dict)
    sources: set = field(default_factory=set)
    gql_ops: set = field(default_factory=set)
    rpc_methods: set = field(default_factory=set)

    def merge(self, hit: Hit, source: str = ""):
        if hit.method and hit.method in HTTP_METHODS:
            self.methods.add(hit.method)
        if source:
            self.sources.add(source)
        if hit.kind == "graphql" and hit.gql_op_type:
            self.gql_ops.add((hit.gql_op_type, hit.gql_op_name or "anonymous"))
        if hit.kind == "rpc" and hit.rpc_method:
            self.rpc_methods.add(hit.rpc_method)


_KIND_RANK = {"rest": 0, "rpc": 1, "graphql": 2}


class EndpointStore:
    def __init__(self):
        self._map: dict[str, Endpoint] = {}

    def add(self, url: str, hit: Hit, source: str = "", params: dict | None = None):
        if url not in self._map:
            self._map[url] = Endpoint(url=url, kind=hit.kind)
        ep = self._map[url]
        if _KIND_RANK.get(hit.kind, 0) > _KIND_RANK.get(ep.kind, 0):
            ep.kind = hit.kind
        ep.merge(hit, source)
        if params:
            for k, v in params.items():
                ep.params.setdefault(k, []).extend(v)

    def all(self) -> list[Endpoint]:
        return sorted(self._map.values(), key=lambda e: e.url)

    def __len__(self):
        return len(self._map)

    def __bool__(self):
        return bool(self._map)
