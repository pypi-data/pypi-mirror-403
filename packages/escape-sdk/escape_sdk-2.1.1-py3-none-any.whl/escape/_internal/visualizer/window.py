"""Persistent debug window manager using Tkinter."""

import io
import tkinter as tk
from typing import ClassVar

from PIL import Image


class DebugWindow:
    """Debug window that persists across render calls."""

    _instance: ClassVar["DebugWindow | None"] = None
    _root: ClassVar[tk.Tk | None] = None
    _label: ClassVar[tk.Label | None] = None
    _photo_image: ClassVar[tk.PhotoImage | None] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _ensure_window(self, width: int, height: int) -> None:
        """Ensure window exists, create if needed."""
        if DebugWindow._root is None or not self._is_window_alive():
            self._create_window(width, height)
        else:
            # Resize if needed
            current_width = DebugWindow._root.winfo_width()
            current_height = DebugWindow._root.winfo_height()
            if current_width != width or current_height != height:
                DebugWindow._root.geometry(f"{width}x{height}")

    def _is_window_alive(self) -> bool:
        """Check if the Tkinter window still exists."""
        try:
            if DebugWindow._root is None:
                return False
            DebugWindow._root.winfo_exists()
            return True
        except tk.TclError:
            return False

    def _create_window(self, width: int, height: int) -> None:
        """Create new Tkinter window."""
        DebugWindow._root = tk.Tk()
        DebugWindow._root.title("Escape Debug Visualizer")
        DebugWindow._root.geometry(f"{width}x{height}")
        DebugWindow._root.resizable(False, False)

        # Create label to hold image
        DebugWindow._label = tk.Label(DebugWindow._root)
        DebugWindow._label.pack(fill=tk.BOTH, expand=True)

        # Handle window close - destroy and reset references
        DebugWindow._root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self) -> None:
        """Handle window close button - destroy and reset references."""
        if DebugWindow._root is not None:
            DebugWindow._root.destroy()
            DebugWindow._root = None
            DebugWindow._label = None
            DebugWindow._photo_image = None

    def _pil_to_tk_photo(self, image: Image.Image) -> tk.PhotoImage:
        """Convert PIL Image to Tkinter PhotoImage without ImageTk."""
        # Convert to RGB if necessary (PhotoImage doesn't support RGBA well)
        if image.mode != "RGB":
            image = image.convert("RGB")

        # Save to PPM format in memory (Tkinter natively supports PPM)
        buffer = io.BytesIO()
        image.save(buffer, format="PPM")
        ppm_data = buffer.getvalue()

        return tk.PhotoImage(data=ppm_data)

    def render(self, image: Image.Image) -> None:
        """Render image to debug window."""
        width, height = image.size
        self._ensure_window(width, height)

        # Convert to PhotoImage and update label
        # Keep reference to prevent garbage collection
        if DebugWindow._root is None or DebugWindow._label is None:
            return
        DebugWindow._photo_image = self._pil_to_tk_photo(image)
        DebugWindow._label.configure(image=DebugWindow._photo_image)

        # Process pending events and update display (non-blocking)
        DebugWindow._root.update_idletasks()
        DebugWindow._root.update()

    def close(self) -> None:
        """Close and destroy the debug window."""
        self._on_close()

    def is_open(self) -> bool:
        """Check if debug window is currently open."""
        return self._is_window_alive()
