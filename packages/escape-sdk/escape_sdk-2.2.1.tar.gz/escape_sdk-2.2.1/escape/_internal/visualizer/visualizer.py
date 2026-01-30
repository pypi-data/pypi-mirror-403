"""Main Visualizer class for debug rendering."""

from PIL import Image, ImageDraw

from escape.types.box import Box
from escape.types.circle import Circle
from escape.types.point import Point
from escape.types.polygon import Polygon
from escape.types.quad import Quad

from .capture import capture_runelite
from .window import DebugWindow

# Type alias for color - RGB tuple or color name
Color = tuple[int, int, int] | str


class Visualizer:
    """Debug visualizer for rendering overlays on RuneLite screenshots."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self):
        """Actual initialization, runs once."""
        self._image: Image.Image | None = None
        self._draw: ImageDraw.ImageDraw | None = None
        self._debug_window = DebugWindow()

    def capture(self) -> bool:
        """Capture screenshot of RuneLite window."""
        image = capture_runelite()
        if image is None:
            return False

        self._image = image
        self._draw = ImageDraw.Draw(self._image)
        return True

    def get_image(self) -> Image.Image | None:
        """Get the current captured image."""
        return self._image

    def set_image(self, image: Image.Image) -> None:
        """Set custom image for testing or external sources."""
        self._image = image

    def render(self) -> bool:
        """Render current image to debug window."""
        if self._image is None:
            return False

        self._debug_window.render(self._image)
        return True

    def close(self) -> None:
        """Close the debug window."""
        self._debug_window.close()

    def is_window_open(self) -> bool:
        """Check if debug window is currently open."""
        return self._debug_window.is_open()

    def draw_box(
        self,
        box: Box,
        color: Color = "red",
        width: int = 2,
        fill: Color | None = None,
    ) -> None:
        """Draw a Box rectangle on the image."""
        if self._draw is None:
            return
        self._draw.rectangle(
            [box.x1, box.y1, box.x2, box.y2], outline=color, width=width, fill=fill
        )

    def draw_circle(
        self,
        circle: Circle,
        color: Color = "red",
        width: int = 2,
        fill: Color | None = None,
    ) -> None:
        """Draw a Circle on the image."""
        if self._draw is None:
            return
        x1 = circle.center_x - circle.radius
        y1 = circle.center_y - circle.radius
        x2 = circle.center_x + circle.radius
        y2 = circle.center_y + circle.radius
        self._draw.ellipse([x1, y1, x2, y2], outline=color, width=width, fill=fill)

    def draw_polygon(
        self,
        polygon: Polygon,
        color: Color = "red",
        width: int = 2,
        fill: Color | None = None,
    ) -> None:
        """Draw a Polygon on the image."""
        if self._draw is None:
            return
        points = [(v.x, v.y) for v in polygon.vertices]
        self._draw.polygon(points, outline=color, width=width, fill=fill)

    def draw_quad(
        self,
        quad: Quad,
        color: Color = "red",
        width: int = 2,
        fill: Color | None = None,
    ) -> None:
        """Draw a Quad quadrilateral on the image."""
        if self._draw is None:
            return
        points = [
            (quad.p1.x, quad.p1.y),
            (quad.p2.x, quad.p2.y),
            (quad.p3.x, quad.p3.y),
            (quad.p4.x, quad.p4.y),
        ]
        self._draw.polygon(points, outline=color, width=width, fill=fill)

    def draw_point(
        self,
        point: Point,
        color: Color = "red",
        size: int = 5,
    ) -> None:
        """Draw a Point as a small crosshair."""
        if self._draw is None:
            return
        self._draw.line([(point.x - size, point.y), (point.x + size, point.y)], fill=color, width=2)
        self._draw.line([(point.x, point.y - size), (point.x, point.y + size)], fill=color, width=2)

    def draw_line(
        self,
        p1: Point,
        p2: Point,
        color: Color = "red",
        width: int = 2,
    ) -> None:
        """Draw a line between two points."""
        if self._draw is None:
            return
        self._draw.line([(p1.x, p1.y), (p2.x, p2.y)], fill=color, width=width)

    def draw_text(
        self,
        point: Point,
        text: str,
        color: Color = "white",
    ) -> None:
        """Draw text at a point."""
        if self._draw is None:
            return
        self._draw.text((point.x, point.y), text, fill=color)
