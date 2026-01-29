from . import data1, data2, person1
from natal.config import Config, Display
from natal.stats import Data, Stats
from pytest import fixture


@fixture(scope="module")
def stats(data1):
    return Stats(data1=data1, city1=("Hong Kong", "HK"), tz1="Asia/Hong_Kong")


@fixture(scope="module")
def composite_stats(data1, data2):
    return Stats(
        data1=data1,
        data2=data2,
        city1=("Hong Kong", "HK"),
        tz1="Asia/Hong_Kong",
        city2=("Hong Kong", "HK"),
        tz2="Asia/Hong_Kong",
    )


@fixture
def info():
    return list(
        zip(
            ["name", "city", "coordinates", "local time"],
            ("shing", ("Hong Kong", "HK"), "22.2783°N 114.175°E", "1976-04-20 18:58"),
        )
    )


@fixture
def composite_info():
    return list(
        zip(
            ["name", "city", "coordinates", "local time"],
            ("shing", ("Hong Kong", "HK"), "22.2783°N 114.175°E", "1976-04-20 18:58"),
            ("belle", ("Hong Kong", "HK"), "22.2783°N 114.175°E", "2011-01-23 08:44"),
        )
    )


@fixture
def celestial_bodies():
    return [
        ["body", "sign", "house", "dignity"],
        ["☉", "00° ♉ 26'", "7", ""],
        ["☽", "19° ♑ 47'", "3", "detriment"],
        ["☿", "18° ♉ 30'", "7", ""],
        ["♀", "14° ♈ 49'", "6", "detriment"],
        ["♂", "15° ♋ 54'", "9", "fall"],
        ["♃", "05° ♉ 52'", "7", ""],
        ["♄", "26° ♋ 31'", "10", "detriment"],
        ["♅", "05° ♏ 19' ℞", "1", ""],
        ["♆", "13° ♐ 38' ℞", "2", ""],
        ["♇", "09° ♎ 47' ℞", "12", ""],
        ["☋", "13° ♉ 25' ℞", "7", ""],
        ["Asc", "20° ♎ 32'", "1", ""],
    ]


@fixture
def data2_celestial_bodies():
    return [
        ["body", "sign", "house", "dignity"],
        ["☉", "02° ♒ 38'", "4", "detriment"],
        ["☽", "15° ♍ 46'", "11", ""],
        ["☿", "12° ♑ 25'", "3", ""],
        ["♀", "16° ♐ 22'", "2", ""],
        ["♂", "05° ♒ 32'", "4", ""],
        ["♃", "00° ♈ 03'", "6", ""],
        ["♄", "17° ♎ 13'", "12", "exaltation"],
        ["♅", "27° ♓ 37'", "6", ""],
        ["♆", "27° ♒ 26'", "5", ""],
        ["♇", "06° ♑ 05'", "3", ""],
        ["☊", "01° ♑ 08' ℞", "3", ""],
        ["Asc", "00° ♓ 24'", "5", ""],
    ]


@fixture
def houses():
    return [
        ["house", "cusp", "celestial bodies 1", "celestial bodies 2", "sum"],
        ["1", "20° ♎ 32'", "♅, Asc", "", "2"],
        ["2", "19° ♏ 43'", "♆", "♀", "2"],
        ["3", "19° ♐ 49'", "☽", "☿, ♇, ☊", "4"],
        ["4", "20° ♑ 36'", "", "☉, ♂", "2"],
        ["5", "21° ♒ 53'", "", "♆, Asc", "2"],
        ["6", "22° ♓ 29'", "♀", "♃, ♅", "3"],
        ["7", "20° ♈ 32'", "☉, ☿, ♃, ☋", "", "4"],
        ["8", "19° ♉ 43'", "", "", ""],
        ["9", "19° ♊ 49'", "♂", "", "1"],
        ["10", "20° ♋ 36'", "♄", "", "1"],
        ["11", "21° ♌ 54'", "", "☽", "1"],
        ["12", "22° ♍ 29'", "♇", "♄", "2"],
    ]


