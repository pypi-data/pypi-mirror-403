"""Scene utilities for working with tiles in the loaded scene."""

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from escape.types import Point, Quad
    from escape.world.projection import TileGrid


class VisibleTiles:
    """Collection of visible tiles with numpy array access."""

    __slots__ = ("_grid", "_indices")

    def __init__(self, grid: "TileGrid", indices: np.ndarray):
        self._grid = grid
        self._indices = indices

    def __len__(self) -> int:
        return len(self._indices)

    @property
    def scene_x(self) -> np.ndarray:
        """Scene X coordinates of visible tiles."""
        return self._grid._scene_xs[self._indices]

    @property
    def scene_y(self) -> np.ndarray:
        """Scene Y coordinates of visible tiles."""
        return self._grid._scene_ys[self._indices]

    @property
    def world_x(self) -> np.ndarray:
        """World X coordinates of visible tiles."""
        return self._grid._scene_xs[self._indices].astype(np.int32) + self._grid.base_x

    @property
    def world_y(self) -> np.ndarray:
        """World Y coordinates of visible tiles."""
        return self._grid._scene_ys[self._indices].astype(np.int32) + self._grid.base_y

    @property
    def screen_x(self) -> np.ndarray:
        """Screen X coordinates of tile centers."""
        center_x, _ = self._grid.get_tile_centers()
        return center_x[self._indices]

    @property
    def screen_y(self) -> np.ndarray:
        """Screen Y coordinates of tile centers."""
        _, center_y = self._grid.get_tile_centers()
        return center_y[self._indices]

    @property
    def indices(self) -> np.ndarray:
        """Flat tile indices into the grid."""
        return self._indices

    def get_screen_point(self, i: int) -> "Point":
        """Get screen position of tile at local index i."""
        from escape.types import Point

        center_x, center_y = self._grid.get_tile_centers()
        idx = self._indices[i]
        return Point(int(center_x[idx]), int(center_y[idx]))

    def get_world_coord(self, i: int) -> tuple[int, int]:
        """Get world coordinates of tile at local index i."""
        idx = self._indices[i]
        return (
            int(self._grid._scene_xs[idx]) + self._grid.base_x,
            int(self._grid._scene_ys[idx]) + self._grid.base_y,
        )

    def get_quad(self, i: int) -> "Quad":
        """Get Quad for tile at local index i."""
        return self._grid.get_tile_quad(self._indices[i])


class Scene:
    """Utilities for working with tiles in the loaded scene."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _get_tile_grid(self) -> "TileGrid | None":
        """Get cached TileGrid from projection."""
        from escape.world.projection import projection

        return projection.tiles

    def _get_player_scene_pos(self) -> tuple[int, int] | None:
        """Get player scene position from cache."""
        from escape.globals import get_event_cache

        gt = get_event_cache().get_gametick_state()
        if not gt:
            return None
        x, y = gt.get("sceneX"), gt.get("sceneY")
        return (x, y) if x is not None and y is not None else None

    def get_visible_tiles(self, margin: int = 0) -> VisibleTiles | None:
        """Get all tiles visible on screen."""
        grid = self._get_tile_grid()
        if grid is None:
            return None

        indices = grid.get_visible_indices(margin=margin)
        return VisibleTiles(grid, indices)

    def get_visible_tiles_near_player(
        self, radius: int = 25, margin: int = 0
    ) -> VisibleTiles | None:
        """Get visible tiles within radius of player."""
        grid = self._get_tile_grid()
        if grid is None:
            return None

        pos = self._get_player_scene_pos()
        if pos is None:
            return None

        px, py = pos

        # Create mask for tiles near player
        near_mask = (
            (grid._scene_xs >= max(0, px - radius))
            & (grid._scene_xs <= min(grid.size_x - 1, px + radius))
            & (grid._scene_ys >= max(0, py - radius))
            & (grid._scene_ys <= min(grid.size_y - 1, py + radius))
        )

        indices = grid.get_visible_indices(mask=near_mask, margin=margin)
        return VisibleTiles(grid, indices)

    def get_tiles_in_area(
        self,
        world_x1: int,
        world_y1: int,
        world_x2: int,
        world_y2: int,
        margin: int = 0,
    ) -> VisibleTiles | None:
        """Get visible tiles in a world rectangle."""
        grid = self._get_tile_grid()
        if grid is None:
            return None

        # Convert to scene coords
        min_sx = max(0, min(world_x1, world_x2) - grid.base_x)
        max_sx = min(grid.size_x - 1, max(world_x1, world_x2) - grid.base_x)
        min_sy = max(0, min(world_y1, world_y2) - grid.base_y)
        max_sy = min(grid.size_y - 1, max(world_y1, world_y2) - grid.base_y)

        if min_sx > max_sx or min_sy > max_sy:
            return None

        # Create mask
        area_mask = (
            (grid._scene_xs >= min_sx)
            & (grid._scene_xs <= max_sx)
            & (grid._scene_ys >= min_sy)
            & (grid._scene_ys <= max_sy)
        )

        indices = grid.get_visible_indices(mask=area_mask, margin=margin)
        return VisibleTiles(grid, indices)

    def is_tile_on_screen(self, world_x: int, world_y: int) -> bool:
        """Check if a world tile is visible on screen."""
        grid = self._get_tile_grid()
        if grid is None:
            return False

        scene_x = world_x - grid.base_x
        scene_y = world_y - grid.base_y
        if not (0 <= scene_x < grid.size_x and 0 <= scene_y < grid.size_y):
            return False

        tile_idx = scene_x * grid.size_y + scene_y
        return bool(grid.tile_on_screen[tile_idx])

    def get_tile_quad(self, world_x: int, world_y: int) -> "Quad | None":
        """Get Quad for a world tile. Returns None if not in scene or not valid."""
        grid = self._get_tile_grid()
        if grid is None:
            return None

        scene_x = world_x - grid.base_x
        scene_y = world_y - grid.base_y
        if not (0 <= scene_x < grid.size_x and 0 <= scene_y < grid.size_y):
            return None

        tile_idx = scene_x * grid.size_y + scene_y
        if not grid.tile_valid[tile_idx]:
            return None

        return grid.get_tile_quad(tile_idx)

    def get_scene_bounds(self) -> tuple[int, int, int, int]:
        """Get world bounds: (minX, minY, maxX, maxY)."""
        grid = self._get_tile_grid()
        if grid is None:
            from escape.world.projection import projection

            return (
                projection.base_x,
                projection.base_y,
                projection.base_x + projection.size_x - 1,
                projection.base_y + projection.size_y - 1,
            )
        return (
            grid.base_x,
            grid.base_y,
            grid.base_x + grid.size_x - 1,
            grid.base_y + grid.size_y - 1,
        )

    def is_in_scene(self, world_x: int, world_y: int) -> bool:
        """Check if world coordinate is in loaded scene."""
        grid = self._get_tile_grid()
        if grid is None:
            return False
        scene_x = world_x - grid.base_x
        scene_y = world_y - grid.base_y
        return 0 <= scene_x < grid.size_x and 0 <= scene_y < grid.size_y


# Module-level instance
scene = Scene()
