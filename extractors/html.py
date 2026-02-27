from urllib.parse import urljoin, urlparse, urlunparse

from bs4 import BeautifulSoup


def _dir_url(url: str) -> str:
    p = urlparse(url)
    last = p.path.rstrip("/").rsplit("/", 1)[-1]
    if "." not in last:
        p = p._replace(path=p.path.rstrip("/") + "/")
    return urlunparse(p)


def extract_forms(soup: BeautifulSoup, page_url: str) -> list[tuple[str, str]]:
    base = _dir_url(page_url)
    results = []
    for form in soup.find_all("form", action=True):
        url = urljoin(base, form["action"])
        method = form.get("method", "GET").upper()
        results.append((url, method))
    return results


def extract_data_urls(soup: BeautifulSoup, page_url: str) -> list[str]:
    """Return URLs from data-url and data-endpoint attributes only.
    data-href is intentionally excluded — it is a navigation attribute,
    not an API endpoint signal."""
    base = _dir_url(page_url)
    results = []
    for tag in soup.find_all(True, attrs={"data-url": True}):
        results.append(urljoin(base, tag["data-url"]))
    for tag in soup.find_all(True, attrs={"data-endpoint": True}):
        results.append(urljoin(base, tag["data-endpoint"]))
    return results


def extract_script_srcs(soup: BeautifulSoup, page_url: str) -> list[str]:
    base = _dir_url(page_url)
    return [urljoin(base, t["src"]) for t in soup.find_all("script", src=True)]


def extract_inline_js(soup: BeautifulSoup) -> list[str]:
    return [t.string for t in soup.find_all("script", src=False) if t.string]


def extract_links(soup: BeautifulSoup, page_url: str) -> list[str]:
    base = _dir_url(page_url)
    out = []
    for tag in soup.find_all("a", href=True):
        out.append(urljoin(base, tag["href"]).split("#")[0].split("?")[0])
    return out