@fixture
def elements_vs_modalities():
    return [
        ["", "fire", "air", "water", "earth", "sum"],
        ["cardinal", "♀", "♇, Asc", "♂, ♄", "☽", "6"],
        ["fixed", "", "", "♅", "☉, ☿, ♃, ☋", "5"],
        ["mutable", "♆", "", "", "", "1"],
        ["sum", "2", "2", "3", "5", ""],
        ["polarity", "null:4 pos", "null:8 neg", ""],
    ]


@fixture
def quadrants_vs_hemispheres():
    return [
        ["", "eastern", "western", "sum"],
        ["southern", "♄, ♇", "☉, ☿, ♂, ♃, ☋", "7"],
        ["northern", "☽, ♅, ♆", "♀", "4"],
        ["sum", "5", "6", ""],
    ]


@fixture
def composite_aspect_grid():
    return [
        ["", "☉", "☽", "☿", "♀", "♂", "♃", "♄", "♅", "♆", "♇", "☊", "Asc", "sum"],
        ["☉", "□", "", "", "", "□", "", "", "", "⚹", "△", "△", "⚹", "6"],
        ["☽", "", "△", "", "", "", "", "□", "", "", "", "", "", "2"],
        ["☿", "", "△", "", "", "", "", "", "", "", "", "", "", "1"],
        ["♀", "", "", "□", "△", "", "", "☍", "", "", "", "", "", "3"],
        ["♂", "", "⚹", "☍", "", "", "", "□", "", "", "", "", "", "3"],
        ["♃", "□", "", "", "", "□", "", "", "", "", "△", "△", "", "4"],
        ["♄", "", "", "", "", "", "△", "", "△", "", "", "", "", "2"],
        ["♅", "□", "", "", "", "□", "", "", "", "", "⚹", "⚹", "△", "5"],
        ["♆", "", "□", "", "☌", "", "", "⚹", "", "", "", "", "", "3"],
        ["♇", "", "", "□", "", "△", "", "", "", "", "□", "", "", "3"],
        ["☋", "", "△", "△", "", "", "", "", "", "", "", "", "", "2"],
        ["Asc", "", "", "", "⚹", "", "", "☌", "", "", "", "", "", "2"],
    ]


def test_info_grid(stats, info):
    assert stats.basic_info() == info


def test_composite_info_grid(composite_stats, composite_info):
    assert composite_stats.basic_info() == composite_info


def test_celestial_bodies(stats, celestial_bodies):
    assert stats.celestial_bodies(1) == celestial_bodies


def test_data2_celestial_bodies(composite_stats, data2_celestial_bodies):
    assert composite_stats.celestial_bodies(2) == data2_celestial_bodies


def test_houses(composite_stats, houses):
    assert composite_stats.houses() == houses


def test_elements_vs_modalities(stats, elements_vs_modalities):
    assert stats.elements_vs_modalities() == elements_vs_modalities


def test_quadrants_vs_hemispheres(stats, quadrants_vs_hemispheres):
    assert stats.quadrants_vs_hemispheres() == quadrants_vs_hemispheres


def test_composite_aspect_grid(composite_stats, composite_aspect_grid):
    assert composite_stats.aspect_grid() == composite_aspect_grid


def test_no_entities():
    display = Display(**dict.fromkeys(Display(), False))
    stats = Stats(data1=Data(**person1, config=Config(display=display)))
    elements_vs_modalities = stats.elements_vs_modalities()
    assert elements_vs_modalities[1][5] == "0"
    assert elements_vs_modalities[2][5] == "0"
    assert elements_vs_modalities[3][5] == "0"
    assert elements_vs_modalities[4][1] == "0"
    assert elements_vs_modalities[4][2] == "0"
    assert elements_vs_modalities[4][3] == "0"
    assert elements_vs_modalities[4][4] == "0"
    quadrants_vs_hemispheres = stats.quadrants_vs_hemispheres()
    assert quadrants_vs_hemispheres[1][3] == "0"
    assert quadrants_vs_hemispheres[2][3] == "0"
    assert quadrants_vs_hemispheres[3][1] == "0"
    assert quadrants_vs_hemispheres[3][2] == "0"
