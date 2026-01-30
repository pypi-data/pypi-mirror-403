"""GroundItemList type with fluent filtering."""

from collections.abc import Callable

from .ground_item import GroundItem
from .item import ItemIdentifier
from .packed_position import PackedPosition


class GroundItemList:
    """List of ground items with fluent filtering methods."""

    def __init__(self, items: list[GroundItem]):
        """Initialize ground item list."""
        self._items = items

    def filter(self, predicate: Callable[[GroundItem], bool]) -> "GroundItemList":
        """Filter items by custom predicate."""
        return GroundItemList([item for item in self._items if predicate(item)])

    def filter_by_item(self, identifier: ItemIdentifier) -> "GroundItemList":
        """Filter by item ID or name."""
        if isinstance(identifier, int):
            return GroundItemList([item for item in self._items if item.id == identifier])
        return GroundItemList(
            [item for item in self._items if identifier.lower() in item.name.lower()]
        )

    def filter_by_ownership(self, ownership: int) -> "GroundItemList":
        """Filter by ownership type."""
        return GroundItemList([item for item in self._items if item.ownership == ownership])

    def filter_yours(self) -> "GroundItemList":
        """Filter to only your items (ownership 1 or 3)."""
        return GroundItemList([item for item in self._items if item.is_yours])

    def filter_lootable(self) -> "GroundItemList":
        """Filter to only lootable items (yours or public)."""
        return GroundItemList([item for item in self._items if item.can_loot])

    def filter_by_position(self, x: int, y: int, plane: int) -> "GroundItemList":
        """Filter to items at specific position."""
        target = PackedPosition(x, y, plane)
        return GroundItemList([item for item in self._items if item.position == target])

    def filter_nearby(self, x: int, y: int, plane: int, radius: int) -> "GroundItemList":
        """Filter to items within radius of position."""
        center = PackedPosition(x, y, plane)
        return GroundItemList(
            [
                item
                for item in self._items
                if item.position.is_nearby(center, radius, same_plane=True)
            ]
        )

    def sort_by_distance(self, x: int, y: int, plane: int) -> "GroundItemList":
        """Sort items by distance from position (closest first)."""
        center = PackedPosition(x, y, plane)
        sorted_items = sorted(self._items, key=lambda item: item.position.distance_to(center))
        return GroundItemList(sorted_items)

    def sort_by_quantity(self, reverse: bool = True) -> "GroundItemList":
        """Sort items by quantity."""
        sorted_items = sorted(self._items, key=lambda item: item.quantity, reverse=reverse)
        return GroundItemList(sorted_items)

    def first(self) -> GroundItem | None:
        """Get first item in list."""
        return self._items[0] if self._items else None

    def last(self) -> GroundItem | None:
        """Get last item in list."""
        return self._items[-1] if self._items else None

    def is_empty(self) -> bool:
        """Check if list is empty."""
        return len(self._items) == 0

    def count(self) -> int:
        """Get number of items in list."""
        return len(self._items)

    def to_list(self) -> list[GroundItem]:
        """Convert to regular Python list."""
        return self._items.copy()

    def __len__(self) -> int:
        """Support len() builtin."""
        return len(self._items)

    def __iter__(self):
        """Support iteration."""
        return iter(self._items)

    def __getitem__(self, index):
        """Support indexing."""
        return self._items[index]

    def __repr__(self) -> str:
        return f"GroundItemList({len(self._items)} items)"
