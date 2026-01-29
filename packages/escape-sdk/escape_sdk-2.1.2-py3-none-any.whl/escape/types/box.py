"""Box (rectangular area) geometry type."""

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from escape.types.point import Point


@dataclass
class Box:
    """Represents a rectangular area (axis-aligned box) with integer coordinates."""

    x1: int
    y1: int
    x2: int
    y2: int

    def __post_init__(self):
        """Ensure coordinates are ordered correctly (x1 < x2, y1 < y2)."""
        if self.x1 > self.x2:
            self.x1, self.x2 = self.x2, self.x1
        if self.y1 > self.y2:
            self.y1, self.y2 = self.y2, self.y1

    @classmethod
    def from_rect(cls, x: int, y: int, width: int, height: int) -> "Box":
        """Create a Box from Java Rectangle format (x, y, width, height)."""
        return cls(x, y, x + width, y + height)

    def width(self) -> int:
        """Get width of the box."""
        return self.x2 - self.x1

    def height(self) -> int:
        """Get height of the box."""
        return self.y2 - self.y1

    def area(self) -> int:
        """Get area of the box."""
        return self.width() * self.height()

    def center(self) -> "Point":
        """Get the center point of the box."""
        from escape.types.point import Point

        return Point((self.x1 + self.x2) // 2, (self.y1 + self.y2) // 2)

    def contains(self, other: "Point | Box") -> bool:
        """Check if a point or box is within this box."""
        if isinstance(other, Box):
            return (
                self.x1 <= other.x1
                and other.x2 <= self.x2
                and self.y1 <= other.y1
                and other.y2 <= self.y2
            )
        return self.x1 <= other.x < self.x2 and self.y1 <= other.y < self.y2

    def random_point(self) -> "Point":
        """Generate a random point within this box."""
        from escape.types.point import Point

        return Point(random.randrange(self.x1, self.x2), random.randrange(self.y1, self.y2))

    def click(self, button: str = "left", randomize: bool = True) -> None:
        """Click within this box."""
        point = self.random_point() if randomize else self.center()
        point.click(button=button)

    def hover(self, randomize: bool = True) -> bool:
        """Move mouse to hover within this box."""
        from escape.globals import get_client
        from escape.types.point import Point

        current = Point(*get_client().input.mouse.position)
        if self.contains(current):
            return True
        point = self.random_point() if randomize else self.center()
        point.hover()
        return True

    def right_click(self, randomize: bool = True) -> None:
        """Right-click within this box."""
        self.click(button="right", randomize=randomize)

    def click_option(self, option: str, randomize: bool = True) -> bool:
        """Click a specific option from the context menu after right-clicking within this box."""
        from escape.client import client

        self.hover(randomize=randomize)
        if client.interactions.menu.wait_has_option(option):
            return client.interactions.menu.click_option(option)
        return False

    def __repr__(self) -> str:
        return f"Box({self.x1}, {self.y1}, {self.x2}, {self.y2})"

    def debug(self, color: tuple[int, int, int] | str = "red", width: int = 2) -> None:
        """Visualize this box on a fresh capture of the game window."""
        from escape._internal.visualizer import Visualizer

        viz = Visualizer()
        if viz.capture():
            viz.draw_box(self, color=color, width=width)
            viz.render()


def create_grid(
    start_x: int,
    start_y: int,
    width: int,
    height: int,
    columns: int,
    rows: int,
    spacing_x: int = 0,
    spacing_y: int = 0,
    padding: int = 0,
) -> list[Box]:
    """Create a grid of Box objects."""
    boxes = []
    for row in range(rows):
        for col in range(columns):
            x1 = start_x + col * (width + spacing_x)
            y1 = start_y + row * (height + spacing_y)
            x2 = x1 + width
            y2 = y1 + height

            # Apply padding (shrink box on all sides)
            if padding > 0:
                x1 += padding
                y1 += padding
                x2 -= padding
                y2 -= padding

            boxes.append(Box(x1, y1, x2, y2))
    return boxes
