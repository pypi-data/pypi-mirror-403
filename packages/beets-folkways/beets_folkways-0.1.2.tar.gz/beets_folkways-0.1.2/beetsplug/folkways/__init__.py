"""
Beets metadata plugin for folkways releases (https://folkways.si.edu/).
"""

from typing import (
    Iterable,
    Sequence,
)

from beets.autotag.hooks import AlbumInfo, TrackInfo
from beets.library import Item
from beets.metadata_plugins import MetadataSourcePlugin

from beetsplug.folkways.definitions import FolkwaysId
from beetsplug.folkways.record import FolkwaysRecord, get_tracks
from beetsplug.folkways.record import get as get_record
from beetsplug.folkways.search import search
from beetsplug.folkways.track import FolkwaysTrack
from beetsplug.folkways.track import get as get_track


def _from_folkways_to_beets_record(record: FolkwaysRecord) -> AlbumInfo:
    """
    Convert FolkwaysRecord into AlbumInfo.

    If there are are mutliple artists, set the main artist as 'Various Artists'.
    """
    artist = "Unknown Artist"
    if artists := record.artists:
        artist = artists[0] if len(artists) == 1 else "Various Artists"

    return AlbumInfo(
        album=record.title,
        album_id=record.id,
        artist=artist,
        artists=record.artists,
        year=record.release_years[0],
        label=record.label,
        catalognum=record.catalog_nrs[0],
        cover_art_url=record.cover_art_url,
        tracks=[_from_folkways_to_beets_track(track) for track in record.tracks]
        if record.tracks is not None
        else [],
    )


def _from_folkways_to_beets_track(track: FolkwaysTrack) -> TrackInfo:
    """
    Convert FolkwaysTrack into TrackInfo.
    """
    return TrackInfo(
        title=track.title,
        length=track.duration,
        artists=track.artists,
        index=track.track_nr,
    )


class FolkwaysPlugin(MetadataSourcePlugin):
    """Fetch metadata for folkways releases and convert them to beets format."""

    def _fetch_full_record(self, id: FolkwaysId) -> AlbumInfo:
        """Fetch the folkways record with the specified id and all its tracks."""
        record = get_record(id)
        record.tracks = get_tracks(id)

        return _from_folkways_to_beets_record(record)

    def album_for_id(self, album_id: str) -> AlbumInfo:
        """Fetch the folkways record with the specified id and all its tracks."""
        return self._fetch_full_record(FolkwaysId(album_id))

    def track_for_id(self, track_id: str):
        """Fetch the folkways track with the specified id."""
        return _from_folkways_to_beets_track(get_track(FolkwaysId(track_id)))

    def candidates(
        self, items: Sequence[Item], artist: str, album: str, va_likely: bool
    ) -> Iterable[AlbumInfo]:
        """
        Fetch folkways record that are a close match to the provided artist and album.

        Use the configured limit as a maximum.
        """
        self._log.debug(f"Folkways candidates called: {artist} - {album}")
        limit = self.config["search_limit"].get()
        return self.get_albums(f"{artist} {album}" if va_likely else album, limit)

    def item_candidates(self, item: Item, artist: str, title: str):
        """TODO: figure out how to implement this, I do not need it for now"""
        pass

    def get_albums(self, query: str, limit: int) -> Iterable[AlbumInfo]:
        """Fetch folkways record fitting the provided query up to the specified limit."""
        candidate_ids = search(query, limit)
        candidate_records = [
            self._fetch_full_record(FolkwaysId(id)) for id in candidate_ids
        ]

        return candidate_records
