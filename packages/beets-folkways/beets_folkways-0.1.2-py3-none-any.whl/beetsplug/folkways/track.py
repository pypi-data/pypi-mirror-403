"""Fetch and parse folkways tracks."""

import time
from dataclasses import dataclass
from typing import Any, Callable, Final, Self, TypeAlias

from bs4 import BeautifulSoup, ResultSet, Tag

from beetsplug.folkways.definitions import FolkwaysError, FolkwaysId
from beetsplug.folkways.extract_info import (
    from_info_html,
    get_multi,
    get_multi_split,
    get_single,
)
from beetsplug.folkways.http import get as http_get


def get_track_length(duration: str) -> int | None:
    """
    Return the track length in seconds for a folkways duration like '01:30'.
    (taken from the beets discogs plugin).
    """
    try:
        length = time.strptime(duration, "%M:%S")
    except ValueError:
        return None
    return length.tm_min * 60 + length.tm_sec


_EXTRACTORS: Final[dict[str, Callable]] = {
    "Catalog Number": get_multi_split,
    "Artist(s)": get_multi,
    "Track Number": get_single,
    "Duration": get_single,
    "Language(s)": get_multi,
    "Performer Credit(s)": get_multi,
}

_KEY_MAP: Final[dict[str, str]] = {
    "Catalog Number": "catalog_nrs",
    "Artist(s)": "artists",
    "Track Number": "track_nr",
    "Duration": "duration",
    "Language(s)": "languages",
    "Performer Credit(s)": "credits",
}

_VALUE_MAP: Final[dict[str, Callable[[Any], Any]]] = {
    "track_nr": lambda x: int(x),
    "duration": lambda x: get_track_length(x),
}


class TrackHtmlError(FolkwaysError):
    """Failed to parse track data."""

    pass


@dataclass
class FolkwaysTrack:
    title: str
    catalog_nrs: list[str]
    track_nr: int
    duration: int | None = None
    artists: list[str] | None = None
    languages: list[str] | None = None
    credits: list[str] | None = None

    @classmethod
    def from_html(cls, html: ResultSet[Tag]) -> Self:
        """Convert a html folkways track to its respective dataclass."""
        search_context = html[0]
        if title_tag := search_context.select_one("div.content h1.title"):
            title = title_tag.text.strip()

            track_info = search_context.select("div.sidebar-item.album-info")
            track_data = from_info_html(track_info, _EXTRACTORS, _KEY_MAP, _VALUE_MAP)

            data = {"title": title} | track_data

            return cls(**data)
        else:
            raise TrackHtmlError("missing div.content h1.title")


GetFunction: TypeAlias = Callable[[str], str]


def get(id: FolkwaysId, get: GetFunction = http_get) -> FolkwaysTrack:
    """Fetch the track with the specified id."""
    html = get(id)
    soup = BeautifulSoup(html, "html.parser")
    if root_tag := soup.select("html"):
        return FolkwaysTrack.from_html(root_tag)
    else:
        raise TrackHtmlError("missing html")
