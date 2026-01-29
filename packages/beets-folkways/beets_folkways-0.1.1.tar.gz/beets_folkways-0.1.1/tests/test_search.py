from beetsplug.folkways.search import search


def get(query: str, params: dict[str, str]) -> str:
    filename = params["query"].replace(" ", "_")
    filename = "tests/html/search/{}.{}.html".format(filename, params["releasePageNum"])
    with open(
        filename,
        "r",
        encoding="utf-8",
    ) as file:
        content = file.read()
        return content


def test_no_results_len():
    results = search("flubbergnabber", None, get)
    assert len(results) == 0


def test_songs_of_the_sea_len():
    results = search("songs of the sea", None, get)
    assert len(results) == 20


def test_alan_mills_songs_of_the_sea_len():
    results = search("alan mills songs of the sea", None, get)
    assert len(results) == 1


def test_songs_of_the_sea_limit():
    results = search("songs of the sea", 5, get)
    assert len(results) == 5
