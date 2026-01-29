"""
Shared functionality to extract information out of folkways information boxes.

Some might work better with taking the meta tags into consideration but theys seem to be even more inconsistent.
"""

from typing import (
    Any,
    Callable,
)
import re
from bs4 import ResultSet, Tag


def get_single(html: Tag) -> str | None:
    """Return the stripped text of a single value info box."""
    return (
        value_tag.text.strip() if (value_tag := html.select_one("div.copy")) else None
    )


def get_multi_split(html: Tag) -> list[str] | None:
    """Split the value of an info box by ',' and ';' and return the result as a list."""
    if value_tag := html.select_one("div.copy"):
        return [value.strip() for value in re.split(",|;", value_tag.text)]
    return None


def get_multi(html: Tag) -> list[str]:
    """Return all values of a list info box."""
    return [
        " ".join(re.split(r";|\s+", value.text)).strip().rstrip(",")
        for value in html.select("div.copy span")
    ]


def _html_info_to_dict(
    html: ResultSet[Tag],
    extractors: dict[str, Callable],
    key_map: dict[str, str],
) -> dict[str, str | list[str]]:
    """
    Transform a folkways info box into a dictionary.

    Use the provided extractors to get the values and then the key_map to transform the keys.
    """
    data = {}
    for inner_html in html:
        if (title := inner_html.select_one("h4")) and title.text in extractors:
            value = extractors[title.text](inner_html)
            data[key_map[title.text]] = value

    return data


def from_info_html(
    html: ResultSet[Tag],
    extractors: dict[str, Callable],
    key_map: dict[str, str],
    value_map: dict[str, Callable[[Any], Any]],
) -> dict[str, Any]:
    """
    Transform a folkways info box into a dictionary.

    Use the provided extractors to get the values, then the key_map to
    transform the keys and finally the value_map to transform the values.
    """
    info_data = _html_info_to_dict(html, extractors, key_map)
    info_data_transformed: dict[str, Any] = {
        key: value_map[key](value) if key in value_map else value
        for key, value in info_data.items()
    }

    return info_data_transformed
