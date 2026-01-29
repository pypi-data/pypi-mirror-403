from dataclasses import dataclass
from natal.const import ASPECT_MEMBERS, SIGN_MEMBERS
from natal.data import Data
from natal.utils import body_name_to_svg, dignity_of
from typing import Literal
from zoneinfo import ZoneInfo


@dataclass
class Stats:
    """statistics for a natal chart data"""

    data1: Data
    city1: tuple[str, str] | None = None
    tz1: str | None = None
    data2: Data | None = None
    city2: tuple[str, str] | None = None
    tz2: str | None = None

    def aspect_pairs(self):
        """aspects between celestial bodies depending on whether data2 is present"""
        if self.data2:
            synastry_pairs = self.data2.composite_aspect_pairs(self.data1)
            return self.data1.calculate_aspects(synastry_pairs)
        else:
            return self.data1.aspects

    # data grids =================================================================

    def basic_info(self, headers: list[str] = ["name", "city", "coordinates", "local time"]):
        """grid containing name, city, coordinates, and local birth datetime"""
        time_fmt = "%Y-%m-%d %H:%M"
        dt1 = self.data1.utc_dt.astimezone(ZoneInfo(self.tz1)).strftime(time_fmt)
        coordinates1 = f"{self.data1.lat}°N {self.data1.lon}°E"
        output = [headers]
        city1 = self.city1 if self.city1 else "-"
        output.append([self.data1.name, city1, coordinates1, dt1])
        if self.data2:
            dt2 = self.data2.utc_dt.astimezone(ZoneInfo(self.tz2)).strftime(time_fmt)
            city2 = self.city2 if self.city2 else "-"
            coordinates2 = f"{self.data2.lat}°N {self.data2.lon}°E"
            output.append([self.data2.name, city2, coordinates2, dt2])
        return list(zip(*output))

    def elements_vs_modalities(
        self,
        headers: list[str] = ["fire", "air", "water", "earth", "sum"],
        row_label: list[str] = ["cardinal", "fixed", "mutable", "sum"],
        polarity_label: list[str] = ["polarity", "pos", "neg"],
        pdf: bool = False,
    ):
        """grid of celestial bodies' elements and modalities"""
        aspectable1 = self.data1.aspectables
        grid = [["", *headers]]
        ele_keys = ["fire", "air", "water", "earth"]
        mod_keys = ["cardinal", "fixed", "mutable"]
        element_count = {key: 0 for key in ele_keys}
        for i in range(3):
            row = [row_label[i]]
            modality_count = 0
            for j in range(4):
                count = 0
                symbols = []
                for body in aspectable1:
                    if body.sign.element == ele_keys[j] and body.sign.modality == mod_keys[i]:
                        symbols.append(body.symbol)
                        count += 1
                        element_count[ele_keys[j]] += 1
                row.append(", ".join(symbols))
                modality_count += count
            row.append(str(modality_count))
            grid.append(row)
        grid.append([row_label[3], *[str(v) for v in element_count.values()], ""])
        pos_sum = f"null:{element_count['fire'] + element_count['air']} {polarity_label[1]}"
        neg_sum = f"null:{element_count['water'] + element_count['earth']} {polarity_label[2]}"
        grid.append([polarity_label[0], pos_sum, neg_sum, ""])
        return body_name_to_svg(grid) if pdf else grid

    def quadrants_vs_hemispheres(
        self,
        headers: list[str] = ["eastern", "western", "northern", "southern", "sum"],
        pdf: bool = False,
    ):
        """grid of celestial bodies' quadrants and hemispheres"""
        q = self.data1.quadrants
        first_q = ", ".join([body.symbol for body in q[0]])
        second_q = ", ".join([body.symbol for body in q[1]])
        third_q = ", ".join([body.symbol for body in q[2]])
        forth_q = ", ".join([body.symbol for body in q[3]])
        eastern, western, northern, southern, total = headers
        grid = [["", eastern, western, total]]
        southern_sum = str(len(q[3] + q[2]))
        northern_sum = str(len(q[0] + q[1]))
        eastern_sum = str(len(q[3] + q[0]))
        western_sum = str(len(q[1] + q[2]))
        grid.append([southern, forth_q, third_q, southern_sum])
        grid.append([northern, first_q, second_q, northern_sum])
        grid.append([total, eastern_sum, western_sum, ""])
        return body_name_to_svg(grid) if pdf else grid

    def celestial_bodies(
        self,
        data: Literal[1, 2] = 1,
        headers: list[str] = ["body", "sign", "house", "dignity"],
        dignity_labels: list[str] = ["domicile", "exaltation", "detriment", "fall"],
        pdf: bool = False,
    ):
        """grid showing the sign, house and dignity of specific celestial body"""
        chart_data = self.data2 if data == 2 else self.data1
        grid = [headers]
        for body in chart_data.aspectables:
            house = str(self.data1.house_of(body))
            dignity = dignity_of(body, labels=dignity_labels)
            grid.append([body.symbol, body.signed_dms, house, dignity])
        return body_name_to_svg(grid) if pdf else grid

    def signs(
        self,
        headers: list[str] | None = None,
        pdf: bool = False,
    ):
        """distribution of celestial bodies in signs, headers length depends on data2"""
        data1, data2 = self.data1, self.data2
        default_headers = (
            ["sign", "celestial bodies 1", "celestial bodies 2", "sum"]
            if data2
            else ["sign", "celestial bodies", "sum"]
        )
        grid = [headers or default_headers]
        for sign in SIGN_MEMBERS:
            bodies1 = [b.symbol for b in data1.aspectables if b.sign.name == sign.name]
            bodies1_str = ", ".join(bodies1)
            row = [sign.symbol, bodies1_str]
            if data2:
                bodies2 = [b.symbol for b in data2.aspectables if b.sign.name == sign.name]
                bodies2_str = ", ".join(bodies2)
                sum = str(len(bodies1) + len(bodies2) or "")
                row += [bodies2_str, sum]
            else:
                row += [str(len(bodies1) or "")]
            grid.append(row)
        return body_name_to_svg(grid) if pdf else grid

    def houses(
        self,
        headers: list[str] | None = None,
        pdf: bool = False,
    ):
        """distribution of celestial bodies in houses, headers length depends on data2"""
        data1, data2 = self.data1, self.data2
        default_headers = (
            ["house", "cusp", "celestial bodies 1", "celestial bodies 2", "sum"]
            if data2
            else ["house", "cusp", "celestial bodies", "sum"]
        )
        grid = [headers or default_headers]
        for hse in data1.houses:
            bodies1 = [b.symbol for b in data1.aspectables if data1.house_of(b) == hse.value]
            bodies1_str = ", ".join(bodies1)
            row = [str(hse.value), hse.signed_dms, bodies1_str]
            if data2:
                bodies2 = [b.symbol for b in data2.aspectables if data1.house_of(b) == hse.value]
                bodies2_str = ", ".join(bodies2)
                sum = str(len(bodies1) + len(bodies2) or "")
                row += [bodies2_str, sum]
            else:
                row += [str(len(bodies1) or "")]
            grid.append(row)
        return body_name_to_svg(grid) if pdf else grid

    def aspect_grid(self, total_label: str = "sum", pdf: bool = False):
        """aspects cross-reference between celestial bodies"""
        aspectable1 = self.data1.aspectables
        aspectable2 = self.data2.aspectables if self.data2 else self.data1.aspectables
        asp_dict = {
            frozenset((asp.body1, asp.body2)): asp.aspect_member.symbol
            for asp in self.aspect_pairs()
        }
        asp_sets = frozenset(asp_dict.keys())
        body_symbols = [body.symbol for body in aspectable2]
        grid = [[""] + body_symbols + [total_label]]
        for body1 in aspectable1:
            row = [body1.symbol]
            aspect_count = 0
            for body2 in aspectable2:
                symbol_pair = frozenset((body1, body2))
                if symbol_pair in asp_sets:
                    row.append(asp_dict[symbol_pair])
                    aspect_count += 1
                else:
                    row.append("")
            row.append(str(aspect_count))
            grid.append(row)
        return body_name_to_svg(grid) if pdf else grid

    def orb_settings(self, headers: list[str] = ["aspect", "orb"]):
        """orbs settings of each aspect"""
        grid = [headers]
        for aspect in ASPECT_MEMBERS:
            grid.append([aspect.symbol, str(self.data1.config.orb[aspect.name])])
        return body_name_to_svg(grid)
