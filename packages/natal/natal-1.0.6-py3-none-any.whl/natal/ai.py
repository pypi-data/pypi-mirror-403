from natal import const
from natal.stats import Stats
from typing import Literal


class AIContext(Stats):
    """statistics data in markdown format for AI context"""

    def basic_info(self):
        """pivot the basic info grid"""
        return list(zip(*super().basic_info()))

    def elements(self):
        """distribution of celestial bodies in the 4 elements"""
        return self.distribution("element")

    def modalities(self):
        """distribution of celestial bodies in the 3 modalities"""
        return self.distribution("modality")

    def polarities(self):
        """distribution of celestial bodies in the 2 polarities"""
        return self.distribution("polarity")

    def quadrants(self):
        """distribution of celestial bodies in the 4 quadrants"""
        quadrant_names = ["first", "second", "third", "fourth"]
        grid = [["quadrants", "celestial bodies", "sum"]]
        for i, q in enumerate(self.data1.quadrants):
            grid.append([quadrant_names[i], ", ".join([b.symbol for b in q]), len(q)])
        return grid

    def hemispheres(self):
        """distribution of celestial bodies in the 4 hemispheres"""
        q = self.data1.quadrants
        grid = [["hemispheres", "celestial bodies", "sum"]]
        southern_sum = len(q[3] + q[2])
        northern_sum = len(q[0] + q[1])
        eastern_sum = len(q[3] + q[0])
        western_sum = len(q[1] + q[2])
        grid.append(["southern", ", ".join([b.symbol for b in q[2] + q[3]]), southern_sum])
        grid.append(["northern", ", ".join([b.symbol for b in q[0] + q[1]]), northern_sum])
        grid.append(["eastern", ", ".join([b.symbol for b in q[0] + q[3]]), eastern_sum])
        grid.append(["western", ", ".join([b.symbol for b in q[1] + q[2]]), western_sum])
        return grid

    def aspects(self):
        """aspects in long form"""
        headers = ["celestial body 1", "celestial body 2", "aspect"]
        if self.data2:
            headers = [
                f"{self.data1.name}'s celestial body",
                f"{self.data2.name}'s celestial body",
                "aspect",
            ]
        grid = [headers]
        for asp in self.aspect_pairs():
            grid.append([asp.body1.symbol, asp.body2.symbol, asp.aspect_member.name])
        return grid

    def markdown(self, title: str, grid: list[list]) -> str:
        """markdown of specific function's grid data for AI context"""
        output = f"#### {title}\n"
        header = grid.pop(0)
        output += "|"
        for item in header:
            output += f"{item} | "
        output += "\n"
        output += "|" + "--- | " * len(header)
        output += "\n"
        for row in grid:
            output += "|"
            for item in row:
                output += f"{item} | "
            output += "\n"
        output += "\n"
        return output

    def distribution(self, kind: Literal["element", "modality", "polarity"]) -> list[list]:
        """distribution of celestial bodies based on kind"""
        names = getattr(const, f"{kind}_NAMES".upper())
        grid = [[kind, "celestial bodies", "sum"]]
        for name in names:
            bodies = []
            for body in self.data1.aspectables:
                if body.sign[kind] == name:
                    bodies.append(body.symbol)
            grid.append([name, ", ".join(bodies), len(bodies)])
        return grid
