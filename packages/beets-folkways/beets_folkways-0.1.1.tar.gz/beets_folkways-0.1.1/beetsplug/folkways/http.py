"""Abstract http requests."""

from typing import Mapping

import requests

from beetsplug.folkways.definitions import FolkwaysError


class HttpError(FolkwaysError):
    """Failed to communicate with an external API."""

    pass


def get(query: str, params: Mapping[str, str] = {}) -> str:
    """
    Send a http get request with the specified parameters.

    Return the raw text from the response.

    Raise HttpError if something breaks.
    """
    try:
        return requests.get(query, params=params).text
    except requests.exceptions.RequestException as e:
        raise HttpError("Could not fetch data via http") from e
