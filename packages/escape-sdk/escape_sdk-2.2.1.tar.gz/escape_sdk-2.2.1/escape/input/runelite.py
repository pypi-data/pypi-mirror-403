"""RuneLite window detection and position management using X11 events."""

import contextlib
import subprocess
import threading
import time
from typing import Any

from Xlib import X, display

from escape.types.box import Box


class RuneLite:
    """RuneLite window position tracker using X11 events."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self, window_title: str = "RuneLite", auto_refresh: bool = True):
        """Initialize the instance."""
        self.window_title = window_title
        self.auto_refresh = auto_refresh

        # Window state (updated by event thread)
        self._window_id: int | None = None
        self._window_offset: tuple[int, int] | None = None
        self._window_size: tuple[int, int] | None = None
        self._is_minimized: bool = False
        self._is_active: bool = False
        self._state_valid: bool = False
        self._window_box: Box = Box(4, 4, 765, 503)

        # Thread synchronization
        self._lock = threading.Lock()
        self._stop_event = threading.Event()

        # X11 display connection (main thread for queries)
        self._display: display.Display | None = None

        # Start event listener thread
        self._event_thread: threading.Thread | None = None

        # Do initial window detection
        self._initialize_display()
        self.detect_window()

        # Start event listener if window found
        if self._window_id:
            self._start_event_listener()

    def _initialize_display(self) -> bool:
        """Initialize X11 display connection."""
        try:
            self._display = display.Display()
            return True
        except Exception:
            self._display = None
            return False

    def _start_event_listener(self) -> None:
        """Start the background event listener thread."""
        if self._event_thread is not None and self._event_thread.is_alive():
            return

        self._stop_event.clear()
        self._event_thread = threading.Thread(target=self._event_loop, daemon=True)
        self._event_thread.start()

    def _stop_event_listener(self) -> None:
        """Stop the background event listener thread."""
        self._stop_event.set()
        if self._event_thread is not None:
            self._event_thread.join(timeout=1.0)
            self._event_thread = None

    def _event_loop(self) -> None:
        """Background thread listening for X11 window events."""
        try:
            # Create separate display connection for event thread
            event_display = display.Display()
            root = event_display.screen().root

            # Subscribe to property changes on root to detect active window changes
            root.change_attributes(event_mask=X.PropertyChangeMask)

            # Subscribe to events on the RuneLite window if we have it
            if self._window_id:
                try:
                    window = event_display.create_resource_object("window", self._window_id)
                    window.change_attributes(
                        event_mask=(
                            X.StructureNotifyMask
                            | X.FocusChangeMask
                            | X.PropertyChangeMask
                            | X.VisibilityChangeMask
                        )
                    )
                except Exception:
                    pass

            while not self._stop_event.is_set():
                # Check for pending events with timeout
                if event_display.pending_events() > 0:
                    evt = event_display.next_event()
                    self._handle_event(evt, event_display)
                else:
                    # Small sleep to avoid busy-waiting
                    time.sleep(0.01)

            event_display.close()

        except Exception:
            # Event loop crashed, mark state as invalid
            with self._lock:
                self._state_valid = False

    def _handle_event(self, evt: Any, event_display: display.Display) -> None:
        """Handle an X11 event and update internal state."""
        with self._lock:
            # ConfigureNotify: window moved or resized
            if evt.type == X.ConfigureNotify:
                if hasattr(evt, "window") and evt.window:
                    window_id = evt.window.id if hasattr(evt.window, "id") else evt.window
                    if window_id == self._window_id:
                        self._window_offset = (evt.x, evt.y)
                        self._window_size = (evt.width, evt.height)

            # UnmapNotify: window minimized/hidden
            elif evt.type == X.UnmapNotify:
                if hasattr(evt, "window") and evt.window:
                    window_id = evt.window.id if hasattr(evt.window, "id") else evt.window
                    if window_id == self._window_id:
                        self._is_minimized = True

            # MapNotify: window restored/shown
            elif evt.type == X.MapNotify:
                if hasattr(evt, "window") and evt.window:
                    window_id = evt.window.id if hasattr(evt.window, "id") else evt.window
                    if window_id == self._window_id:
                        self._is_minimized = False

            # FocusIn: window gained focus
            elif evt.type == X.FocusIn:
                if hasattr(evt, "window") and evt.window:
                    window_id = evt.window.id if hasattr(evt.window, "id") else evt.window
                    if window_id == self._window_id:
                        self._is_active = True

            # FocusOut: window lost focus
            elif evt.type == X.FocusOut:
                if hasattr(evt, "window") and evt.window:
                    window_id = evt.window.id if hasattr(evt.window, "id") else evt.window
                    if window_id == self._window_id:
                        self._is_active = False

            # PropertyNotify on root: check for active window change
            elif evt.type == X.PropertyNotify and hasattr(evt, "atom"):
                atom_name = event_display.get_atom_name(evt.atom)
                if atom_name == "_NET_ACTIVE_WINDOW":
                    self._update_active_state(event_display)

    def _update_active_state(self, event_display: display.Display) -> None:
        """Update active window state from _NET_ACTIVE_WINDOW property."""
        try:
            root = event_display.screen().root
            atom = event_display.intern_atom("_NET_ACTIVE_WINDOW")
            response = root.get_full_property(atom, X.AnyPropertyType)

            if response and response.value:
                active_id = response.value[0]
                self._is_active = active_id == self._window_id
        except Exception:
            pass

    def detect_window(self) -> bool:
        """Detect RuneLite window and get its position/size."""
        try:
            # Use wmctrl to find the exact RuneLite window
            result = subprocess.run(
                ["wmctrl", "-l", "-G"], capture_output=True, text=True, check=False
            )

            if result.returncode != 0:
                return False

            # Parse wmctrl output to find RuneLite window
            for line in result.stdout.split("\n"):
                if self.window_title in line:
                    parts = line.split()
                    if len(parts) >= 7:
                        # Check if this is actually the RuneLite client window
                        window_name = " ".join(parts[7:])

                        # Skip if it's not the actual RuneLite window
                        if not window_name.startswith("RuneLite"):
                            continue

                        # Format: window_id desktop x y width height client_machine window_title
                        window_id_hex = parts[0]
                        x = int(parts[2])
                        y = int(parts[3])
                        width = int(parts[4])
                        height = int(parts[5])

                        # Convert hex window ID to int
                        window_id = int(window_id_hex, 16)

                        # Use xwininfo to get the client area (without decorations)
                        geom_result = subprocess.run(
                            ["xwininfo", "-id", window_id_hex],
                            capture_output=True,
                            text=True,
                            check=False,
                        )

                        if geom_result.returncode == 0:
                            # Parse xwininfo for more accurate client coordinates
                            for info_line in geom_result.stdout.split("\n"):
                                info_line = info_line.strip()
                                if info_line.startswith("Absolute upper-left X:"):
                                    x = int(info_line.split(":")[1].strip())
                                elif info_line.startswith("Absolute upper-left Y:"):
                                    y = int(info_line.split(":")[1].strip())
                                elif info_line.startswith("Width:"):
                                    width = int(info_line.split(":")[1].strip())
                                elif info_line.startswith("Height:"):
                                    height = int(info_line.split(":")[1].strip())

                            # Check if minimized
                            is_minimized = "IsUnMapped" in geom_result.stdout

                        with self._lock:
                            self._window_id = window_id
                            self._window_offset = (x, y)
                            self._window_size = (width, height)
                            self._is_minimized = is_minimized
                            self._state_valid = True

                        # Check active state
                        self._check_active_state()

                        # Start event listener if not running
                        self._start_event_listener()

                        return True

            return False

        except FileNotFoundError:
            return False
        except Exception:
            return False

    def _check_active_state(self) -> None:
        """Check if RuneLite window is currently active."""
        if self._display is None or self._window_id is None:
            return

        try:
            root = self._display.screen().root
            atom = self._display.intern_atom("_NET_ACTIVE_WINDOW")
            response = root.get_full_property(atom, X.AnyPropertyType)

            if response and response.value:
                active_id = response.value[0]
                with self._lock:
                    self._is_active = active_id == self._window_id
        except Exception:
            pass

    def activate_window(self) -> bool:
        """Activate and bring RuneLite window to foreground."""
        if self._window_id is None and not self.detect_window():
            return False
        if self._window_id is None:
            return False

        try:
            window_id_hex = hex(self._window_id)

            # Unminimize and activate using xdotool
            subprocess.run(
                ["xdotool", "windowmap", window_id_hex], capture_output=True, check=False
            )
            subprocess.run(
                ["xdotool", "windowactivate", window_id_hex], capture_output=True, check=False
            )

            # Give window manager time to process
            time.sleep(0.1)

            self._window_box.hover()

            # Update state
            with self._lock:
                self._is_minimized = False
                self._is_active = True

            # Re-detect position (may have changed)
            self.detect_window()

            return True

        except Exception:
            return False

    def is_window_minimized(self) -> bool:
        """Check if window is minimized."""
        with self._lock:
            return self._is_minimized

    def is_window_active(self) -> bool:
        """Check if the window is currently active."""
        with self._lock:
            return self._is_active

    def ensure_window_ready(self) -> bool:
        """Ensure window is detected, not minimized, and activated."""
        with self._lock:
            if not self._state_valid:
                # Need to detect first
                pass
            elif not self._is_minimized and self._is_active:
                return True

        # Detect if needed
        if not self._state_valid and not self.detect_window():
            return False

        # Activate if minimized or not active
        if self._is_minimized or not self._is_active:
            return self.activate_window()

        return True

    def refresh_window_position(self, force: bool = False, max_age: float = 10.0) -> bool:
        """Refresh the window position if needed."""
        if force:
            return self.detect_window()

        with self._lock:
            if not self._state_valid:
                # First time, need detection
                pass
            elif self._is_minimized or not self._is_active:
                # Need to activate
                pass
            else:
                # State is valid and window is ready
                return True

        # Need to ensure window is ready
        return self.ensure_window_ready()

    def _auto_refresh(self) -> None:
        """Auto-refresh window position if enabled."""
        if self.auto_refresh:
            self.refresh_window_position()

    def get_window_offset(self) -> tuple[int, int] | None:
        """Get current window offset (x, y)."""
        self._auto_refresh()
        with self._lock:
            return self._window_offset

    def get_window_size(self) -> tuple[int, int] | None:
        """Get current window size (width, height)."""
        self._auto_refresh()
        with self._lock:
            return self._window_size

    def get_game_bounds(self) -> tuple[int, int, int, int] | None:
        """Get game window bounds (x, y, width, height)."""
        self._auto_refresh()

        with self._lock:
            if self._window_offset and self._window_size:
                return (
                    self._window_offset[0],
                    self._window_offset[1],
                    self._window_size[0],
                    self._window_size[1],
                )
        return None

    def set_minimized(self, minimized: bool) -> None:
        """Manually set the minimized state."""
        with self._lock:
            self._is_minimized = minimized

    def set_active(self, active: bool) -> None:
        """Manually set the active state."""
        with self._lock:
            self._is_active = active

    def __del__(self):
        """Clean up resources on destruction."""
        self._stop_event_listener()
        if self._display:
            with contextlib.suppress(Exception):
                self._display.close()


# Module-level instance
runelite = RuneLite()
