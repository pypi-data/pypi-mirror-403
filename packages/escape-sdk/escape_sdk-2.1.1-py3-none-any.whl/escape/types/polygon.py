"""Polygon geometry type."""

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from escape.types.point import Point


@dataclass
class Polygon:
    """Represents an arbitrary polygon defined by n vertices."""

    vertices: list["Point"]

    def __post_init__(self):
        """Validate polygon has at least 3 vertices."""
        if len(self.vertices) < 3:
            raise ValueError("Polygon must have at least 3 vertices")

    def from_array(self, data: list[list[int]]) -> None:
        """Populate Polygon from array of [x, y] coordinate pairs."""
        from escape.types.point import Point

        x_data = data[0]
        y_data = data[1]

        self.vertices = [Point(x, y) for x, y in zip(x_data, y_data, strict=False)]

    def center(self) -> "Point":
        """Get the centroid (center of mass) of the polygon."""
        from escape.types.point import Point

        x_sum = sum(v.x for v in self.vertices)
        y_sum = sum(v.y for v in self.vertices)
        n = len(self.vertices)
        return Point(x_sum // n, y_sum // n)

    def bounds(self) -> tuple[int, int, int, int]:
        """Get the bounding box of this polygon."""
        min_x = min(v.x for v in self.vertices)
        min_y = min(v.y for v in self.vertices)
        max_x = max(v.x for v in self.vertices)
        max_y = max(v.y for v in self.vertices)
        return (min_x, min_y, max_x, max_y)

    def contains(self, point: "Point") -> bool:
        """Check if a point is within this polygon using ray casting algorithm."""
        x, y = point.x, point.y
        n = len(self.vertices)
        inside = False

        p1x, p1y = self.vertices[0].x, self.vertices[0].y
        for i in range(1, n + 1):
            p2x, p2y = self.vertices[i % n].x, self.vertices[i % n].y
            if y > min(p1y, p2y) and y <= max(p1y, p2y) and x <= max(p1x, p2x):
                if p1y != p2y:
                    xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                if p1x == p2x or x <= xinters:
                    inside = not inside
            p1x, p1y = p2x, p2y

        return inside

    def area(self) -> float:
        """Calculate the area of the polygon using the shoelace formula."""
        n = len(self.vertices)
        area = 0.0
        for i in range(n):
            j = (i + 1) % n
            area += self.vertices[i].x * self.vertices[j].y
            area -= self.vertices[j].x * self.vertices[i].y
        return abs(area) / 2.0

    def random_point(self) -> "Point":
        """Generate a random point within this polygon using rejection sampling."""
        min_x, min_y, max_x, max_y = self.bounds()

        # Rejection sampling with max attempts
        max_attempts = 1000
        for _ in range(max_attempts):
            from escape.types.point import Point

            x = random.randint(min_x, max_x)
            y = random.randint(min_y, max_y)
            point = Point(x, y)
            if self.contains(point):
                return point

        # Fallback to center if rejection sampling fails
        return self.center()

    def click(self, button: str = "left", randomize: bool = True) -> None:
        """Click within this polygon."""
        point = self.random_point() if randomize else self.center()
        point.click(button=button)

    def hover(self, randomize: bool = True) -> bool:
        """Move mouse to hover within this polygon."""
        from escape.globals import get_client
        from escape.types.point import Point

        current = Point(*get_client().input.mouse.position)
        if self.contains(current):
            return True
        point = self.random_point() if randomize else self.center()
        point.hover()
        return True

    def right_click(self, randomize: bool = True) -> None:
        """Right-click within this polygon."""
        self.click(button="right", randomize=randomize)

    def __repr__(self) -> str:
        return f"Polygon({len(self.vertices)} vertices, area={self.area():.2f})"

    def debug(
        self, argb_color: int = 0xFFFF0000, filled: bool = False, tag: str | None = None
    ) -> None:
        """Draw this polygon as an overlay on RuneLite."""
        from escape.input.drawing import drawing

        x_points = [v.x for v in self.vertices]
        y_points = [v.y for v in self.vertices]
        drawing.add_polygon(x_points, y_points, argb_color, filled, tag)
