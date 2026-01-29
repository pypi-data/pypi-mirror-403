"""utility functions for natal"""

from datetime import datetime, timezone
from natal.classes import Aspectable
from natal.config import Config
from pathlib import Path
from tagit import svg
from typing import Iterable


def color_hex(name: str, config: Config = Config()) -> str:
    """Get color hex code from name and config.

    Args:
        name (str): Color name to look up
        config (Config): Config containing color definitions

    Returns:
        str: Hex color code string
    """
    return getattr(config.colors, name)


def pairs[T](iterable: Iterable[T]) -> list[tuple[T, T]]:
    """Generate unique pairs of elements from an iterable.

    Args:
        iterable (Iterable[T]): Source of elements to pair

    Returns:
        list[tuple[T, T]]: List of element pairs as tuples
    """
    output = []
    for i in range(len(iterable)):
        for j in range(i + 1, len(iterable)):
            output.append((iterable[i], iterable[j]))
    return output


def member_of[T](const: list[T], name: str) -> T:
    """Get a member from a list of constants by name.

    Args:
        const (list[T]): List of constant definitions
        name (str): Name to look up

    Returns:
        T: Matching constant member
    """
    idx: int = const["name"].index(name)
    return {prop: const[prop][idx] for prop in const.model_fields}


def str_to_dt(dt_str: str) -> datetime:
    """Convert string to datetime object.

    Args:
        dt_str (str): Datetime string in format "YYYY-MM-DD HH:MM"

    Returns:
        datetime: Parsed datetime object
    """
    return datetime.strptime(dt_str[:16], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)


def apply_utc(dt: datetime) -> datetime:
    """apply UTC timezone to datetime object"""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    elif dt.tzinfo == timezone.utc:
        return dt
    else:
        return dt.astimezone(timezone.utc)


# stats and pdf report =========================================================

symbol_to_svg_filename = {
    "☉": "sun",
    "☽": "moon",
    "☿": "mercury",
    "♀": "venus",
    "♂": "mars",
    "♃": "jupiter",
    "♄": "saturn",
    "♅": "uranus",
    "♆": "neptune",
    "♇": "pluto",
    "☊": "north_node",
    "☋": "south_node",
    "⚷": "chiron",
    "⚳": "ceres",
    "⚴": "pallas",
    "⚵": "juno",
    "⚶": "vesta",
    "♈": "aries",
    "♉": "taurus",
    "♊": "gemini",
    "♋": "cancer",
    "♌": "leo",
    "♍": "virgo",
    "♎": "libra",
    "♏": "scorpio",
    "♐": "sagittarius",
    "♑": "capricorn",
    "♒": "aquarius",
    "♓": "pisces",
    "℞": "retrograde",
    "☌": "conjunction",
    "☍": "opposition",
    "△": "trine",
    "□": "square",
    "⚹": "sextile",
    "⚻": "quincunx",
    "🜂": "fire",
    "🜃": "earth",
    "🜁": "air",
    "🜄": "water",
    "⟑": "cardinal",
    "⊟": "fixed",
    "𛰣": "mutable",
    "⏫": "domicile",
    "🔼": "exaltation",
    "⏬": "detriment",
    "🔽": "fall",
}


def svg_tag(name: str, scale: float = 0.5, color: str = "#595959") -> str:
    """generates an SVG tag of a given symbol name"""
    if not name:
        return ""
    stroke = color
    fill = "none"
    if name in ["mc", "asc", "dsc", "ic"]:
        stroke = "none"
        fill = color

    return svg(
        (Path(__file__).parent / "svg_paths" / f"{name}.svg").read_text(),
        fill=fill,
        stroke=stroke,
        stroke_width=3 * scale,
        version="1.1",
        width=f"{20 * scale}px",
        height=f"{20 * scale}px",
        transform=f"scale({scale})",
        xmlns="http://www.w3.org/2000/svg",
    )


def dignity_of(
    body: Aspectable,
    labels: list[str] = ["domicile", "exaltation", "detriment", "fall"],
) -> str:
    """get the dignity of a celestial body"""
    if body.name == (body.sign.classic_ruler or body.sign.ruler):
        return labels[0]
    if body.name == body.sign.exaltation:
        return labels[1]
    if body.name == (body.sign.classic_detriment or body.sign.detriment):
        return labels[2]
    if body.name == body.sign.fall:
        return labels[3]
    return ""


def body_name_to_svg(grid: list[list[str]]):
    """convert grid to SVG"""
    for row in grid:
        for i, cell_txt in enumerate(row):
            row[i] = string_to_svg(cell_txt)
    return grid


def string_to_svg(text: str) -> str:
    """convert string to SVG"""
    output = ""
    for char in text:
        filename = symbol_to_svg_filename.get(char)
        output += svg_tag(filename) if filename else char
    return output
