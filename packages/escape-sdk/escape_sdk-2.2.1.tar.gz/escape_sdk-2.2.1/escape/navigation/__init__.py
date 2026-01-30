"""Navigation module."""

from escape.navigation.pathfinder import Pathfinder, pathfinder
from escape.navigation.walker import Walker, walker


class Navigation:
    """Pathfinding and walking to destinations."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def pathfinder(self) -> Pathfinder:
        """Pathfinder for calculating routes."""
        return pathfinder

    @property
    def walker(self) -> Walker:
        """Walker for moving the player."""
        return walker


# Module-level instance
navigation = Navigation()


__all__ = ["Navigation", "Pathfinder", "Walker", "navigation", "pathfinder", "walker"]
