from enum import StrEnum
from pydantic import BaseModel, Field
from types import SimpleNamespace
from typing import Any, Iterator, Literal, Mapping

ThemeType = Literal["light", "dark", "mono"]


class Dictable(Mapping):
    """
    Protocols for subclasses to behave like a dict.
    """

    def __getitem__(self, key: str, default: Any = None):
        return getattr(self, key, default)

    def __setitem__(self, key: str, value: Any) -> None:
        setattr(self, key, value)

    def __iter__(self) -> Iterator[str]:
        return iter(self.__dict__)

    def __len__(self) -> int:
        return len(self.__dict__)

    def __delitem__(self, key: Any, /) -> None:
        return super().__delattr__(key)

    def __contains__(self, key: Any) -> bool:
        if not isinstance(key, str):
            raise TypeError("only string keys are supported in the Mapping super class")
        return hasattr(self, key)

    def update(self, other: Mapping[str, Any] | None = None, **kwargs) -> None:
        """
        Update the attributes with elements from another mapping or from key/value pairs.

        Args:
            other (Mapping[str, Any] | None): A mapping object to update from.
            **kwargs: Additional key/value pairs to update with.
        """
        if other is not None:
            for key, value in other.items():
                setattr(self, key, value)
        for key, value in kwargs.items():
            setattr(self, key, value)

    def setdefault(self, key: str, value: Any) -> None:
        """
        Set a default value for a key if it is not already set.
        """
        if not hasattr(self, key):
            setattr(self, key, value)


class DotDict(SimpleNamespace, Dictable):
    """
    Extends SimpleNamespace to allow for unpacking and subscript notation access.
    """

    pass


class ModelDict(BaseModel, Dictable):
    """
    Extends BaseModel to allow for unpacking and subscript notation access.
    """

    # override to return keys, otherwise BaseModel.__iter__ returns key value pairs
    def __iter__(self) -> Iterator[str]:
        return iter(self.__dict__)


class HouseSys(StrEnum):
    Placidus = "P"
    Whole_Sign = "W"
    Equal = "E"
    Koch = "K"
    Porphyry = "O"
    Regiomontanus = "R"
    Campanus = "C"


class Orb(ModelDict):
    """default orb for natal chart"""

    conjunction: int = 7
    opposition: int = 6
    trine: int = 6
    square: int = 6
    sextile: int = 5
    quincunx: int = 0


class Theme(ModelDict):
    """
    Default colors for the chart.
    """

    fire: str = "#ef476f"  # fire, square, Asc
    earth: str = "#ffd166"  # earth, MC
    air: str = "#06d6a0"  # air, trine
    water: str = "#81bce7"  # water, opposition
    points: str = "#118ab2"  # lunar nodes, sextile
    asteroids: str = "#AA96DA"  # asteroids, quincunx
    positive: str = "#FFC0CB"  # positive
    negative: str = "#AD8B73"  # negative
    others: str = "#FFA500"  # conjunction
    transparency: float = 0.1
    foreground: str
    background: str
    dim: str


class LightTheme(Theme):
    """
    Default light colors.
    """

    foreground: str = "#758492"
    background: str = "#FFFDF1"
    dim: str = "#A4BACD"


class DarkTheme(Theme):
    """
    Default dark colors.
    """

    foreground: str = "#F7F3F0"
    background: str = "#343a40"
    dim: str = "#515860"


class Display(ModelDict):
    """
    Display settings for celestial bodies.
    """

    sun: bool = True
    moon: bool = True
    mercury: bool = True
    venus: bool = True
    mars: bool = True
    jupiter: bool = True
    saturn: bool = True
    uranus: bool = True
    neptune: bool = True
    pluto: bool = True
    north_node: bool = True
    south_node: bool = False
    chiron: bool = False
    ceres: bool = False
    pallas: bool = False
    juno: bool = False
    vesta: bool = False
    asc: bool = True
    ic: bool = False
    dsc: bool = False
    mc: bool = False


class ChartConfig(ModelDict):
    """
    Chart configuration settings.

    font_size_fraction: the size of the symbols, compared to the radius
    inner_min_degree / outer_min_degree: the minimum degree separation between celestial bodies, to prevent overlap
    margin_factor: the length of stroke compared to the radius, outside the outer circle of the 4 vertex lines
    ring_thickness_fraction: the thickness of the sign and house rings, compared to the radius
    scale_adj_factor: the number divide the chart width, to create scale adjustment for symbols
    pos_adj_factor: the number divide the font size, to create position adjustment for symbols
    """

    stroke_width: int = 1
    stroke_opacity: float = 1
    font: str = "sans-serif"
    font_size_fraction: float = 0.55
    inner_min_degree: float = 9
    outer_min_degree: float = 8
    margin_factor: float = 0.04
    ring_thickness_fraction: float = 0.15
    # hard-coded 2.2 and 600 due to the original symbol svg size = 20x20
    scale_adj_factor: float = 600
    pos_adj_factor: float = 2.2


class Config(ModelDict):
    """
    Package configuration model.
    """

    theme_type: ThemeType = "dark"
    house_sys: HouseSys = Field(default=HouseSys.Placidus, frozen=True)
    orb: Orb = Field(default_factory=Orb, frozen=True)
    light_theme: LightTheme = LightTheme()
    dark_theme: DarkTheme = DarkTheme()
    display: Display = Field(default_factory=Display, frozen=True)
    chart: ChartConfig = ChartConfig()

    @property
    def theme(self) -> Theme:
        """
        Return theme colors based on the theme type.

        Returns:
            Theme: The theme colors.
        """
        match self.theme_type:
            case "light":
                return self.light_theme
            case "dark":
                return self.dark_theme
            case "mono":
                kwargs = {key: "#888888" for key in self.light_theme.model_dump()}
                kwargs["background"] = "#FFFFFF"
                kwargs["transparency"] = 0
                return Theme(**kwargs)
