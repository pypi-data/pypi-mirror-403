"""Global definitions and constants."""

from typing import (
    Any,
    Callable,
    Final,
    Mapping,
    NewType,
    TypeAlias,
)

BASE_URL: Final[str] = "https://folkways.si.edu/"

GetFunction: TypeAlias = Callable[[str, Mapping[str, Any]], str]

FolkwaysId = NewType("FolkwaysId", str)


class FolkwaysError(Exception):
    """Base Exception for Folkways Communication and Data."""

    pass
