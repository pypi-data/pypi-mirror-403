from . import data1, data2
from natal.ai import AIContext
from pytest import fixture


@fixture(scope="module")
def ai(data1, data2):
    return AIContext(
        data1=data1,
        city1=("Hong Kong", "HK"),
        tz1="Asia/Hong_Kong",
        data2=data2,
        city2=("Hong Kong", "HK"),
        tz2="Asia/Hong_Kong",
    )


@fixture(scope="module")
def element_grid():
    return [
        ["element", "celestial bodies", "sum"],
        ["fire", "♀, ♆", 2],
        ["earth", "☉, ☽, ☿, ♃, ☋", 5],
        ["air", "♇, Asc", 2],
        ["water", "♂, ♄, ♅", 3],
    ]


@fixture(scope="module")
def modality_grid():
    return [
        ["modality", "celestial bodies", "sum"],
        ["cardinal", "☽, ♀, ♂, ♄, ♇, Asc", 6],
        ["fixed", "☉, ☿, ♃, ♅, ☋", 5],
        ["mutable", "♆", 1],
    ]


@fixture(scope="module")
def polarity_grid():
    return [
        ["polarity", "celestial bodies", "sum"],
        ["positive", "♀, ♆, ♇, Asc", 4],
        ["negative", "☉, ☽, ☿, ♂, ♃, ♄, ♅, ☋", 8],
    ]


@fixture
def quadrants():
    return [
        ["quadrants", "celestial bodies", "sum"],
        ["first", "☽, ♅, ♆", 3],
        ["second", "♀", 1],
        ["third", "☉, ☿, ♂, ♃, ☋", 5],
        ["fourth", "♄, ♇", 2],
    ]


@fixture
def hemispheres():
    return [
        ["hemispheres", "celestial bodies", "sum"],
        ["southern", "☉, ☿, ♂, ♃, ☋, ♄, ♇", 7],
        ["northern", "☽, ♅, ♆, ♀", 4],
        ["eastern", "☽, ♅, ♆, ♄, ♇", 5],
        ["western", "♀, ☉, ☿, ♂, ♃, ☋", 6],
    ]


@fixture
def aspects():
    return [
        ["shing's celestial body", "belle's celestial body", "aspect"],
        ["☉", "☉", "square"],
        ["☉", "♃", "square"],
        ["☉", "♅", "square"],
        ["☽", "☽", "trine"],
        ["☽", "☿", "trine"],
        ["☽", "♂", "sextile"],
        ["☽", "♆", "square"],
        ["☽", "☋", "trine"],
        ["☿", "♀", "square"],
        ["☿", "♂", "opposition"],
        ["☿", "♇", "square"],
        ["☿", "☋", "trine"],
        ["♀", "♀", "trine"],
        ["♀", "♆", "conjunction"],
        ["♀", "Asc", "sextile"],
        ["♂", "☉", "square"],
        ["♂", "♃", "square"],
        ["♂", "♅", "square"],
        ["♂", "♇", "trine"],
        ["♃", "♄", "trine"],
        ["♄", "☽", "square"],
        ["♄", "♀", "opposition"],
        ["♄", "♂", "square"],
        ["♄", "♆", "sextile"],
        ["♄", "Asc", "conjunction"],
        ["♅", "♄", "trine"],
        ["♆", "☉", "sextile"],
        ["♇", "☉", "trine"],
        ["♇", "♃", "trine"],
        ["♇", "♅", "sextile"],
        ["♇", "♇", "square"],
        ["☊", "☉", "trine"],
        ["☊", "♃", "trine"],
        ["☊", "♅", "sextile"],
        ["Asc", "☉", "sextile"],
        ["Asc", "♅", "trine"],
    ]


@fixture
def markdown():
    return "#### Quadrants\n|quadrants | celestial bodies | sum | \n|--- | --- | --- | \n|first | ☽, ♅, ♆ | 3 | \n|second | ♀ | 1 | \n|third | ☉, ☿, ♂, ♃, ☋ | 5 | \n|fourth | ♄, ♇ | 2 | \n\n"


def test_distributions(ai, element_grid, modality_grid, polarity_grid):
    assert ai.elements() == element_grid
    assert ai.modalities() == modality_grid
    assert ai.polarities() == polarity_grid


def test_quadrants(ai, quadrants):
    assert ai.quadrants() == quadrants


def test_hemispheres(ai, hemispheres):
    assert ai.hemispheres() == hemispheres


def test_aspects(ai, aspects):
    assert ai.aspects() == aspects


def test_markdown(ai, markdown):
    assert ai.markdown("Quadrants", ai.quadrants()) == markdown
