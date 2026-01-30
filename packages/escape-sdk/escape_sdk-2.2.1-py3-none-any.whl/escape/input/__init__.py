"""OS-level input handling - mouse, keyboard, and drawing."""

from escape.input.drawing import Drawing, drawing
from escape.input.keyboard import Keyboard, keyboard
from escape.input.mouse import Mouse, mouse
from escape.input.runelite import RuneLite, runelite


class Input:
    """OS-level input controls: mouse, keyboard, and drawing overlays."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def runelite(self) -> RuneLite:
        """RuneLite window manager."""
        return runelite

    @property
    def mouse(self) -> Mouse:
        """Mouse controller."""
        return mouse

    @property
    def keyboard(self) -> Keyboard:
        """Keyboard controller."""
        return keyboard

    @property
    def drawing(self) -> Drawing:
        """Drawing overlay for debugging."""
        return drawing


# Module-level instance
input = Input()


__all__ = [
    "Drawing",
    "Input",
    "Keyboard",
    "Mouse",
    "RuneLite",
    "drawing",
    "input",
    "keyboard",
    "mouse",
    "runelite",
]
