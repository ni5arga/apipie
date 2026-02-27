from urllib.parse import urljoin

from bs4 import BeautifulSoup


def extract_forms(soup: BeautifulSoup, page_url: str) -> list[tuple[str, str]]:
    results = []
    for form in soup.find_all("form", action=True):
        url = urljoin(page_url, form["action"])
        method = form.get("method", "GET").upper()
        results.append((url, method))
    return results


def extract_data_urls(soup: BeautifulSoup, page_url: str) -> list[str]:
    """Return URLs from data-url and data-endpoint attributes only.
    data-href is intentionally excluded — it is a navigation attribute,
    not an API endpoint signal."""
    results = []
    for tag in soup.find_all(True, attrs={"data-url": True}):
        results.append(urljoin(page_url, tag["data-url"]))
    for tag in soup.find_all(True, attrs={"data-endpoint": True}):
        results.append(urljoin(page_url, tag["data-endpoint"]))
    return results


def extract_script_srcs(soup: BeautifulSoup, page_url: str) -> list[str]:
    return [urljoin(page_url, t["src"]) for t in soup.find_all("script", src=True)]


def extract_inline_js(soup: BeautifulSoup) -> list[str]:
    return [t.string for t in soup.find_all("script", src=False) if t.string]


def extract_links(soup: BeautifulSoup, page_url: str) -> list[str]:
    out = []
    for tag in soup.find_all("a", href=True):
        out.append(urljoin(page_url, tag["href"]).split("#")[0].split("?")[0])
    return out
