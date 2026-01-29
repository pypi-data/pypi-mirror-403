"""Keyboard control with human-like typing."""

import random
import time
from typing import Any

try:
    import pyautogui as pag
except ImportError:
    pag = None


class Keyboard:
    """Keyboard controller with human-like typing."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self, speed: float = 1.0):
        """Actual initialization, runs once."""
        from escape.input.runelite import runelite

        if pag is None:
            raise ImportError("pyautogui is required. Install with: pip install pyautogui")

        # Configure pyautogui
        pag.PAUSE = 0
        pag.FAILSAFE = False
        self._pag: Any = pag

        self.runelite = runelite
        self.speed = speed

    def _ensure_focus(self) -> None:
        """Ensure RuneLite window is ready for input."""
        self.runelite.refresh_window_position()

    def _press(self, key: str) -> None:
        """Core press function - ONLY access point to pyautogui.press()."""
        self._ensure_focus()
        self._pag.press(key, _pause=False)

    def _key_down(self, key: str) -> None:
        """Core key down function - ONLY access point to pyautogui.keyDown()."""
        self._ensure_focus()
        self._pag.keyDown(key, _pause=False)

    def _key_up(self, key: str) -> None:
        """Core key up function - ONLY access point to pyautogui.keyUp()."""
        self._ensure_focus()
        self._pag.keyUp(key, _pause=False)

    def _type_char(self, char: str) -> None:
        """Core type function - ONLY access point to pyautogui.write() for single char."""
        self._ensure_focus()
        self._pag.write(char, interval=0, _pause=False)

    def type(self, text: str, humanize: bool = True) -> None:
        """Type text with optional human-like delays."""
        if not text:
            return

        self._ensure_focus()

        # Base delay: ~50ms per keystroke at speed=1.0
        base_delay = 0.05 / self.speed

        for char in text:
            self._type_char(char)

            if humanize:
                # Random delay with variation (±40%)
                delay = base_delay * random.uniform(0.6, 1.4)

                # Occasionally add longer pause (simulates thinking)
                if random.random() < 0.05:
                    delay += random.uniform(0.1, 0.3)

                time.sleep(delay)

    def press(self, key: str) -> None:
        """Press and release a key."""
        self._press(key)

        # Small delay after key press (human-like)
        time.sleep(random.uniform(0.02, 0.05))

    def hold(self, key: str) -> None:
        """Hold a key down (must call release() to let go)."""
        self._key_down(key)

    def release(self, key: str) -> None:
        """Release a held key."""
        self._key_up(key)

        # Small delay after release (human-like)
        time.sleep(random.uniform(0.02, 0.05))

    def hotkey(self, *keys: str) -> None:
        """Press a key combination (hotkey)."""
        self._ensure_focus()

        # Press keys in order
        for key in keys:
            self._key_down(key)
            time.sleep(random.uniform(0.01, 0.03))

        # Release in reverse order
        for key in reversed(keys):
            self._key_up(key)
            time.sleep(random.uniform(0.01, 0.03))

        # Small delay after hotkey (human-like)
        time.sleep(random.uniform(0.03, 0.08))

    def press_enter(self) -> None:
        """Press Enter key."""
        self.press("enter")

    def press_escape(self) -> None:
        """Press Escape key."""
        self.press("escape")

    def press_space(self) -> None:
        """Press Space key."""
        self.press("space")

    def press_tab(self) -> None:
        """Press Tab key."""
        self.press("tab")

    def press_f_key(self, num: int) -> None:
        """Press a function key (F1-F12)."""
        if not 1 <= num <= 12:
            raise ValueError(f"Function key must be between 1 and 12, got {num}")

        self.press(f"f{num}")

    def press_number(self, num: int) -> None:
        """Press a number key (0-9)."""
        if not 0 <= num <= 9:
            raise ValueError(f"Number must be between 0 and 9, got {num}")

        self.press(str(num))


# Module-level instance
keyboard = Keyboard()
