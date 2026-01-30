"""Item type for representing game items."""

from dataclasses import dataclass
from typing import Any

# Type alias for item identification - can be ID (int) or name (str)
ItemIdentifier = int | str


@dataclass
class Item:
    """Represents an OSRS item."""

    id: int
    name: str
    quantity: int
    noted: bool

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Item":
        """Convert dict from Java to Item instance."""
        return cls(
            id=data.get("id", -1),
            name=data.get("name", "Unknown"),
            quantity=data.get("stack", 1),
            noted=data.get("noted", False),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert Item back to dict format."""
        return {"id": self.id, "name": self.name, "stack": self.quantity, "noted": self.noted}

    def __repr__(self) -> str:
        """Return string representation."""
        noted_str = " (noted)" if self.noted else ""
        return f"Item({self.id}, '{self.name}' x{self.quantity}{noted_str})"

    def matches(self, identifier: ItemIdentifier) -> bool:
        """Check if this item matches the given identifier."""
        if isinstance(identifier, int):
            return self.id == identifier
        return identifier in self.name
