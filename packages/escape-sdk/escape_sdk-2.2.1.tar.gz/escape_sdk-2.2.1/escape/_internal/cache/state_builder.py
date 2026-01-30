"""Builds derived game state from events."""

from collections import defaultdict, deque
from time import time
from typing import Any

import numpy as np

from escape._internal.events.channels import LATEST_STATE_CHANNELS
from escape._internal.logger import logger
from escape._internal.resources import varps as varps_resource
from escape.globals import get_api
from escape.types import ItemContainer

# Skill names constant - defined here to avoid circular import with tabs.skills
# Note: Also defined in tabs/skills.py for public API access
SKILL_NAMES = [
    "Attack",
    "Defence",
    "Strength",
    "Hitpoints",
    "Ranged",
    "Prayer",
    "Magic",
    "Cooking",
    "Woodcutting",
    "Fletching",
    "Fishing",
    "Firemaking",
    "Crafting",
    "Smithing",
    "Mining",
    "Herblore",
    "Agility",
    "Thieving",
    "Slayer",
    "Farming",
    "Runecrafting",
    "Hunter",
    "Construction",
    "Sailing",
]


class StateBuilder:
    """Processes events and maintains game state."""

    def __init__(self, event_history_size: int = 100):
        """Initialize with empty state."""
        # Latest-state channels (overwritten, no history)
        self.latest_states: dict[str, dict[str, Any]] = {}

        # Ring buffer channels (last N events)
        self.recent_events: dict[str, deque] = defaultdict(lambda: deque(maxlen=event_history_size))

        self.recently_changed_containers: deque = deque(maxlen=100)

        # Derived state from ring buffer events
        self.varps: list[int] = []  # {varp_id: value}
        self.varcs: dict[int, Any] = {}  # {varc_id: value}

        self.skills: dict[str, dict[str, int]] = {}  # {skill_name: {level, xp, boosted_level}}
        self.last_click: dict[str, Any] = {}  # {button, coords, time}
        self.chat_history: deque = deque(maxlen=100)  # Last 100 chat messages
        self.current_state: dict[str, Any] = {}  # Other derived state as needed
        self.animating_actors: dict[str, Any] = defaultdict(dict)  # Actors currently animating

        self.ground_items_initialized = False
        self.varps_initialized = False
        self.varcs_initialized = False
        self.skills_initialized = False
        self.containers_initialized = False

        self.itemcontainers: dict[int, ItemContainer] = {}
        self.inventory: list[int] = [-1] * 28  # Legacy inventory state

        self.itemcontainers[93] = ItemContainer(93, 28)  # Inventory
        self.itemcontainers[94] = ItemContainer(94, 14)  # Equipment
        self.itemcontainers[95] = ItemContainer(95, -1)  # Bank

    @property
    def equipment(self) -> ItemContainer:
        """Get the equipment container (ID 94)."""
        return self.itemcontainers[94]

    @property
    def bank(self) -> ItemContainer:
        """Get the bank container (ID 95)."""
        return self.itemcontainers[95]

    def add_event(self, channel: str, event: dict[str, Any]) -> None:
        """Process incoming event and update state."""
        if channel in LATEST_STATE_CHANNELS:
            # Latest-state: just overwrite
            event["_timestamp"] = time()
            self.latest_states[channel] = event

            # Handle projection-related events immediately
            if channel == "world_view_loaded":
                self._process_world_view_loaded(event)
            elif channel in ("camera_changed", "world_entity"):
                self._process_camera_changed()
        else:
            # Ring buffer: store history + update derived state
            self.recent_events[channel].append(event)
            self._process_event(channel, event)

    def _process_event(self, channel: str, event: dict[str, Any]) -> None:
        """Update derived state from ring buffer event."""
        if channel == "varbit_changed":
            self._process_varbit_changed(event)
        elif channel in ["var_client_int_changed", "var_client_str_changed"]:
            self._process_varc_changed(event)
        elif channel == "item_container_changed":
            self._process_item_container_changed(event)
        elif channel == "stat_changed":
            self._process_stat_changed(event)
        elif channel == "animation_changed":
            actor_name = event.get("actor_name")
            animation_id = event.get("animation_id")
            if actor_name is not None:
                self.animating_actors[actor_name] = {
                    "animation_id": animation_id,
                    "location": event.get("location"),
                    "timestamp": event.get("_timestamp", time()),
                }
        elif channel == "chat_message":
            message = event.get("message", "")
            msgtype = event.get("type", "")
            timestamp = event.get("_timestamp", time())
            self.chat_history.append({"message": message, "type": msgtype, "timestamp": timestamp})
        elif channel == "item_spawned":
            pass  # Could implement item spawn tracking if needed
        elif channel == "item_despawned":
            pass  # Could implement item despawn tracking if needed

    def _edit_varp(self, varp_id: int, new_value: int) -> None:
        """Set a varp to a new value."""
        # Ensure varps list is large enough
        if varp_id >= len(self.varps):
            # Extend list with zeros
            self.varps.extend([0] * (varp_id - len(self.varps) + 1))

        self.varps[varp_id] = new_value

    def _edit_varc(self, varc_id: int, new_value: Any) -> None:
        """Set a varc to a new value."""
        if (len(self.varcs) == 0) and (not self.varcs_initialized):
            self.init_varcs()
        self.varcs[varc_id] = new_value

    def _edit_varbit(self, varbit_id: int, varp_id: int, new_value: int) -> None:
        """Update a varbit value by modifying specific bits in its parent varp."""
        # Get varbit metadata from resources (direct import to avoid race condition)
        varbit_info = varps_resource.get_varbit_info(varbit_id)

        if not varbit_info:
            return

        # Get bit positions
        lsb = varbit_info["lsb"]  # Least significant bit
        msb = varbit_info["msb"]  # Most significant bit

        # Ensure varps list is large enough
        if varp_id >= len(self.varps) and not self.varps_initialized:
            self.init_varps()
            if varp_id >= len(self.varps):
                return  # Invalid varp_id

        # Get current varp value
        current_varp = self.varps[varp_id]

        # Calculate bit manipulation
        num_bits = msb - lsb + 1
        bit_mask = (1 << num_bits) - 1  # Create mask for the bit range

        # Clear the bits in the current varp value
        clear_mask = ~(bit_mask << lsb)  # Invert mask and shift to position
        cleared_varp = current_varp & clear_mask

        # Insert new value at the correct position
        shifted_value = (new_value & bit_mask) << lsb
        new_varp = cleared_varp | shifted_value

        # Update the varp
        self.varps[varp_id] = new_varp

    def _process_varbit_changed(self, event: dict[str, Any]) -> None:
        """Update varbit/varp state from event."""
        varbit_id = event.get("varbit_id")
        varp_id = event.get("varp_id")
        value = event.get("value")

        if not isinstance(varp_id, int):
            return  # Invalid event
        if not isinstance(value, int):
            return  # Invalid event

        # Special case: varbit_id == -1 means update full varp
        if varbit_id == -1 or varbit_id is None:
            self._edit_varp(varp_id, value)
        else:
            # Update varbit (with bit manipulation)
            if isinstance(varbit_id, int):
                self._edit_varbit(varbit_id, varp_id, value)

    def _process_varc_changed(self, event: dict[str, Any]) -> None:
        """Update varc state from event."""
        varc_id = event.get("varc_id")
        value = event.get("value")

        if varc_id is None:
            return  # Invalid event

        self._edit_varc(varc_id, value)

    def _process_item_container_changed(self, event: dict[str, Any]) -> None:
        """Update inventory/equipment/bank from event."""
        container_id = event.get("container_id")
        items_list = event.get("items", [])

        if not isinstance(container_id, int):
            return

        self.recently_changed_containers.append(
            [container_id, time()]
        )  # Keep track of last 100 changed containers

        if not self.itemcontainers.get(container_id):
            self.itemcontainers[container_id] = ItemContainer(container_id, -1)

        if items_list is None:
            return

        self.itemcontainers[container_id].from_array(items_list)

    def _process_stat_changed(self, event: dict[str, Any]) -> None:
        """Update skill levels/XP from stat_changed event."""
        skill_name = event.get("skill")
        if not skill_name:
            return

        # Store skill data
        self.skills[skill_name] = {
            "level": event.get("level", 1),
            "xp": event.get("xp", 0),
            "boosted_level": event.get("boosted_level", event.get("level", 1)),
        }

    def init_varps(self) -> None:
        api = get_api()
        q = api.query()
        v = q.client.getServerVarps()
        results = q.execute({"varps": v})
        varps = results["results"].get("varps", [])
        if len(varps) > 1000:
            self.varps = varps
            self.varps_initialized = True

    def init_varcs(self) -> None:
        api = get_api()
        q = api.query()
        v = q.client.getVarcMap()
        results = q.execute({"varcs": v})
        varcs = results["results"].get("varcs", {})
        if len(varcs) > 0:
            self.varcs = varcs
            self.varcs_initialized = True

    def init_skills(self) -> None:
        api = get_api()
        q = api.query()
        levels = q.client.getRealSkillLevels()
        xps = q.client.getSkillExperiences()
        boosted_levels = q.client.getBoostedSkillLevels()
        results = q.execute({"levels": levels, "xps": xps, "boosted_levels": boosted_levels})
        if len(results["results"].get("levels", {})) > 0:
            self.skills_initialized = True
            for index, skill in enumerate(SKILL_NAMES):
                leveldata = results["results"].get("levels", {})
                xpdata = results["results"].get("xps", {})
                boosteddata = results["results"].get("boosted_levels", {})
                self.skills[skill] = {
                    "level": leveldata[index],
                    "xp": xpdata[index],
                    "boosted_level": boosteddata[index],
                }

    def init_ground_items(self) -> None:
        """Initialize ground items via query."""
        api = get_api()

        try:
            api.invoke_custom_method(
                target="EventBusListener",
                method="rebuildGroundItems",
                signature="()V",
                args=[],
                async_exec=False,
            )
        except Exception as e:
            logger.error(f"Rebuild grounditems failed: {e}")
            return

    def _process_camera_changed(self) -> None:
        """Invalidate tile projection cache when camera changes."""
        from escape.world.projection import projection

        projection.invalidate()

    def _process_world_view_loaded(self, event: dict[str, Any]) -> None:
        """Configure Projection when world_view_loaded event is received."""
        from escape.world.projection import EntityConfig, projection

        # Extract scene data
        size_x = event.get("size_x", 104)
        size_y = event.get("size_y", 104)

        # Convert flat tile_heights list to [4, size_x, size_y] array
        tile_heights_list = event.get("tile_heights", [])
        if tile_heights_list:
            expected_tile_size = 4 * size_x * size_y
            if len(tile_heights_list) == expected_tile_size:
                tile_heights = np.array(tile_heights_list, dtype=np.int32).reshape(
                    4, size_x, size_y
                )
            else:
                # Handle size mismatch - pad or truncate
                arr = np.zeros(expected_tile_size, dtype=np.int32)
                arr[: min(len(tile_heights_list), expected_tile_size)] = tile_heights_list[
                    :expected_tile_size
                ]
                tile_heights = arr.reshape(4, size_x, size_y)
        else:
            # Fallback to zeros if no data
            tile_heights = np.zeros((4, size_x, size_y), dtype=np.int32)

        # Convert flat bridge_flags list to [size_x, size_y] array
        # Note: bridge_flags may be (size_x-1)*(size_y-1) or other sizes
        bridge_flags_list = event.get("bridge_flags", [])
        bridge_flags = np.zeros((size_x, size_y), dtype=np.bool_)
        if bridge_flags_list:
            flag_len = len(bridge_flags_list)
            # Try to infer the correct dimensions
            if flag_len == size_x * size_y:
                bridge_flags = np.array(bridge_flags_list, dtype=np.bool_).reshape(size_x, size_y)
            elif flag_len == (size_x - 1) * (size_y - 1):
                # Bridge flags may be for interior tiles only
                inner = np.array(bridge_flags_list, dtype=np.bool_).reshape(size_x - 1, size_y - 1)
                bridge_flags[:-1, :-1] = inner
            else:
                # Best effort: reshape to square if possible, otherwise fill what we can
                side = int(np.sqrt(flag_len))
                if side * side == flag_len and side <= size_x and side <= size_y:
                    inner = np.array(bridge_flags_list, dtype=np.bool_).reshape(side, side)
                    bridge_flags[:side, :side] = inner

        base_x = event.get("base_x", 0)
        base_y = event.get("base_y", 0)

        # Set scene data on projection and invalidate cache
        projection.set_scene(tile_heights, bridge_flags, base_x, base_y, size_x, size_y)
        projection.invalidate()

        # Handle entity config (for WorldEntity instances)
        # When on top-level, bounds are all 0, which means identity transform
        bounds_x = event.get("boundsX", 0)
        bounds_y = event.get("boundsY", 0)
        bounds_width = event.get("boundsWidth", 0)
        bounds_height = event.get("boundsHeight", 0)

        # Only set entity config if we have non-zero bounds (inside a WorldEntity)
        if bounds_width > 0 or bounds_height > 0:
            config = EntityConfig(
                bounds_x=bounds_x,
                bounds_y=bounds_y,
                bounds_width=bounds_width,
                bounds_height=bounds_height,
            )
            projection.set_entity_config(config)
        else:
            # Top-level world: use None for identity transform
            projection.set_entity_config(None)
