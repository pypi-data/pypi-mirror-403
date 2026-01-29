"""Point geometry types for 2D and 3D coordinates."""

import math
from dataclasses import dataclass


@dataclass
class Point:
    """Represents a 2D point with integer coordinates."""

    x: int
    y: int

    def distance_to(self, other: "Point") -> float:
        """Calculate Euclidean distance to another point."""
        dx = self.x - other.x
        dy = self.y - other.y
        return math.sqrt(dx * dx + dy * dy)

    def click(self, button: str = "left") -> None:
        """Click at this point."""
        from escape.globals import get_client

        mouse = get_client().input.mouse
        if button == "left":
            mouse.left_click(self.x, self.y)
        else:
            mouse.right_click(self.x, self.y)

    def hover(self) -> None:
        """Move mouse to hover over this point."""
        from escape.globals import get_client

        mouse = get_client().input.mouse
        mouse.move_to(self.x, self.y)

    def right_click(self) -> None:
        """Right-click at this point."""
        self.click(button="right")

    def __repr__(self) -> str:
        return f"Point({self.x}, {self.y})"

    def debug(
        self,
        argb_color: int = 0xFFFF0000,
        size: int = 5,
        thickness: int = 2,
        tag: str | None = None,
    ) -> None:
        """Draw this point as a crosshair overlay on RuneLite."""
        from escape.input.drawing import drawing

        drawing.add_line(self.x - size, self.y, self.x + size, self.y, argb_color, thickness, tag)
        drawing.add_line(self.x, self.y - size, self.x, self.y + size, argb_color, thickness, tag)


@dataclass
class Point3D:
    """Represents a 3D point with integer coordinates."""

    x: int
    y: int
    z: int

    def distance_to(self, other: "Point3D") -> float:
        """Calculate 3D Euclidean distance to another point."""
        dx = self.x - other.x
        dy = self.y - other.y
        dz = self.z - other.z
        return math.sqrt(dx * dx + dy * dy + dz * dz)

    def to2d(self) -> Point:
        """Convert to 2D point, dropping z coordinate."""
        return Point(self.x, self.y)

    def __repr__(self) -> str:
        return f"Point3D({self.x}, {self.y}, {self.z})"
