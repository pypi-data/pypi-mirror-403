from beetsplug.folkways.record import get as get_record
from beetsplug.folkways.definitions import BASE_URL


def get(query: str, params: dict[str, str] = {}) -> str:
    filename = query.replace(BASE_URL, "").replace("/", "_")
    filename = "tests/html/record/{}.html".format(filename)
    with open(
        filename,
        "r",
        encoding="utf-8",
    ) as file:
        content = file.read()
        return content


def test_ray_reed_traditional_frontier_and_cowboy_songs():
    r = get_record(
        "https://folkways.si.edu/ray-reed/sings-traditional-frontier-and-cowboy-songs/american-folk/music/album/smithsonian",
        get,
    )
    assert (
        r.id
        == "https://folkways.si.edu/ray-reed/sings-traditional-frontier-and-cowboy-songs/american-folk/music/album/smithsonian"
    )
    assert r.title == "Ray Reed Sings Traditional Frontier and Cowboy Songs"
    assert r.catalog_nrs == ["FW05329", "FD 5329"]
    assert r.release_years == [1977]
    assert r.label == "Folkways Records"
    assert r.artists == ["Ray Reed"]
    assert r.countries == ["United States"]
    assert r.genres == ["American Folk"]
    assert r.instruments == ["Acoustic guitar", "Lead vocals"]
    assert r.languages == ["English"]
    assert r.credits == [
        "Ray Reed - Artist",
        "Ronald Clyne - Designer",
        "Will James - Cover Artwork",
    ]


def test_alan_mills_songs_of_the_sea():
    r = get_record(
        "https://folkways.si.edu/alan-mills/songs-of-the-sea/celtic-world/music/album/smithsonian",
        get,
    )

    assert (
        r.id
        == "https://folkways.si.edu/alan-mills/songs-of-the-sea/celtic-world/music/album/smithsonian"
    )
    assert r.title == "Songs of the Sea"
    assert r.catalog_nrs == ["FW02312", "FA 2312"]
    assert r.release_years == [1957]
    assert r.label == "Folkways Records"
    assert r.artists == ["Alan Mills"]
    assert r.countries == ["Canada", "Ireland", "United Kingdom", "United States"]
    assert r.genres == ["Celtic", "World"]
    assert r.instruments == ["Acoustic guitar", "Lead vocals"]
    assert r.languages == ["English"]
    assert r.credits == [
        "Edith Fulton Fowke - Producer",
        "Four Shipmates - Artist",
        "Alan Mills - Artist",
        "Robert Clyne - Designer",
    ]


def test_mountain_music_of_kentucky():
    r = get_record(
        "https://folkways.si.edu/mountain-music-of-kentucky/american-folk-old-time/album/smithsonian",
        get,
    )

    assert (
        r.id
        == "https://folkways.si.edu/mountain-music-of-kentucky/american-folk-old-time/album/smithsonian"
    )
    assert r.title == "Mountain Music of Kentucky"
    assert r.catalog_nrs == ["SFW40077"]
    assert r.release_years == [1996, 2025]
    assert r.label == "Smithsonian Folkways Recordings"
    assert r.artists is None
    assert r.countries == ["United States"]
    assert r.genres == ["American Folk", "Old Time"]
    assert r.instruments == [
        "Acoustic guitar",
        "Backing vocals",
        "Banjo",
        "Chorus",
        "Fiddle",
        "Hand-clapping",
        "Lead vocals",
        "Percussion",
        "Shrieking",
        "Tambourine",
    ]
    assert r.languages == ["English"]
    assert r.credits == [
        "John Cohen - Recorder, Field Worker, Producer, Liner Notes",
        "David Glasser - Mastering Engineer",
        "Carla Borden - Liner Notes Editor",
        "Visual Dialogue - Designer",
    ]


