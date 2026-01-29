"""Player state middleware."""

from typing import Any, ClassVar, Self


class Player:
    """Player state accessor for position, energy, and game tick."""

    _instance: ClassVar[Self | None] = None
    _cached_state: dict[str, Any]
    _cached_tick: int

    def __new__(cls) -> Self:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._cached_state = {}
            cls._instance._cached_tick = -1
        return cls._instance

    def _get_state(self) -> dict[str, Any]:
        """Get cached player state (refreshed per tick)."""
        from escape.client import client

        current_tick = client.cache.tick

        # Return cached if same tick
        if self._cached_tick == current_tick and self._cached_state:
            return self._cached_state

        # Refresh from cache
        position = client.cache.position
        if position is not None:
            self._cached_state = position.copy()
        if current_tick is not None:
            self._cached_tick = current_tick

        return self._cached_state

    @property
    def position(self) -> dict[str, int]:
        """Get player position."""
        return self._get_state()

    @property
    def x(self) -> int:
        """Get player X coordinate."""
        return self._get_state().get("x", 0)

    @property
    def y(self) -> int:
        """Get player Y coordinate."""
        return self._get_state().get("y", 0)

    @property
    def plane(self) -> int:
        """Get player plane level."""
        return self._get_state().get("plane", 0)

    @property
    def energy(self) -> int:
        """Get run energy (0-10000)."""
        from escape.client import client

        return client.cache.energy or 0

    @property
    def tick(self) -> int:
        """Get current game tick."""
        from escape.client import client

        return client.cache.tick or 0

    def distance_to(self, x: int, y: int) -> int:
        """Calculate distance from player to coordinates."""
        dx = abs(self.x - x)
        dy = abs(self.y - y)
        return max(dx, dy)

    def is_at(self, x: int, y: int, plane: int | None = None) -> bool:
        """Check if player is at specific coordinates."""
        if self.x != x or self.y != y:
            return False

        return not (plane is not None and self.plane != plane)

    def is_nearby(self, x: int, y: int, radius: int, plane: int | None = None) -> bool:
        """Check if player is within radius of coordinates."""
        if plane is not None and self.plane != plane:
            return False

        return self.distance_to(x, y) <= radius


# Module-level instance
player = Player()
