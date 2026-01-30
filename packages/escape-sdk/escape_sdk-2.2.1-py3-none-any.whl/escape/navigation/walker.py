"""Walker module - handles walking from point A to point B with target tracking."""

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from escape.types import Quad
    from escape.types.path import Path

# Local coordinate units per tile (RuneLite LocalPoint)
LOCAL_UNITS_PER_TILE = 128


class Walker:
    """Walker for navigating with smart target tracking."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self):
        """Actual initialization, runs once."""
        pass

    def _get_player_position(self) -> tuple[int, int, int] | None:
        """Get player world position (x, y, plane) from cache."""
        from escape.client import client

        pos = client.cache.position
        if pos is None:
            return None
        return (pos.get("x", 0), pos.get("y", 0), pos.get("plane", 0))

    def _get_player_scene_position(self) -> tuple[int, int] | None:
        """Get player scene position (scene_x, scene_y) from cache."""
        from escape.client import client

        pos = client.cache.scene_position
        if pos is None:
            return None
        return (pos.get("sceneX", 0), pos.get("sceneY", 0))

    def _get_target_scene_position(self) -> tuple[int, int] | None:
        """Get current walk target in scene coordinates."""
        from escape.client import client

        target = client.cache.target_location
        if target is None:
            return None

        local_x = target.get("x")
        local_y = target.get("y")
        if local_x is None or local_y is None:
            return None

        # Convert local to scene coords (128 local units = 1 tile)
        scene_x = local_x // LOCAL_UNITS_PER_TILE
        scene_y = local_y // LOCAL_UNITS_PER_TILE

        return (scene_x, scene_y)

    def _distance_to_target(self) -> int | None:
        """Get Chebyshev distance from player to current walk target."""
        player_pos = self._get_player_scene_position()
        target_pos = self._get_target_scene_position()

        if player_pos is None or target_pos is None:
            return None

        player_x, player_y = player_pos
        target_x, target_y = target_pos

        return max(abs(target_x - player_x), abs(target_y - player_y))

    def has_target(self) -> bool:
        """Check if player currently has a walk target."""
        return self._get_target_scene_position() is not None

    def is_near_target(self, threshold: int = 2) -> bool:
        """Check if player is near their current walk target (within threshold tiles)."""
        dist = self._distance_to_target()
        if dist is None:
            return True  # No target = effectively "at" target

        return dist <= threshold

    def should_click_new_tile(self, threshold: int = 2) -> bool:
        """Determine if we should click a new tile (idle or near target)."""
        return self.is_near_target(threshold=threshold)

    def _find_first_obstacle_index(self, path: "Path") -> int:
        """Find the index of the first obstacle on the path."""
        if not path.has_obstacles():
            return path.length()

        # Find the earliest obstacle origin
        first_obstacle_idx = path.length()
        for obstacle in path.obstacles:
            # Find where this obstacle's origin is on the path
            matches = np.where(path.packed == obstacle.origin.packed)[0]
            if len(matches) > 0:
                idx = int(matches[0])
                if idx < first_obstacle_idx:
                    first_obstacle_idx = idx

        return first_obstacle_idx

    def _select_walk_tile(
        self,
        path: "Path",
        visible_indices: np.ndarray,
        player_x: int,
        player_y: int,
        max_index: int,
    ) -> int | None:
        """Select the optimal tile to click for walking (visible, clickable, far enough)."""
        from escape.world.scene import scene

        # Filter to tiles before obstacle
        valid_indices = visible_indices[visible_indices < max_index]

        if len(valid_indices) == 0:
            return None

        # Filter by Chebyshev distance <= 19 (same as Java isTileClickable)
        world_x = path.world_x[valid_indices]
        world_y = path.world_y[valid_indices]
        dist = np.maximum(np.abs(world_x - player_x), np.abs(world_y - player_y))
        within_range = dist <= 19
        valid_indices = valid_indices[within_range]

        if len(valid_indices) == 0:
            return None

        # Get tile grid for viewport bounds
        grid = scene._get_tile_grid()
        if grid is None:
            return None

        # Filter to tiles whose quad is FULLY inside viewport (all 4 corners)
        clickable_indices = []
        for idx in valid_indices:
            quad = path.get_quad(int(idx))
            if quad is not None:
                # Check all 4 vertices are inside viewport
                all_inside = all(
                    grid.view_min_x <= p.x <= grid.view_max_x
                    and grid.view_min_y <= p.y <= grid.view_max_y
                    for p in quad.vertices
                )
                if all_inside:
                    clickable_indices.append(int(idx))

        if len(clickable_indices) == 0:
            return None

        clickable_indices = np.array(clickable_indices)

        # Get world coordinates for clickable tiles
        world_x = path.world_x[clickable_indices]
        world_y = path.world_y[clickable_indices]

        # Calculate distance from player (Chebyshev)
        dist = np.maximum(np.abs(world_x - player_x), np.abs(world_y - player_y))

        # Filter out tiles too close (< 3 tiles away)
        far_enough = dist >= 3
        if not far_enough.any():
            # If all tiles are close, just pick the furthest
            best_local = int(np.argmax(dist))
            return int(clickable_indices[best_local])

        # Among far enough tiles, pick the one furthest along the path
        # (which is the highest index in clickable_indices)
        far_mask = np.array(far_enough)
        far_indices = clickable_indices[far_mask]
        return int(far_indices[-1])  # Last one is furthest along path

    def click_tile(self, world_x: int, world_y: int) -> bool:
        """Click a specific world tile to walk to it."""
        from escape.client import client
        from escape.world.scene import scene

        # Get the quad for this tile
        quad = scene.get_tile_quad(world_x, world_y)
        if quad is None:
            return False

        # Hover on the tile
        quad.hover()

        # Wait for WALK action to appear in menu
        if not client.interactions.menu.wait_has_type("WALK", timeout=0.5):
            return False

        # Click the walk action
        return client.interactions.menu.click_option_type("WALK")

    def walk_to(
        self,
        dest_x: int,
        dest_y: int,
        dest_plane: int = 0,
        margin: int = 50,
        near_target_threshold: int = 2,
    ) -> bool:
        """Walk towards destination by clicking a tile along the path."""
        from escape.navigation.pathfinder import pathfinder

        # Get player position
        player_pos = self._get_player_position()
        if player_pos is None:
            return False

        player_x, player_y, player_plane = player_pos

        # Check if already at destination
        if player_x == dest_x and player_y == dest_y and player_plane == dest_plane:
            return True  # Already there

        # Check if we should click a new tile or wait
        if not self.should_click_new_tile(threshold=near_target_threshold):
            # Still walking to current target, no need to click
            return True  # Return True because we're making progress

        # Get path to destination
        path = pathfinder.get_path(dest_x, dest_y, dest_plane)
        if path is None or path.is_empty():
            return False

        # Find first obstacle (we'll walk up to it)
        obstacle_idx = self._find_first_obstacle_index(path)

        # Get visible path tiles (with margin to avoid edge clicks)
        visible_indices = path.get_visible_indices(margin=margin)

        if len(visible_indices) == 0:
            # No visible path tiles - might need to turn camera or wait
            return False

        # Select optimal tile to click
        target_idx = self._select_walk_tile(path, visible_indices, player_x, player_y, obstacle_idx)

        if target_idx is None:
            return False

        # Get the quad for this tile
        quad = path.get_quad(target_idx)
        if quad is None:
            return False

        # Click the tile
        return self._click_walk_quad(quad)

    def _click_walk_quad(self, quad: "Quad") -> bool:
        """Hover over quad and click with WALK action."""
        from escape.client import client

        # Hover on the tile
        quad.hover()

        # Wait for WALK action to appear in menu
        if not client.interactions.menu.wait_has_type("WALK", timeout=0.5):
            return False

        # Click the walk action
        return client.interactions.menu.click_option_type("WALK")

    def is_moving(self) -> bool:
        """Check if player is currently moving (has a walk target)."""
        return self.has_target()

    def distance_to_destination(self, dest_x: int, dest_y: int) -> int:
        """Get Chebyshev distance from player to destination (-1 if unknown)."""
        player_pos = self._get_player_position()
        if player_pos is None:
            return -1

        player_x, player_y, _ = player_pos
        return max(abs(dest_x - player_x), abs(dest_y - player_y))


# Module-level instance
walker = Walker()
