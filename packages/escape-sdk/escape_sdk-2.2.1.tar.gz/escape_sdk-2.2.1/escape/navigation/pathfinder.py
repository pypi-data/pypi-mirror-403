"""Pathfinder for navigation."""

from ..types.packed_position import PackedPosition
from ..types.path import Path


class Pathfinder:
    """Pathfinder for calculating routes between locations."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self):
        """Actual initialization, runs once."""
        pass

    def get_path(
        self,
        destination_x: int,
        destination_y: int,
        destination_plane: int,
        use_transport: bool = True,
    ) -> Path | None:
        """Calculate path to destination."""
        from escape.client import client

        dest_packed = PackedPosition(destination_x, destination_y, destination_plane).packed

        result = client.api.invoke_custom_method(
            target="Pathfinder",
            method="getPathWithObstaclesPacked",
            signature="(I)[B",
            args=[dest_packed],
            async_exec=True,
        )

        if not result or "path" not in result:
            return None

        return Path.from_dict(result)

    def get_path_from_position(
        self,
        start_x: int,
        start_y: int,
        start_plane: int,
        destination_x: int,
        destination_y: int,
        destination_plane: int,
        use_transport: bool = True,
    ) -> Path | None:
        """Calculate path from specific start position to destination."""
        # For now, use the simpler method
        # TODO: Extend Java bridge to support custom start positions
        return self.get_path(destination_x, destination_y, destination_plane, use_transport)

    def can_reach(
        self,
        destination_x: int,
        destination_y: int,
        destination_plane: int,
        use_transport: bool = True,
    ) -> bool:
        """Check if destination is reachable."""
        path = self.get_path(destination_x, destination_y, destination_plane, use_transport)
        return path is not None and not path.is_empty()


# Module-level instance
pathfinder = Pathfinder()