def test_dan_milner_david_coffin_jeff_davis_civil_war_naval_songs():
    r = get_record(
        "https://folkways.si.edu/dan-milner-david-coffin-jeff-davis/civil-war-naval-songs/american-folk-american-history-historical/music/album/smithsonian",
        get,
    )

    assert (
        r.id
        == "https://folkways.si.edu/dan-milner-david-coffin-jeff-davis/civil-war-naval-songs/american-folk-american-history-historical/music/album/smithsonian"
    )
    assert r.title == "Civil War Naval Songs"
    assert r.catalog_nrs == ["SFW40189"]
    assert r.release_years == [2011]
    assert r.label == "Smithsonian Folkways Recordings"
    assert r.artists == ["Dan Milner", "David Coffin", "Jeff Davis"]
    assert r.countries == ["United States"]
    assert r.genres == ["American Folk", "American History", "Historical Song"]
    assert r.instruments == [
        "Anglo concertina",
        "Banjo",
        "Chorus",
        "Clarinet",
        "Concertina",
        "Drum",
        "Dulcimer",
        "English concertina",
        "Fiddle",
        "Lead vocals",
        "Piano",
        "Piccolo",
        "Trombone",
    ]
    assert r.languages == ["English"]
    assert r.credits == [
        "Dan Milner - Producer, Mixing Engineer, Liner Notes",
        "Gabriel Donohue - Recorder, Mixing Engineer",
        "Mark Thayer - Recorder",
        "Ken Lardner - Recorder",
        "Pete Reiniger - Mastering Engineer",
        "James Bradford - Liner Notes",
        "Galen Lawson - Designer",
        "Communication Visual - Designer",
    ]


def test_folkways_world_music_collection_central_asia_islamica_album_smithsonian():
    r = get_record(
        "https://folkways.si.edu/folkways-world-music-collection/central-asia-islamica/album/smithsonian",
        get,
    )

    assert (
        r.id
        == "https://folkways.si.edu/folkways-world-music-collection/central-asia-islamica/album/smithsonian"
    )
    assert r.title == "Smithsonian Folkways World Music Collection"
    assert r.catalog_nrs == ["SFW40471"]
    assert r.release_years == [1997]
    assert r.label == "Smithsonian Folkways Recordings"
    assert r.artists is None
    assert r.countries == [
        "Australia",
        "Bahamas",
        "Benin",
        "Brazil",
        "Cuba",
        "Ghana",
        "Haiti",
        "Indonesia",
        "Jamaica",
        "Lithuania",
        "Malaysia",
        "Peru",
        "Portugal",
        "Puerto Rico",
        "Russia",
        "Saint Lucia",
        "United States",
        "Uruguay",
        "USSR (former)",
        "Uzbekistan",
    ]
    assert r.genres == ["Central Asia", "Islamica", "World"]
    assert r.instruments == [
        "2-stringed plucked lute",
        "Acoustic guitar",
        "Anak",
        "Backing vocals",
        "Bandoneon",
        "Banjo",
        "Bass guitar",
        "Bata",
        "Berimbau",
        "Bongo",
        "Chinese fiddle",
        "Chorus",
        "Cittern",
        "Clapsticks",
        "Clarinet",
        "Cuatro",
        "Didgeridoo",
        "Drum",
        "Drums",
        "Fiddle",
        "Flute",
        "Gandang",
        "Gong",
        "Gourd",
        "Gourd rattle",
        "Guiro",
        "Hand-clapping",
        "Lead vocals",
        "Metallic percussion",
        "Pahu",
        "Paningkan",
        "Panyaluak",
        "Percussion",
        "Pringting",
        "Pupuik Gadang",
        "Rattle",
        "Saxophone",
        "Side-blown flute",
        "Single-reed aerophone",
        "Stringed instrument",
        "Trumpet",
        "Unspecified",
        "Water sounds",
        "Wind Instrument",
        "Xylophone",
    ]
    assert r.languages == [
        "Akan",
        "Creole",
        "Dalabon",
        "Efe",
        "English",
        "French Creole",
        "Haitian French Creole",
        "Hawaiian (‘Ōlelo Hawai‘I)",
        "Instrumental",
        "Lithuanian",
        "Malay",
        "Ngadha",
        "Portuguese (Português)",
        "Russian",
        "Spanish",
        "Tajik",
        "Temiar",
        "Tuvan (тыва дыл)",
        "Yoruba",
    ]
    assert r.credits == [
        "Charlie Pilzer, Airshow, Springfield, VA - Mastering Engineer",
        "Visual Dialogue - Designer",
        "Anthony Seeger - Compiler, Liner Notes Editor, Liner Notes, Producer",
    ]
