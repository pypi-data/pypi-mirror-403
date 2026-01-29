from beetsplug.folkways.track import get as get_track
from beetsplug.folkways.definitions import BASE_URL


def get(query: str, params: dict[str, str] = {}) -> str:
    filename = query.replace(BASE_URL, "").replace("/", "_")
    filename = "tests/html/track/{}.html".format(filename)
    with open(
        filename,
        "r",
        encoding="utf-8",
    ) as file:
        content = file.read()
        return content


def test_rio_grande():
    r = get_track(
        "https://folkways.si.edu/alan-mills/rio-grande/celtic-world/music/track/smithsonian",
        get,
    )
    assert r.title == "Rio Grande"
    assert r.catalog_nrs == ["FW02312_101"]
    assert r.track_nr == 1
    assert r.duration == 109
    assert r.artists == ["Alan Mills"]
    assert r.credits == [
        "Alan Mills - Lead vocals",
        "Gilbert Lacombe - Acoustic guitar",
    ]


def test_round_and_round_the_bar_room():
    r = get_track(
        "https://folkways.si.edu/nat-saunders/round-and-round-the-bar-room/central-asia-islamica-world/music/track/smithsonian",
        get,
    )
    assert r.title == "Round and Round the Bar-Room"
    assert r.catalog_nrs == ["SFW40471_104"]
    assert r.track_nr == 4
    assert r.duration == 210
    assert r.artists == ["Nat Saunders"]
    assert r.credits == [
        "Nat Saunders - Lead vocals",
        "Unspecified - Banjo, Percussion",
    ]


def test_pretty_fair_miss_in_the_garden():
    r = get_track(
        "https://folkways.si.edu/martin-young-and-corbett-grigsby/pretty-fair-miss-in-the-garden/american-folk-old-time/music/track/smithsonian",
        get,
    )
    assert r.title == "Pretty Fair Miss in the Garden"
    assert r.catalog_nrs == ["SFW40077_166"]
    assert r.track_nr == 66
    assert r.duration == 320
    assert r.artists == ["Martin Young", "Corbett Grigsby"]
    assert r.credits == [
        "Martin Young - Lead vocals",
    ]
