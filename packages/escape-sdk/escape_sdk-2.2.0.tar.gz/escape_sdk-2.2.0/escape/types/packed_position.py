"""PackedPosition type for efficient OSRS coordinate storage."""


class PackedPosition:
    """Efficient packed position representation for OSRS coordinates."""

    __slots__ = ("_packed",)

    def __init__(self, x: int = 0, y: int = 0, plane: int = 0):
        """Create a packed position."""
        if not (0 <= x <= 32767):
            raise ValueError(f"X out of range: {x} (must be 0-32767)")
        if not (0 <= y <= 32767):
            raise ValueError(f"Y out of range: {y} (must be 0-32767)")
        if not (0 <= plane <= 3):
            raise ValueError(f"Plane out of range: {plane} (must be 0-3)")

        self._packed = (x & 0x7FFF) | ((y & 0x7FFF) << 15) | ((plane & 0x3) << 30)

    @classmethod
    def from_packed(cls, packed: int) -> "PackedPosition":
        """Create from a packed integer."""
        pos = cls.__new__(cls)
        pos._packed = packed
        return pos

    @property
    def x(self) -> int:
        """Get X coordinate (bits 0-14)."""
        return self._packed & 0x7FFF

    @property
    def y(self) -> int:
        """Get Y coordinate (bits 15-29)."""
        return (self._packed >> 15) & 0x7FFF

    @property
    def plane(self) -> int:
        """Get plane level."""
        return (self._packed >> 30) & 0x3

    @property
    def packed(self) -> int:
        """Get packed integer representation."""
        return self._packed

    def unpack(self) -> tuple[int, int, int]:
        """Unpack to (x, y, plane) tuple."""
        return (self.x, self.y, self.plane)

    def distance_to(self, other: "PackedPosition") -> int:
        """Calculate Chebyshev distance to another position."""
        dx = abs(self.x - other.x)
        dy = abs(self.y - other.y)
        return max(dx, dy)

    def is_nearby(self, other: "PackedPosition", radius: int, same_plane: bool = True) -> bool:
        """Check if position is within radius of another."""
        if same_plane and self.plane != other.plane:
            return False

        return self.distance_to(other) <= radius

    def __eq__(self, other) -> bool:
        if isinstance(other, PackedPosition):
            return self._packed == other._packed
        return False

    def __hash__(self) -> int:
        return self._packed

    def __repr__(self) -> str:
        return f"PackedPosition(x={self.x}, y={self.y}, plane={self.plane})"

    def __str__(self) -> str:
        return f"({self.x}, {self.y}, {self.plane})"


def pack_position(x: int, y: int, plane: int) -> int:
    """Pack (x, y, plane) into a 32-bit unsigned integer."""
    return (x & 0x7FFF) | ((y & 0x7FFF) << 15) | ((plane & 0x3) << 30)


def pack_position_signed(x: int, y: int, plane: int) -> int:
    """Pack (x, y, plane) into a 32-bit signed integer for SQLite compatibility."""
    packed = pack_position(x, y, plane)
    # Convert to signed 32-bit
    if packed >= 2**31:
        return packed - 2**32
    return packed


def unpack_position(packed: int) -> tuple[int, int, int]:
    """Unpack a 32-bit integer into (x, y, plane)."""
    # Convert signed to unsigned for bit operations
    if packed < 0:
        packed = packed + 2**32

    x = packed & 0x7FFF  # 15 bits (0-14)
    y = (packed >> 15) & 0x7FFF  # 15 bits (15-29)
    plane = (packed >> 30) & 0x3  # 2 bits (30-31)

    return (x, y, plane)
