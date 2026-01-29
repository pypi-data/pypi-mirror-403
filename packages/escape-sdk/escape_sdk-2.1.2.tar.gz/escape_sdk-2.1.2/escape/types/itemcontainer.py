"""ItemContainer type for representing item containers like inventory, bank, equipment."""

from typing import Any

from escape.globals import get_client
from escape.types.item import Item, ItemIdentifier


class ItemContainer:
    """Base class for OSRS item containers (inventory, bank, equipment, etc.)."""

    def __init__(
        self,
        container_id: int = -1,
        slot_count: int = -1,
        items: list[Item | None] | None = None,
    ):
        """Initialize item container."""
        self.container_id = container_id
        self.slot_count = slot_count
        self.items = items if items is not None else []

    def from_array(self, data: list[dict[str, Any]]):
        """Populate ItemContainer from array of item dicts."""
        parsed_items = [
            Item.from_dict(item_data) if item_data is not None else None for item_data in data
        ]

        self.items = parsed_items

    def populate(self):
        client = get_client()

        result = client.api.invoke_custom_method(
            target="EventBusListener",
            method="getItemContainerPacked",
            signature="(I)[B",
            args=[self.container_id],
            async_exec=False,
        )

        if result:
            self.from_array(result)

    def to_dict(self) -> dict[str, Any]:
        """Convert ItemContainer back to dict format."""
        return {
            "containerId": self.container_id,
            "slotCount": self.slot_count,
            "items": [item.to_dict() if item is not None else None for item in self.items],
        }

    def get_total_count(self) -> int:
        """Get count of non-empty slots."""
        return sum(1 for item in self.items if item is not None)

    def get_total_quantity(self) -> int:
        """Get total quantity of all items (sum of stacks)."""
        return sum(item.quantity for item in self.items if item is not None)

    def get_item_count(self, identifier: ItemIdentifier) -> int:
        """Get count of items matching the given ID or name."""
        if isinstance(identifier, int):
            return sum(1 for item in self.items if item is not None and item.id == identifier)
        return sum(1 for item in self.items if item is not None and identifier in item.name)

    def get_items(self, identifier: ItemIdentifier) -> list[Item]:
        """Get all items matching the given ID or name."""
        if isinstance(identifier, int):
            return [item for item in self.items if item is not None and item.id == identifier]
        return [item for item in self.items if item is not None and identifier in item.name]

    def get_slot(self, slot_index: int) -> Item | None:
        """Get item at specific slot index."""
        if 0 <= slot_index < len(self.items):
            return self.items[slot_index]
        return None

    def get_slots(self, slots: list[int]) -> list[Item | None]:
        """Get items at specific slot indices."""
        result = []
        for slot_index in slots:
            if 0 <= slot_index < len(self.items):
                result.append(self.items[slot_index])
            else:
                result.append(None)
        return result

    def find_item_slot(self, identifier: ItemIdentifier) -> int | None:
        """Find the first slot index containing an item matching the ID or name."""
        if isinstance(identifier, int):
            for index, item in enumerate(self.items):
                if item is not None and item.id == identifier:
                    return index
        else:
            for index, item in enumerate(self.items):
                if item is not None and identifier in item.name:
                    return index
        return None

    def find_item_slots(self, identifier: ItemIdentifier) -> list[int]:
        """Find all slot indices containing items matching the ID or name."""
        slots = []
        if isinstance(identifier, int):
            for index, item in enumerate(self.items):
                if item is not None and item.id == identifier:
                    slots.append(index)
        else:
            for index, item in enumerate(self.items):
                if item is not None and identifier in item.name:
                    slots.append(index)
        return slots

    def contains_item(self, identifier: ItemIdentifier) -> bool:
        """Check if container contains an item matching the ID or name."""
        if isinstance(identifier, int):
            return any(item is not None and item.id == identifier for item in self.items)
        return any(item is not None and identifier in item.name for item in self.items)

    def contains_all_items(self, identifiers: list[ItemIdentifier]) -> bool:
        """Check if container contains all items matching the given IDs or names."""
        return all(self.contains_item(identifier) for identifier in identifiers)

    def get_item_quantity(self, identifier: ItemIdentifier) -> int:
        """Get total quantity of items matching the given ID or name."""
        if isinstance(identifier, int):
            return sum(
                item.quantity for item in self.items if item is not None and item.id == identifier
            )
        return sum(
            item.quantity for item in self.items if item is not None and identifier in item.name
        )

    def is_empty(self) -> bool:
        """Check if container has no items."""
        return all(item is None for item in self.items)

    def is_full(self) -> bool:
        """Check if container is full."""
        if self.slot_count > 0:
            return self.get_total_count() >= self.slot_count
        return all(item is not None for item in self.items)

    def __repr__(self) -> str:
        """Return string representation."""
        return f"ItemContainer(id={self.container_id}, items={self.to_dict()})"

    def __eq__(self, other) -> bool:
        """Check equality with another ItemContainer."""
        if not isinstance(other, ItemContainer):
            return False
        return (
            self.container_id == other.container_id
            and self.slot_count == other.slot_count
            and self.items == other.items
        )

    def clear(self) -> None:
        """Clear all items from the container."""
        self.items = []
