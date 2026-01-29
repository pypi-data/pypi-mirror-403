"""Search foir folkways records."""

from typing import (
    Final,
    TypedDict,
)
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from beetsplug.folkways.definitions import BASE_URL, FolkwaysId, GetFunction
from beetsplug.folkways.http import get as http_get

SEARCH_URL: Final[str] = urljoin(BASE_URL, "search")
RESULTS_PER_PAGE: Final[int] = 40


class SearchPayload(TypedDict):
    query: str
    releasePageNum: str


def search(
    query: str,
    limit: int | None = None,
    get: GetFunction = http_get,
) -> list[FolkwaysId]:
    """
    Search for folkways record with the specified query, returning at most `limit` results.

    Properly handle pagination.
    """
    ids: list[FolkwaysId] = []

    page_results = _search_page(query, 1, get)
    ids.extend(page_results)

    current_page: int = 2
    while (limit is None or len(ids) < limit) and len(page_results) > 0:
        page_results = _search_page(query, current_page, get)
        ids.extend(page_results)
        current_page += 1

    return ids[:limit]


def _search_page(query: str, page: int, get: GetFunction) -> list[FolkwaysId]:
    """Search for folkways record with the provided query, returning the results on the specified page."""
    payload: SearchPayload = {"query": query, "releasePageNum": str(page)}
    html = get(SEARCH_URL, payload)
    soup = BeautifulSoup(html, "html.parser")

    title_links = soup.select(
        "#releases ul.releases-flex li.album-card div.details div.details-inner a.title"
    )
    hrefs = [link.get("href") for link in title_links]

    return [FolkwaysId(urljoin(BASE_URL, str(href))) for href in hrefs]
