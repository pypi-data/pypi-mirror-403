"""Screen capture utilities for RuneLite window."""

import subprocess

from PIL import Image
from Xlib import X, display

# Cached state for fast captures
_display: display.Display | None = None
_canvas_window = None
_canvas_size: tuple[int, int] | None = None


def capture_runelite(use_cache: bool = True) -> Image.Image | None:
    """
    Capture screenshot of RuneLite window using Xlib (fast, ~3ms).

    Finds the actual game canvas window (not the frame) and captures it directly
    using X11's GetImage. Caches the window for faster subsequent captures.

    Args:
        use_cache: If True, reuse cached window. Set False to re-detect.

    Returns:
        PIL Image of RuneLite window, or None if not found
    """
    global _display, _canvas_window, _canvas_size

    # Initialize display if needed
    if _display is None:
        try:
            _display = display.Display()
        except Exception:
            return None

    # Use cached window if available
    if use_cache and _canvas_window is not None and _canvas_size is not None:
        img = _capture_window(_canvas_window, _canvas_size[0], _canvas_size[1])
        if img is not None:
            return img
        # Window may have closed, clear cache and retry
        _canvas_window = None
        _canvas_size = None

    # Find the canvas window
    canvas_id = _find_canvas_window()
    if canvas_id is None:
        return None

    wid, width, height = canvas_id
    display_obj = _display
    if display_obj is None:
        return None
    _canvas_window = display_obj.create_resource_object("window", wid)
    _canvas_size = (width, height)

    return _capture_window(_canvas_window, width, height)


def clear_cache() -> None:
    """Clear the cached window. Call this if RuneLite was restarted."""
    global _canvas_window, _canvas_size
    _canvas_window = None
    _canvas_size = None


def _capture_window(window, width: int, height: int) -> Image.Image | None:
    """Capture window using Xlib XGetImage (fast, in-memory)."""
    try:
        raw = window.get_image(0, 0, width, height, X.ZPixmap, 0xFFFFFFFF)
        return Image.frombytes("RGB", (width, height), raw.data, "raw", "BGRX")
    except Exception:
        return None


def _find_canvas_window() -> tuple[int, int, int] | None:
    """
    Find the RuneLite canvas window ID and dimensions.

    RuneLite creates multiple windows - we want the canvas (smallest non-trivial).

    Returns:
        Tuple of (window_id, width, height) or None if not found
    """
    global _display

    try:
        # Get all RuneLite windows using xdotool (reliable window search)
        result = subprocess.run(
            ["xdotool", "search", "--name", "RuneLite"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0 or not result.stdout.strip():
            return None

        window_ids = [int(wid) for wid in result.stdout.strip().split("\n")]

        # Find the canvas (smallest non-trivial window)
        candidates = []
        display_obj = _display
        if display_obj is None:
            return None
        for wid in window_ids:
            try:
                win = display_obj.create_resource_object("window", wid)
                geo = win.get_geometry()
                if geo.width > 1 and geo.height > 1:
                    candidates.append((wid, geo.width, geo.height, geo.width * geo.height))
            except Exception:
                continue

        if not candidates:
            return None

        # Sort by area, return smallest
        candidates.sort(key=lambda x: x[3])
        wid, width, height, _ = candidates[0]
        return (wid, width, height)

    except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
        return None
