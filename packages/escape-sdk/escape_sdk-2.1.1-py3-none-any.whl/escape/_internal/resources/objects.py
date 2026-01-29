"""Game Objects accessor functions for OSRS object definitions and locations."""

import sqlite3
from typing import Any

from escape._internal.logger import logger
from escape.types.packed_position import pack_position_signed, unpack_position

__all__ = [
    "close",
    "count_locations",
    "count_objects",
    "execute_query",
    "get_by_id",
    "get_by_name",
    "get_locations",
    "get_nearby",
    "search_by_action",
    # Setter for cache_manager
    "set_db_connection",
]

# Module-level database connection (loaded by cache_manager at init)
_db_connection: sqlite3.Connection | None = None


def get_by_id(object_id: int) -> dict[str, Any] | None:
    """Get object definition by ID."""
    if _db_connection is None:
        logger.error("Objects database not loaded")
        return None

    cursor = _db_connection.cursor()
    cursor.execute(
        """
        SELECT DISTINCT o.object_id, n.name
        FROM objects o
        JOIN names n ON o.name_id = n.id
        WHERE o.object_id = ?
        LIMIT 1
    """,
        (object_id,),
    )

    row = cursor.fetchone()
    if row:
        return {"id": row[0], "name": row[1]}
    return None


def get_by_name(name: str, exact: bool = False) -> list[dict[str, Any]]:
    """Search for objects by name."""
    if _db_connection is None:
        logger.error("Objects database not loaded")
        return []

    cursor = _db_connection.cursor()
    if exact:
        cursor.execute(
            """
            SELECT DISTINCT o.object_id, n.name
            FROM objects o
            JOIN names n ON o.name_id = n.id
            WHERE n.name = ?
        """,
            (name,),
        )
    else:
        cursor.execute(
            """
            SELECT DISTINCT o.object_id, n.name
            FROM objects o
            JOIN names n ON o.name_id = n.id
            WHERE n.name LIKE ?
        """,
            (f"%{name}%",),
        )

    return [{"id": row[0], "name": row[1]} for row in cursor.fetchall()]


def get_locations(object_id: int) -> list[tuple[int, int, int]]:
    """Get all spawn locations for an object ID."""
    if _db_connection is None:
        logger.error("Objects database not loaded")
        return []

    cursor = _db_connection.cursor()
    cursor.execute("SELECT coord FROM objects WHERE object_id = ?", (object_id,))

    locations = []
    for row in cursor.fetchall():
        packed_pos = row[0]
        x, y, plane = unpack_position(packed_pos)
        locations.append((x, y, plane))

    return locations


def get_nearby(x: int, y: int, plane: int = 0, radius: int = 10) -> list[dict[str, Any]]:
    """Get all objects near a coordinate."""
    if _db_connection is None:
        logger.error("Objects database not loaded")
        return []

    # Calculate coordinate bounds
    min_x = max(0, x - radius)
    max_x = min(32767, x + radius)
    min_y = max(0, y - radius)
    max_y = min(32767, y + radius)

    # Build precise packed position ranges for each X coordinate
    # Since packed format is [plane(2)][x(15)][y(15)], for each X value
    # we can create exact BETWEEN ranges for all Y values in range
    # IMPORTANT: Use signed packing for SQLite compatibility (planes 2-3 become negative)
    ranges = []
    for curr_x in range(min_x, max_x + 1):
        min_packed = pack_position_signed(curr_x, min_y, plane)
        max_packed = pack_position_signed(curr_x, max_y, plane)
        ranges.append((min_packed, max_packed))

    # Build SQL query with OR'd BETWEEN clauses for precise filtering
    or_clauses = " OR ".join(["(o.coord BETWEEN ? AND ?)"] * len(ranges))

    query = f"""
        SELECT o.coord, o.object_id, n.name
        FROM objects o
        LEFT JOIN names n ON o.name_id = n.id
        WHERE {or_clauses}
    """

    # Flatten ranges for query parameters
    params = []
    for min_p, max_p in ranges:
        params.extend([min_p, max_p])

    cursor = _db_connection.cursor()
    cursor.execute(query, params)

    results = []
    for row in cursor.fetchall():
        packed_pos = row[0]
        obj_x, obj_y, obj_plane = unpack_position(packed_pos)

        # Calculate distance (all results should be within radius)
        dx = abs(obj_x - x)
        dy = abs(obj_y - y)

        results.append(
            {
                "object_id": row[1],
                "name": row[2],
                "x": obj_x,
                "y": obj_y,
                "plane": obj_plane,
                "distance": max(dx, dy),  # Chebyshev distance
            }
        )

    # Sort by distance
    results.sort(key=lambda obj: obj["distance"])

    return results


def search_by_action(action: str) -> list[dict[str, Any]]:
    """Find all objects with a specific action."""
    if _db_connection is None:
        logger.error("Objects database not loaded")
        return []

    cursor = _db_connection.cursor()

    # Get all unique objects with this action
    cursor.execute(
        """
        SELECT DISTINCT o.object_id, n.name
        FROM object_action_slots oas
        JOIN objects o ON oas.object_id = o.object_id
        LEFT JOIN names n ON o.name_id = n.id
        WHERE oas.action = ?
    """,
        (action,),
    )

    results = []
    for row in cursor.fetchall():
        object_id = row[0]
        name = row[1]

        # Get all actions for this object
        cursor.execute(
            """
            SELECT slot, action
            FROM object_action_slots
            WHERE object_id = ?
            ORDER BY slot
        """,
            (object_id,),
        )

        # Build actions array [slot0, slot1, slot2, slot3, slot4]
        actions = [None] * 5
        for action_row in cursor.fetchall():
            slot = action_row[0]
            action_text = action_row[1]
            if 0 <= slot <= 4:
                actions[slot] = action_text

        results.append({"id": object_id, "name": name, "actions": actions})

    return results


def count_objects() -> int:
    """Get total number of unique objects in database."""
    if _db_connection is None:
        logger.error("Objects database not loaded")
        return 0

    cursor = _db_connection.cursor()
    cursor.execute("SELECT COUNT(DISTINCT object_id) FROM objects")
    return cursor.fetchone()[0]


def count_locations() -> int:
    """Get total number of object spawn locations in database."""
    if _db_connection is None:
        logger.error("Objects database not loaded")
        return 0

    cursor = _db_connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM objects")
    return cursor.fetchone()[0]


def execute_query(query: str, params: tuple = ()) -> list[dict[str, Any]]:
    """Execute a custom SQL query on the objects database."""
    if _db_connection is None:
        logger.error("Objects database not loaded")
        return []

    cursor = _db_connection.cursor()
    cursor.execute(query, params)
    return [dict(row) for row in cursor.fetchall()]


def close():
    """Close database connection (called at shutdown)."""
    global _db_connection
    if _db_connection:
        _db_connection.close()
        _db_connection = None


def set_db_connection(conn: sqlite3.Connection) -> None:
    """Set the database connection (called by cache_manager during initialization)."""
    global _db_connection
    _db_connection = conn
    _db_connection.row_factory = sqlite3.Row
