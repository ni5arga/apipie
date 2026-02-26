from . import fetch, axios, xhr, jquery, angular, superagent, paths, graphql, rpc
from .html import (
    extract_forms,
    extract_data_urls,
    extract_script_srcs,
    extract_inline_js,
    extract_links,
)

_JS_EXTRACTORS = (fetch, axios, xhr, jquery, angular, superagent, paths, graphql, rpc)


def extract_from_js(js: str) -> list:
    hits = []
    for mod in _JS_EXTRACTORS:
        hits.extend(mod.extract(js))
    return hits


__all__ = [
    "extract_from_js",
    "extract_forms",
    "extract_data_urls",
    "extract_script_srcs",
    "extract_inline_js",
    "extract_links",
]
