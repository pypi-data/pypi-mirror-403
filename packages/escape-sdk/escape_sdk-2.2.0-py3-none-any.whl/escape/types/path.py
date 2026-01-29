"""
Path and obstacle types for navigation.

Uses numpy arrays for efficient coordinate storage and projection integration.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np

from .packed_position import PackedPosition

if TYPE_CHECKING:
    from escape.types import Point, Quad
    from escape.world.projection import TileGrid


@dataclass
class PathObstacle:
    """Represents an obstacle along a path with origin, destination, and timing."""

    origin: PackedPosition
    dest: PackedPosition
    type: str
    duration: int
    display_info: str | None
    object_info: str | None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PathObstacle":
        """Create PathObstacle from dict."""
        return cls(
            origin=PackedPosition.from_packed(data["origin"]),
            dest=PackedPosition.from_packed(data["dest"]),
            type=data["type"],
            duration=data["duration"],
            display_info=data.get("displayInfo"),
            object_info=data.get("objectInfo"),
        )

    def __repr__(self) -> str:
        name = self.display_info or self.object_info or self.type
        return f"PathObstacle({name}, {self.duration} ticks)"


class Path:
    """Navigation path with numpy-backed coordinate storage for efficient vectorized operations."""

    __slots__ = ("_obstacles", "_packed")

    def __init__(self, packed: np.ndarray, obstacles: list[PathObstacle]):
        """Initialize path with packed positions and obstacles."""
        self._packed = packed.astype(np.int32)
        self._obstacles = obstacles

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Path":
        """Create Path from Java response dict."""
        # Direct numpy conversion - instant for any size
        packed = np.array(data["path"], dtype=np.int32)

        # Obstacles are few, so list comprehension is fine
        obstacles = [PathObstacle.from_dict(obs) for obs in data.get("obstacles", [])]

        return cls(packed, obstacles)

    @property
    def world_x(self) -> np.ndarray:
        """World X coordinates (vectorized). Shape: [length]. X is bits 0-14."""
        return (self._packed & 0x7FFF).astype(np.int32)

    @property
    def world_y(self) -> np.ndarray:
        """World Y coordinates (vectorized). Shape: [length]. Y is bits 15-29."""
        return ((self._packed >> 15) & 0x7FFF).astype(np.int32)

    @property
    def plane(self) -> np.ndarray:
        """Plane values (vectorized). Shape: [length]."""
        return ((self._packed >> 30) & 0x3).astype(np.int32)

    @property
    def packed(self) -> np.ndarray:
        """Raw packed integers. Shape: [length]."""
        return self._packed

    def _get_tile_grid(self) -> "TileGrid | None":
        """Get cached TileGrid from projection."""
        from escape.world.projection import projection

        return projection.tiles

    def get_scene_coords(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Convert world coords to scene coords, returning (scene_x, scene_y, in_scene_mask)."""
        grid = self._get_tile_grid()
        if grid is None:
            empty = np.array([], dtype=np.int32)
            return empty, empty, np.array([], dtype=np.bool_)

        scene_x = self.world_x - grid.base_x
        scene_y = self.world_y - grid.base_y

        in_scene = (
            (scene_x >= 0) & (scene_x < grid.size_x) & (scene_y >= 0) & (scene_y < grid.size_y)
        )

        return scene_x, scene_y, in_scene

    def get_screen_coords(self, margin: int = 0) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Get screen coordinates for path tiles, returning (screen_x, screen_y, visible_mask)."""
        grid = self._get_tile_grid()
        if grid is None or len(self._packed) == 0:
            empty = np.array([], dtype=np.int32)
            return empty, empty, np.array([], dtype=np.bool_)

        scene_x, scene_y, in_scene = self.get_scene_coords()

        # Initialize output arrays
        n = len(self._packed)
        screen_x = np.zeros(n, dtype=np.int32)
        screen_y = np.zeros(n, dtype=np.int32)
        visible = np.zeros(n, dtype=np.bool_)

        if not in_scene.any():
            return screen_x, screen_y, visible

        # Get tile indices for in-scene tiles (clip to valid range)
        clipped_x = scene_x.clip(0, grid.size_x - 1)
        clipped_y = scene_y.clip(0, grid.size_y - 1)
        tile_idx = clipped_x * grid.size_y + clipped_y

        # Get centers from grid cache
        center_x, center_y = grid.get_tile_centers()
        screen_x = center_x[tile_idx]
        screen_y = center_y[tile_idx]

        # Visibility: in scene + valid tile + on screen
        tile_valid = grid.tile_valid[tile_idx]

        if margin == 0:
            on_screen = (
                (screen_x >= grid.view_min_x)
                & (screen_x < grid.view_max_x)
                & (screen_y >= grid.view_min_y)
                & (screen_y < grid.view_max_y)
            )
        else:
            on_screen = (
                (screen_x >= grid.view_min_x - margin)
                & (screen_x < grid.view_max_x + margin)
                & (screen_y >= grid.view_min_y - margin)
                & (screen_y < grid.view_max_y + margin)
            )

        visible = in_scene & tile_valid & on_screen

        return screen_x, screen_y, visible

    def get_visible_indices(self, margin: int = 0) -> np.ndarray:
        """Get indices of path tiles visible on screen."""
        _, _, visible = self.get_screen_coords(margin=margin)
        return np.where(visible)[0]

    def get_visible_quads(self) -> list["Quad"]:
        """Get Quads for all visible path tiles."""
        grid = self._get_tile_grid()
        if grid is None:
            return []

        scene_x, scene_y, in_scene = self.get_scene_coords()
        indices = np.where(in_scene)[0]

        quads = []
        for i in indices:
            sx, sy = scene_x[i], scene_y[i]
            tile_idx = int(sx * grid.size_y + sy)
            if grid.tile_on_screen[tile_idx]:
                quads.append(grid.get_tile_quad(tile_idx))

        return quads

    def get_screen_point(self, i: int) -> "Point | None":
        """Get screen Point for path tile at index, or None if not in scene."""
        from escape.types import Point

        grid = self._get_tile_grid()
        if grid is None or i < 0 or i >= len(self._packed):
            return None

        scene_x = int(self.world_x[i]) - grid.base_x
        scene_y = int(self.world_y[i]) - grid.base_y

        if not (0 <= scene_x < grid.size_x and 0 <= scene_y < grid.size_y):
            return None

        tile_idx = scene_x * grid.size_y + scene_y
        if not grid.tile_valid[tile_idx]:
            return None

        center_x, center_y = grid.get_tile_centers()
        return Point(int(center_x[tile_idx]), int(center_y[tile_idx]))

    def get_quad(self, i: int) -> "Quad | None":
        """Get Quad for path tile at index, or None if not in scene."""
        grid = self._get_tile_grid()
        if grid is None or i < 0 or i >= len(self._packed):
            return None

        scene_x = int(self.world_x[i]) - grid.base_x
        scene_y = int(self.world_y[i]) - grid.base_y

        if not (0 <= scene_x < grid.size_x and 0 <= scene_y < grid.size_y):
            return None

        tile_idx = scene_x * grid.size_y + scene_y
        return grid.get_tile_quad(tile_idx)

    @property
    def obstacles(self) -> list[PathObstacle]:
        """Get all obstacles in path."""
        return self._obstacles

    def length(self) -> int:
        """Get path length in tiles."""
        return len(self._packed)

    def is_empty(self) -> bool:
        """Check if path is empty."""
        return len(self._packed) == 0

    def get_position(self, i: int) -> PackedPosition | None:
        """Get PackedPosition at index, or None if out of bounds."""
        if i < 0 or i >= len(self._packed):
            return None
        return PackedPosition.from_packed(int(self._packed[i]))

    def get_start(self) -> PackedPosition | None:
        """Get start position."""
        return self.get_position(0)

    def get_end(self) -> PackedPosition | None:
        """Get end position (destination)."""
        return self.get_position(len(self._packed) - 1)

    def get_next_tile(self, current: PackedPosition) -> PackedPosition | None:
        """Get next tile from current position, or None if at end."""
        # Vectorized search
        matches = np.where(self._packed == current.packed)[0]
        if len(matches) == 0:
            return None
        idx = matches[0]
        if idx < len(self._packed) - 1:
            return PackedPosition.from_packed(int(self._packed[idx + 1]))
        return None

    def get_obstacle_at(self, position: PackedPosition) -> PathObstacle | None:
        """Get obstacle at position, or None if no obstacle."""
        for obstacle in self._obstacles:
            if obstacle.origin == position:
                return obstacle
        return None

    def has_obstacles(self) -> bool:
        """Check if path has any obstacles."""
        return len(self._obstacles) > 0

    def get_total_duration(self) -> int:
        """Get total estimated duration in ticks (walking + obstacles)."""
        # Approximate: 1 tile = 1 tick walking
        walk_ticks = len(self._packed)
        obstacle_ticks = sum(obs.duration for obs in self._obstacles)
        return walk_ticks + obstacle_ticks

    def get_total_seconds(self) -> float:
        """Get total estimated duration in seconds (ticks * 0.6)."""
        return self.get_total_duration() * 0.6

    def distance_to_tile(self, world_x: int, world_y: int) -> np.ndarray:
        """Calculate Chebyshev distance from each path tile to a point."""
        dx = np.abs(self.world_x - world_x)
        dy = np.abs(self.world_y - world_y)
        return np.maximum(dx, dy)

    def find_closest_tile(self, world_x: int, world_y: int) -> int:
        """Find index of path tile closest to a point, or -1 if empty."""
        if len(self._packed) == 0:
            return -1
        return int(self.distance_to_tile(world_x, world_y).argmin())

    def slice_from(self, start_idx: int) -> "Path":
        """Create new Path starting from given index."""
        if start_idx < 0 or start_idx >= len(self._packed):
            return Path(np.array([], dtype=np.int32), [])

        new_packed = self._packed[start_idx:]

        # Filter obstacles that are still ahead
        remaining_positions = set(new_packed.tolist())
        new_obstacles = [obs for obs in self._obstacles if obs.origin.packed in remaining_positions]

        return Path(new_packed, new_obstacles)

    def __len__(self) -> int:
        """Support len() builtin."""
        return len(self._packed)

    def __iter__(self):
        """Iterate over PackedPosition objects (creates on-demand)."""
        for p in self._packed:
            yield PackedPosition.from_packed(int(p))

    def __getitem__(self, index) -> PackedPosition:
        """Support indexing (creates PackedPosition on-demand)."""
        return PackedPosition.from_packed(int(self._packed[index]))

    def __repr__(self) -> str:
        return (
            f"Path({len(self._packed)} tiles, {len(self._obstacles)} obstacles, "
            f"~{self.get_total_seconds():.1f}s)"
        )
