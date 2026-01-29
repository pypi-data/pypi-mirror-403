"""Circle geometry type."""

import math
import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from escape.types.point import Point


@dataclass
class Circle:
    """Represents a circle with integer center coordinates and float radius."""

    center_x: int
    center_y: int
    radius: float

    def center(self) -> "Point":
        """Get the center point of the circle."""
        from escape.types.point import Point

        return Point(self.center_x, self.center_y)

    def area(self) -> float:
        """Get the area of the circle."""
        return math.pi * self.radius * self.radius

    def contains(self, point: "Point") -> bool:
        """Check if a point is within this circle."""
        dx = point.x - self.center_x
        dy = point.y - self.center_y
        return math.sqrt(dx * dx + dy * dy) <= self.radius

    def random_point(self) -> "Point":
        """Generate a uniformly random point within this circle."""
        from escape.types.point import Point

        # Use sqrt to get uniform distribution (not just random angle/radius)
        r = self.radius * math.sqrt(random.random())
        theta = random.uniform(0, 2 * math.pi)

        x = self.center_x + int(r * math.cos(theta))
        y = self.center_y + int(r * math.sin(theta))

        return Point(x, y)

    def click(self, button: str = "left", randomize: bool = True) -> None:
        """Click within this circle."""
        point = self.random_point() if randomize else self.center()
        point.click(button=button)

    def hover(self, randomize: bool = True) -> bool:
        """Move mouse to hover within this circle."""
        from escape.globals import get_client
        from escape.types.point import Point

        current = Point(*get_client().input.mouse.position)
        if self.contains(current):
            return True
        point = self.random_point() if randomize else self.center()
        point.hover()
        return True

    def right_click(self, randomize: bool = True) -> None:
        """Right-click within this circle."""
        self.click(button="right", randomize=randomize)

    def __repr__(self) -> str:
        return f"Circle(center=({self.center_x}, {self.center_y}), radius={self.radius})"

    def debug(
        self, argb_color: int = 0xFFFF0000, filled: bool = False, tag: str | None = None
    ) -> None:
        """Draw this circle as an overlay on RuneLite."""
        from escape.input.drawing import drawing

        drawing.add_circle(self.center_x, self.center_y, int(self.radius), argb_color, filled, tag)
