"""Projection utilities for converting local coordinates to screen coordinates."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

from escape.types.point import Point

if TYPE_CHECKING:
    from escape.types import Quad


@dataclass
class CameraState:
    """Per-frame camera state."""

    camera_x: float
    camera_y: float
    camera_z: float
    camera_pitch: float  # radians
    camera_yaw: float  # radians
    scale: int


@dataclass
class EntityTransform:
    """Per-frame entity transform data (for WorldEntity instances)."""

    entity_x: int
    entity_y: int
    orientation: int  # 0-2047 JAU
    ground_height: int


@dataclass
class EntityConfig:
    """Static WorldEntity config - set once on WorldView load."""

    bounds_x: int
    bounds_y: int
    bounds_width: int
    bounds_height: int

    @property
    def center_x(self) -> int:
        return (self.bounds_x + self.bounds_width // 2) * 128

    @property
    def center_y(self) -> int:
        return (self.bounds_y + self.bounds_height // 2) * 128


class TileGrid:
    """Cached projection of all tile corners in the scene."""

    __slots__ = (
        "_scene_xs",
        "_scene_ys",
        "_tile_on_screen",
        "_tile_valid",
        "base_x",
        "base_y",
        "corner_valid",
        "corner_x",
        "corner_y",
        "plane",
        "size_x",
        "size_y",
        "view_max_x",
        "view_max_y",
        "view_min_x",
        "view_min_y",
    )

    def __init__(
        self,
        corner_x: np.ndarray,
        corner_y: np.ndarray,
        corner_valid: np.ndarray,
        size_x: int,
        size_y: int,
        base_x: int,
        base_y: int,
        plane: int,
        view_min_x: int,
        view_max_x: int,
        view_min_y: int,
        view_max_y: int,
    ):
        self.corner_x = corner_x  # int32[(size_x+1)*(size_y+1)]
        self.corner_y = corner_y  # int32[(size_x+1)*(size_y+1)]
        self.corner_valid = corner_valid  # bool[(size_x+1)*(size_y+1)]
        self.size_x = size_x
        self.size_y = size_y
        self.base_x = base_x
        self.base_y = base_y
        self.plane = plane
        self.view_min_x = view_min_x
        self.view_max_x = view_max_x
        self.view_min_y = view_min_y
        self.view_max_y = view_max_y

        # Pre-compute tile scene coordinates (used for filtering)
        tile_count = size_x * size_y
        self._scene_xs = (np.arange(tile_count, dtype=np.int32) // size_y).astype(np.int16)
        self._scene_ys = (np.arange(tile_count, dtype=np.int32) % size_y).astype(np.int16)

        # Pre-compute tile validity and visibility (lazy, computed on first access)
        self._tile_valid: np.ndarray | None = None
        self._tile_on_screen: np.ndarray | None = None

    def _corner_idx(self, x: int, y: int) -> int:
        """Get flat index for corner at (x, y)."""
        return x * (self.size_y + 1) + y

    def _tile_idx(self, x: int, y: int) -> int:
        """Get flat index for tile at (x, y)."""
        return x * self.size_y + y

    @property
    def tile_valid(self) -> np.ndarray:
        """Bool array of tile validity (all 4 corners valid). Shape: [size_x * size_y]."""
        if self._tile_valid is None:
            sy1 = self.size_y + 1
            # Get corner indices for all tiles
            tile_idxs = np.arange(self.size_x * self.size_y, dtype=np.int32)
            tx = tile_idxs // self.size_y
            ty = tile_idxs % self.size_y
            # Corner indices: NW, NE, SE, SW
            nw = tx * sy1 + ty
            ne = (tx + 1) * sy1 + ty
            se = (tx + 1) * sy1 + (ty + 1)
            sw = tx * sy1 + (ty + 1)
            self._tile_valid = (
                self.corner_valid[nw]
                & self.corner_valid[ne]
                & self.corner_valid[se]
                & self.corner_valid[sw]
            )
        return self._tile_valid

    @property
    def tile_on_screen(self) -> np.ndarray:
        """Bool array of tiles with center on screen. Shape: [size_x * size_y]."""
        if self._tile_on_screen is None:
            # Compute tile centers from corners
            center_x, center_y = self.get_tile_centers()
            self._tile_on_screen = (
                self.tile_valid
                & (center_x >= self.view_min_x)
                & (center_x < self.view_max_x)
                & (center_y >= self.view_min_y)
                & (center_y < self.view_max_y)
            )
        return self._tile_on_screen

    def get_tile_centers(self) -> tuple[np.ndarray, np.ndarray]:
        """Get screen coordinates of tile centers. Returns (center_x, center_y) arrays."""
        sy1 = self.size_y + 1
        tile_idxs = np.arange(self.size_x * self.size_y, dtype=np.int32)
        tx = tile_idxs // self.size_y
        ty = tile_idxs % self.size_y
        nw = tx * sy1 + ty
        ne = (tx + 1) * sy1 + ty
        se = (tx + 1) * sy1 + (ty + 1)
        sw = tx * sy1 + (ty + 1)
        center_x = (
            self.corner_x[nw] + self.corner_x[ne] + self.corner_x[se] + self.corner_x[sw]
        ) >> 2
        center_y = (
            self.corner_y[nw] + self.corner_y[ne] + self.corner_y[se] + self.corner_y[sw]
        ) >> 2
        return center_x, center_y

    def get_tile_corners(self, tile_idx: int) -> tuple[int, int, int, int, int, int, int, int]:
        """Get screen coords of tile corners: (nw_x, nw_y, ne_x, ne_y, se_x, se_y, sw_x, sw_y)."""
        tx = tile_idx // self.size_y
        ty = tile_idx % self.size_y
        sy1 = self.size_y + 1
        nw = tx * sy1 + ty
        ne = (tx + 1) * sy1 + ty
        se = (tx + 1) * sy1 + (ty + 1)
        sw = tx * sy1 + (ty + 1)
        return (
            int(self.corner_x[nw]),
            int(self.corner_y[nw]),
            int(self.corner_x[ne]),
            int(self.corner_y[ne]),
            int(self.corner_x[se]),
            int(self.corner_y[se]),
            int(self.corner_x[sw]),
            int(self.corner_y[sw]),
        )

    def get_tile_quad(self, tile_idx: int) -> "Quad":
        """Get Quad for tile at flat index."""
        from escape.types import Quad

        nw_x, nw_y, ne_x, ne_y, se_x, se_y, sw_x, sw_y = self.get_tile_corners(tile_idx)
        return Quad.from_coords([(nw_x, nw_y), (ne_x, ne_y), (se_x, se_y), (sw_x, sw_y)])

    def get_visible_indices(self, mask: np.ndarray | None = None, margin: int = 0) -> np.ndarray:
        """Get flat indices of visible tiles, optionally filtered by mask."""
        if margin == 0:
            visible = self.tile_on_screen
        else:
            center_x, center_y = self.get_tile_centers()
            visible = (
                self.tile_valid
                & (center_x >= self.view_min_x - margin)
                & (center_x < self.view_max_x + margin)
                & (center_y >= self.view_min_y - margin)
                & (center_y < self.view_max_y + margin)
            )

        if mask is not None:
            visible = visible & mask

        return np.where(visible)[0]


class Projection:
    """Fast projection from local coordinates to canvas coordinates."""

    LOCAL_COORD_BITS = 7
    LOCAL_TILE_SIZE = 128

    VIEWPORT_WIDTH = 512
    VIEWPORT_HEIGHT = 334
    VIEWPORT_X_OFFSET = 4
    VIEWPORT_Y_OFFSET = 4

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self):
        # Sin/cos lookup tables (JAU: 0-2047)
        unit = np.pi / 1024
        angles = np.arange(2048) * unit
        self._sin_table = np.sin(angles).astype(np.float32)
        self._cos_table = np.cos(angles).astype(np.float32)

        # Scene data
        self.tile_heights: np.ndarray | None = None
        self.bridge_flags: np.ndarray | None = None
        self.base_x: int = 0
        self.base_y: int = 0
        self.size_x: int = 104
        self.size_y: int = 104
        self.entity_config: EntityConfig | None = None

        # Camera trig (updated on refresh)
        self._cam_x: float = 0
        self._cam_y: float = 0
        self._cam_z: float = 0
        self._scale: int = 512
        self._pitch_sin: float = 0
        self._pitch_cos: float = 1
        self._yaw_sin: float = 0
        self._yaw_cos: float = 1

        # Entity transform
        self._entity_x: int = 0
        self._entity_y: int = 0
        self._orient_sin: float = 0
        self._orient_cos: float = 1
        self._ground_height: int = 0
        self._center_x: int = 0
        self._center_y: int = 0

        # Tile cache
        self._tile_grid: TileGrid | None = None
        self._stale: bool = True

    def invalidate(self):
        """Mark cache as stale. Called by StateBuilder on relevant events."""
        self._stale = True

    @property
    def tiles(self) -> TileGrid | None:
        """Get cached tile projections, recomputing if stale."""
        if not self._stale and self._tile_grid is not None:
            return self._tile_grid

        if not self._refresh_camera():
            return None

        if self.tile_heights is None:
            return None

        self._compute_tile_grid()
        return self._tile_grid

    def _refresh_camera(self) -> bool:
        """Load camera state from EventCache. Returns True if successful."""
        from escape.globals import get_event_cache

        cache = get_event_cache()
        cam_data = cache.get_camera_state()
        if not cam_data:
            return False

        self._cam_x, self._cam_y, self._cam_z = cam_data[0], cam_data[1], cam_data[2]
        pitch, yaw, self._scale = cam_data[3], cam_data[4], cam_data[5]
        self._pitch_sin = np.sin(pitch)
        self._pitch_cos = np.cos(pitch)
        self._yaw_sin = np.sin(yaw)
        self._yaw_cos = np.cos(yaw)

        # Entity transform
        ent_data = cache.get_entity_transform()
        if ent_data:
            self._entity_x, self._entity_y = ent_data[0], ent_data[1]
            self._orient_sin = self._sin_table[ent_data[2]]
            self._orient_cos = self._cos_table[ent_data[2]]
            self._ground_height = ent_data[3]
        else:
            self._entity_x = self._entity_y = self._ground_height = 0
            self._orient_sin, self._orient_cos = 0.0, 1.0

        return True

    def _compute_tile_grid(self):
        """Compute corner projections for all tiles."""
        # Get current plane
        from escape.globals import get_event_cache

        gametick = get_event_cache().get_gametick_state()
        plane = gametick.get("plane", 0) if gametick else 0

        # Generate corner grid: (size_x+1) x (size_y+1)
        cx = np.arange(self.size_x + 1, dtype=np.int32)
        cy = np.arange(self.size_y + 1, dtype=np.int32)
        grid_x, grid_y = np.meshgrid(cx, cy, indexing="ij")

        # Local coords for corners (not +64 for centers)
        local_x = (grid_x << 7).ravel().astype(np.float32)
        local_y = (grid_y << 7).ravel().astype(np.float32)

        # Project
        screen_x, screen_y, valid = self._project_batch(local_x, local_y, plane)

        self._tile_grid = TileGrid(
            corner_x=screen_x.astype(np.int32),
            corner_y=screen_y.astype(np.int32),
            corner_valid=valid,
            size_x=self.size_x,
            size_y=self.size_y,
            base_x=self.base_x,
            base_y=self.base_y,
            plane=plane,
            view_min_x=self.VIEWPORT_X_OFFSET,
            view_max_x=self.VIEWPORT_X_OFFSET + self.VIEWPORT_WIDTH,
            view_min_y=self.VIEWPORT_Y_OFFSET,
            view_max_y=self.VIEWPORT_Y_OFFSET + self.VIEWPORT_HEIGHT,
        )
        self._stale = False

    def _project_batch(
        self, local_x: np.ndarray, local_y: np.ndarray, plane: int
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Core projection: local coords -> screen coords."""
        if self.bridge_flags is None or self.tile_heights is None:
            raise RuntimeError("Projection scene data not initialized")

        # Tile heights with bridge correction
        scene_x = (local_x.astype(np.int32) >> 7).clip(0, self.size_x - 1)
        scene_y = (local_y.astype(np.int32) >> 7).clip(0, self.size_y - 1)
        tile_plane = np.where((plane < 3) & self.bridge_flags[scene_x, scene_y], plane + 1, plane)
        z = self.tile_heights[tile_plane, scene_x, scene_y].astype(np.float32) + self._ground_height

        # Entity transform (identity if top-level)
        if self.entity_config is None:
            world_x, world_y = local_x, local_y
        else:
            cx = local_x - self._center_x
            cy = local_y - self._center_y
            world_x = self._entity_x + cy * self._orient_sin + cx * self._orient_cos
            world_y = self._entity_y + cy * self._orient_cos - cx * self._orient_sin

        # Camera-relative
        dx = world_x - self._cam_x
        dy = world_y - self._cam_y
        dz = z - self._cam_z

        # Rotate by yaw and pitch
        x1 = dx * self._yaw_cos + dy * self._yaw_sin
        y1 = dy * self._yaw_cos - dx * self._yaw_sin
        y2 = dz * self._pitch_cos - y1 * self._pitch_sin
        depth = y1 * self._pitch_cos + dz * self._pitch_sin

        # Project
        valid = depth >= 50
        safe_depth = np.where(valid, depth, 1.0)
        screen_x = (self.VIEWPORT_WIDTH / 2 + x1 * self._scale / safe_depth).astype(np.int32)
        screen_y = (self.VIEWPORT_HEIGHT / 2 + y2 * self._scale / safe_depth).astype(np.int32)
        screen_x += self.VIEWPORT_X_OFFSET
        screen_y += self.VIEWPORT_Y_OFFSET

        return screen_x, screen_y, valid

    def set_scene(
        self,
        tile_heights: np.ndarray,
        bridge_flags: np.ndarray,
        base_x: int,
        base_y: int,
        size_x: int,
        size_y: int,
    ):
        """Set scene data on WorldView load."""
        self.tile_heights = tile_heights.astype(np.int32)
        self.bridge_flags = bridge_flags.astype(np.bool_)
        self.base_x = base_x
        self.base_y = base_y
        self.size_x = size_x
        self.size_y = size_y

    def set_entity_config(self, config: EntityConfig | None):
        """Set WorldEntity config. None for top-level world."""
        self.entity_config = config
        if config:
            self._center_x = config.center_x
            self._center_y = config.center_y
        else:
            self._center_x = self._center_y = 0

    def world_tile_to_canvas(self, world_x: int, world_y: int, plane: int) -> Point | None:
        """Project a world tile center to screen. Returns None if off-scene or behind camera."""
        grid = self.tiles
        if grid is None or grid.plane != plane:
            return None

        scene_x = world_x - self.base_x
        scene_y = world_y - self.base_y
        if not (0 <= scene_x < self.size_x and 0 <= scene_y < self.size_y):
            return None

        tile_idx = scene_x * self.size_y + scene_y
        if not grid.tile_valid[tile_idx]:
            return None

        center_x, center_y = grid.get_tile_centers()
        return Point(int(center_x[tile_idx]), int(center_y[tile_idx]))


# Module-level instance
projection = Projection()
