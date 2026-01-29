"""Fetch and parse folkways records."""

from dataclasses import dataclass
from typing import (
    Any,
    Callable,
    Final,
    TypeAlias,
)
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from beetsplug.folkways.definitions import BASE_URL, FolkwaysError, FolkwaysId
from beetsplug.folkways.extract_info import (
    from_info_html,
    get_multi,
    get_multi_split,
    get_single,
)
from beetsplug.folkways.http import get as http_get
from beetsplug.folkways.track import FolkwaysTrack
from beetsplug.folkways.track import get as get_track

_EXTRACTORS: Final[dict[str, Callable]] = {
    "Catalog Number(s)": get_multi_split,
    "Catalog Number": get_multi_split,
    "Year(s) Released": get_multi_split,
    "Year of Release": get_multi_split,
    "Label(s)/Collection(s)": get_single,
    "Label/Collection": get_single,
    "Artist(s)": get_multi,
    "Country(s)": get_multi,
    "Genre(s)": get_multi,
    "Instrument(s)": get_multi,
    "Language(s)": get_multi,
    "Credit(s)": get_multi,
}

_KEY_MAP: Final[dict[str, str]] = {
    "Catalog Number(s)": "catalog_nrs",
    "Catalog Number": "catalog_nrs",
    "Year(s) Released": "release_years",
    "Year of Release": "release_years",
    "Label(s)/Collection(s)": "label",
    "Label/Collection": "label",
    "Artist(s)": "artists",
    "Country(s)": "countries",
    "Genre(s)": "genres",
    "Instrument(s)": "instruments",
    "Language(s)": "languages",
    "Credit(s)": "credits",
}

_VALUE_MAP: Final[dict[str, Callable[[Any], Any]]] = {
    "release_years": lambda x: list(map(int, x)),
}


@dataclass
class FolkwaysRecord:
    id: str
    title: str
    catalog_nrs: list[str]
    release_years: list[int]
    label: str
    cover_art_url: str | None = None
    artists: list[str] | None = None
    countries: list[str] | None = None
    genres: list[str] | None = None
    instruments: list[str] | None = None
    languages: list[str] | None = None
    credits: list[str] | None = None
    tracks: list[FolkwaysTrack] | None = None


GetFunction: TypeAlias = Callable[[str], str]


class RecordHtmlError(FolkwaysError):
    """Failed to parse record data."""

    pass


def get(id: FolkwaysId, get: GetFunction = http_get) -> FolkwaysRecord:
    """Fetch the folkways record with the provided id, using the specified get function."""
    html = get(id)
    soup = BeautifulSoup(html, "html.parser")

    if title_tag := soup.select_one("main div.content h1.title"):
        cover_art_url = None
        if cover_tag := soup.select_one("main div.content img"):
            cover_art_url = cover_tag.get("src")

        album_info = soup.select("div.sidebar-item.album-info")
        album_data = from_info_html(album_info, _EXTRACTORS, _KEY_MAP, _VALUE_MAP) | {
            "id": id,
            "title": title_tag.text.strip(),
            "cover_art_url": cover_art_url,
        }
        album = FolkwaysRecord(**album_data)

        return album
    else:
        raise RecordHtmlError("missing main div.content h1.title")


def get_tracks(
    record_id: FolkwaysId, get: GetFunction = http_get
) -> list[FolkwaysTrack]:
    """Fetch all tracks of a folkways record with the specified id using the specified get function."""
    html = get(record_id)
    soup = BeautifulSoup(html, "html.parser")

    if track_table := soup.select_one("#track-listing-table"):
        track_links = track_table.select("tr.track div.track-title a")
        track_hrefs = [urljoin(BASE_URL, str(link.get("href"))) for link in track_links]
        tracks = [get_track(FolkwaysId(track_id), get) for track_id in track_hrefs]

        return tracks
    else:
        raise RecordHtmlError("missing #track-listing-table")
