"""
OSRS Game Resources System

Provides access to game data (varps, varbits, objects) loaded at initialization.
Data is downloaded and loaded once per session by cache_manager.ensureResourcesLoaded().

Example:
    from escape._internal.resources import varps, objects

    # Varps/varbits
    quest_points = varps.get_varp_by_name("quest_points")
    varbit_value = varps.get_varbit_by_index(5087)

    # Objects
    tree = objects.getById(1276)
    nearby = objects.getNearby(3222, 3218, 0, radius=10)
"""

from escape._internal.resources import objects as objects
from escape._internal.resources import varps as varps

__all__ = [
    "objects",
    "varps",
]
