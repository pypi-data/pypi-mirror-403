"""OSRS ground item handling using event cache."""

from typing import ClassVar, Self

from ..types.ground_item import GroundItem
from ..types.ground_item_list import GroundItemList
from ..types.packed_position import PackedPosition


class GroundItems:
    """Ground items accessor from event cache."""

    _instance: ClassVar[Self | None] = None
    _cached_list: GroundItemList
    _cached_tick: int

    def __new__(cls) -> Self:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._cached_list = GroundItemList([])
            cls._instance._cached_tick = -1
        return cls._instance

    def get_all_items(self) -> GroundItemList:
        """Get all ground items from cache."""
        from escape.client import client

        current_tick = client.cache.tick

        # Return cached if same tick
        if self._cached_tick == current_tick and self._cached_list.count() > 0:
            return self._cached_list

        # Refresh cache
        ground_items_dict = client.cache.get_ground_items()
        result = []

        for packed_coord, items_list in ground_items_dict.items():
            position = PackedPosition.from_packed(packed_coord)
            for item_data in items_list:
                result.append(GroundItem(data=item_data, position=position, client=client))

        self._cached_list = GroundItemList(result)
        if current_tick is not None:
            self._cached_tick = current_tick

        return self._cached_list


# Module-level instance
ground_items = GroundItems()
