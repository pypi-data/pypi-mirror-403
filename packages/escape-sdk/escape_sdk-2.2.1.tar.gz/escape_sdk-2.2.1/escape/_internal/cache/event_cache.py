"""
Thread-safe public API for accessing game state.

Wraps StateBuilder with thread safety and provides clean public methods.
"""

import threading
import time
from typing import Any

from escape.types import ItemContainer
from escape.utilities.timing import wait_until

from .state_builder import StateBuilder


class EventCache:
    """Thread-safe public API for game state, wrapping StateBuilder with locking."""

    def __init__(self, event_history_size: int = 100):
        """Initialize event cache with given history buffer size."""
        # StateBuilder does the actual work
        self._state = StateBuilder(event_history_size)

        # Track last update time
        self._last_update_time: float = 0.0

        # Thread safety - protects all access to _state
        self._lock = threading.RLock()

    def add_event(self, channel: str, event: dict[str, Any]) -> None:
        """Add event from EventConsumer (thread-safe)."""
        with self._lock:
            self._state.add_event(channel, event)
            self._last_update_time = time.time()

    def get_gametick_state(self) -> dict[str, Any]:
        """Get latest gametick state with tick, energy, position, etc."""
        with self._lock:
            return self._state.latest_states.get("gametick", {}).copy()

    def get_recent_events(self, channel: str, n: int | None = None) -> list[dict[str, Any]]:
        """Get recent events from ring buffer channel (newest last)."""
        with self._lock:
            events = list(self._state.recent_events[channel])
            if n is not None:
                events = events[-n:]
            return events

    def get_all_recent_events(self) -> dict[str, list[dict[str, Any]]]:
        """Get all recent events across all ring buffer channels."""
        with self._lock:
            return {channel: list(events) for channel, events in self._state.recent_events.items()}

    def get_last_update_time(self) -> float:
        """Get timestamp of last cache update (Unix timestamp)."""
        with self._lock:
            return self._last_update_time

    def get_age(self) -> float:
        """Get age of cached data in seconds since last update."""
        with self._lock:
            if self._last_update_time == 0:
                return float("inf")
            return time.time() - self._last_update_time

    def is_fresh(self, max_age: float = 1.0) -> bool:
        """Check if cache data is fresh (age < max_age)."""
        return self.get_age() < max_age

    def clear(self) -> None:
        """Clear all cached data and reset update time."""
        with self._lock:
            self._state.latest_states.clear()
            self._state.recent_events.clear()
            self._state.varps.clear()
            self._state.skills.clear()
            self._state.inventory = [-1] * 28
            self._state.equipment.clear()
            self._state.bank.clear()
            self._last_update_time = 0.0

    @property
    def tick(self) -> int | None:
        """Get current game tick from latest gametick state."""
        gametick = self._state.latest_states.get("gametick", {})
        return gametick.get("tick")

    @property
    def energy(self) -> int | None:
        """Get current run energy (0-10000) from latest gametick state."""
        gametick = self._state.latest_states.get("gametick", {})
        return gametick.get("energy")

    @property
    def position(self) -> dict[str, int] | None:
        """Get current player world position {x, y, plane}."""
        gametick = self._state.latest_states.get("gametick", {})
        world_view = self._state.latest_states.get("world_view_loaded", {})

        scene_x = gametick.get("sceneX")
        scene_y = gametick.get("sceneY")
        if scene_x is None or scene_y is None:
            return None

        base_x = world_view.get("base_x", 0)
        base_y = world_view.get("base_y", 0)
        plane = world_view.get("plane", 0)

        return {"x": scene_x + base_x, "y": scene_y + base_y, "plane": plane}

    @property
    def scene_position(self) -> dict[str, int] | None:
        """Get current player scene position {sceneX, sceneY}."""
        gametick = self._state.latest_states.get("gametick", {})
        scene_x = gametick.get("sceneX")
        scene_y = gametick.get("sceneY")
        if scene_x is None or scene_y is None:
            return None
        return {"sceneX": scene_x, "sceneY": scene_y}

    @property
    def target_location(self) -> dict[str, int] | None:
        """Get current destination location {x, y} where player is walking to."""
        gametick = self._state.latest_states.get("gametick", {})
        x = gametick.get("target_location_x")
        y = gametick.get("target_location_y")
        if x is None or y is None:
            return None
        return {"x": x, "y": y}

    def get_varp(self, varp_id: int) -> int | None:
        """Get current value of a varp from cache."""
        with self._lock:
            if len(self._state.varps) < varp_id + 1 and not self._state.varps_initialized:
                self._state.init_varps()
            if varp_id >= len(self._state.varps):
                return None
            return self._state.varps[varp_id]

    def get_varc(self, varc_id: int) -> Any | None:
        """Get current value of a varc from cache."""
        with self._lock:
            varc = self._state.varcs.get(varc_id, None)
            if varc is None and not self._state.varcs_initialized:
                self._state.init_varcs()
                varc = self._state.varcs.get(varc_id, None)
            return varc

    def get_all_skills(self) -> dict[str, dict[str, int]]:
        """Get all tracked skills as dict mapping name to skill data."""
        with self._lock:
            if len(self._state.skills) != 24:
                self._state.init_skills()
            return self._state.skills.copy()

    def get_ground_items(self) -> dict[int, Any]:
        """Get current ground items state as dict of packed coords to item lists."""
        with self._lock:
            if (
                self._state.latest_states.get("ground_items") is None
                and not self._state.ground_items_initialized
            ):
                self._state.init_ground_items()
                if wait_until(
                    lambda: self._state.latest_states.get("ground_items") is not None, timeout=5
                ):
                    self._state.ground_items_initialized = True

            raw = self._state.latest_states.get("ground_items", {})
            normalized: dict[int, Any] = {}
            if isinstance(raw, dict):
                for key, value in raw.items():
                    if isinstance(key, int):
                        normalized[key] = value
                    elif isinstance(key, str) and key.lstrip("-").isdigit():
                        normalized[int(key)] = value
            return normalized

    def get_item_container(self, container_id: int) -> ItemContainer | None:
        """Get item container by ID (93=inventory, 94=equipment, 95=bank)."""
        with self._lock:
            containers = self._state.itemcontainers
            if not containers:
                return None

            if container_id in [93, 94] and not self._state.containers_initialized:
                inventory = self._state.itemcontainers.get(93)
                equipment = self._state.itemcontainers.get(94)
                if inventory:
                    inventory.populate()
                if equipment:
                    equipment.populate()
                self._state.containers_initialized = True

            if container_id not in containers:
                containers[container_id] = ItemContainer(container_id, -1)

            return self._state.itemcontainers.get(container_id, None)

    def get_menu_options(self) -> dict[str, Any]:
        """Get latest menu options."""
        with self._lock:
            menu_state = self._state.latest_states.get("post_menu_sort", {})
            return menu_state.copy() if isinstance(menu_state, dict) else {}

    def get_menu_open_state(self) -> dict[str, Any]:
        """Get latest menu open state."""
        with self._lock:
            return self._state.latest_states.get("menu_open", {}).copy()

    def get_last_selected_widget(self) -> dict[str, Any]:
        """Get latest selected widget state."""
        with self._lock:
            return self._state.latest_states.get("selected_widget", {}).copy()

    def get_menu_clicked_state(self) -> dict[str, Any]:
        """Get latest menu option clicked state."""
        with self._lock:
            return self._state.latest_states.get("menu_option_clicked", {}).copy()

    def consume_menu_clicked_state(self) -> dict[str, Any]:
        with self._lock:
            if "menu_option_clicked" in self._state.latest_states:
                self._state.latest_states["menu_option_clicked"]["consumed"] = True
                return self._state.latest_states["menu_option_clicked"].copy()
            return {}

    def is_menu_option_clicked_consumed(self) -> bool:
        with self._lock:
            menu_clicked = self._state.latest_states.get("menu_option_clicked", {})
            return menu_clicked.get("consumed", False)

    def get_open_widgets(self) -> list[int]:
        """Get list of currently open widgets."""
        with self._lock:
            raw = self._state.latest_states.get("active_interfaces", {}).get(
                "active_interfaces", []
            )
            if not isinstance(raw, list):
                return []
            result: list[int] = []
            for item in raw:
                if isinstance(item, int):
                    result.append(item)
                elif isinstance(item, dict):
                    value = item.get("id")
                    if isinstance(value, int):
                        result.append(value)
            return result

    def get_camera_state(
        self,
    ) -> tuple[float, float, float, float, float, int, int, int, int, int] | None:
        """Get current camera state for projection calculations, or None if unavailable."""
        with self._lock:
            camera = self._state.latest_states.get("camera_changed")
            if not camera:
                return None

            return (
                camera.get("cameraX", 0),
                camera.get("cameraY", 0),
                camera.get("cameraZ", 0),
                camera.get("cameraPitch", 0.0),
                camera.get("cameraYaw", 0.0),
                camera.get("scale", 512),
                camera.get("viewportWidth", 765),
                camera.get("viewportHeight", 503),
                camera.get("viewportXOffset", 0),
                camera.get("viewportYOffset", 0),
            )

    def get_camera_state_dict(self) -> dict[str, Any]:
        """Get current camera state as a dictionary."""
        with self._lock:
            return self._state.latest_states.get("camera_changed", {}).copy()

    def get_entity_transform(self) -> tuple[int, int, int, int] | None:
        """Get WorldEntity transform for projection, or None if top-level world."""
        with self._lock:
            entity = self._state.latest_states.get("world_entity")
            if not entity:
                return None

            return (
                entity.get("entityX", 0),
                entity.get("entityY", 0),
                entity.get("orientation", 0),
                entity.get("groundHeightOffset", 0),
            )

    def get_entity_transform_dict(self) -> dict[str, Any]:
        """Get current WorldEntity transform as a dictionary."""
        with self._lock:
            return self._state.latest_states.get("world_entity", {}).copy()

    def get_world_view_state(self) -> dict[str, Any]:
        """Get current world view state with scene dimensions and tile heights."""
        with self._lock:
            return self._state.latest_states.get("world_view_loaded", {}).copy()

    def get_current_plane(self) -> int:
        """Get current plane/level (0-3), defaults to 0."""
        with self._lock:
            world_view = self._state.latest_states.get("world_view_loaded", {})
            return world_view.get("plane", 0)

    def get_skill(self, skill_name: str) -> dict[str, int] | None:
        """Get a specific skill's data by name."""
        with self._lock:
            if len(self._state.skills) != 24:
                self._state.init_skills()
            return self._state.skills.get(skill_name)


if __name__ == "__main__":
    # Simple test
    cache = EventCache()
    print(cache.get_skill("Attack"))
