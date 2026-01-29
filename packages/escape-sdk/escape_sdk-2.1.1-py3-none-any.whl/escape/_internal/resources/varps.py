"""Varps and Varbits accessor functions."""

from typing import Any

from escape._internal.logger import logger

__all__ = [
    "extract_bits",
    "get_varbit_by_index",
    "get_varbit_by_name",
    "get_varbit_info",
    "get_varbits_data_count",
    "get_varc_name",
    "get_varc_value",
    "get_varp_by_index",
    "get_varp_by_name",
    "get_varps_data_count",
    "list_varbits",
    "list_varps",
    "set_varbits_data",
    "set_varps_data",
]

# Module-level data (loaded by cache_manager at init)
_varps_data: dict[int, dict[str, Any]] | None = None
_varbits_data: dict[int, dict[str, Any]] | None = None


def _get_varp_value(varp_id: int) -> int | None:
    """Get the current value of a varp from the event cache."""
    try:
        from escape.globals import get_client

        client = get_client()
        if hasattr(client, "event_cache"):
            return client.event_cache.get_varp(varp_id)
        return None
    except Exception:
        return None


def extract_bits(value: int, start_bit: int, end_bit: int) -> int:
    """Extract bits from a varp value."""
    num_bits = end_bit - start_bit + 1
    mask = (1 << num_bits) - 1
    return (value >> start_bit) & mask


def get_varbit_info(varbit_id: int) -> dict[str, Any] | None:
    """Get metadata about a varbit (which varp it belongs to, bit positions)."""
    if not _varbits_data:
        return None

    varbit_info = _varbits_data.get(varbit_id)
    if not varbit_info:
        return None

    return {
        "varp": varbit_info.get("varp"),
        "lsb": varbit_info.get("lsb", 0),
        "msb": varbit_info.get("msb", 31),
        "name": varbit_info.get("name", f"varbit_{varbit_id}"),
    }


def get_varp_by_name(name: str) -> int | None:
    """Get a varp value by name."""
    if not _varps_data:
        logger.error("Varps data not loaded")
        return None

    # Search for varp by name
    for varp_id, varp_info in _varps_data.items():
        if isinstance(varp_info, dict) and varp_info.get("name") == name:
            return _get_varp_value(int(varp_id))

    logger.error(f"Varp '{name}' not found")
    return None


def get_varp_by_index(varp_id: int) -> int | None:
    """Get a varp value by its index."""
    return _get_varp_value(varp_id)


def get_varbit_by_index(varbit_id: int) -> int | None:
    """Get a varbit value by its index."""
    if not _varbits_data:
        logger.error("Varbits data not loaded")
        return None

    # Get varbit info
    varbit_info = _varbits_data.get(varbit_id)
    if not varbit_info:
        logger.error(f"Varbit {varbit_id} not found")
        return None

    # Get the varp value
    varp_id = varbit_info.get("varp")
    if varp_id is None:
        logger.error(f"Varbit {varbit_id} has no varp mapping")
        return None

    varp_value = _get_varp_value(varp_id)
    if varp_value is None:
        return None

    # Extract the bits
    start_bit = varbit_info.get("lsb", 0)
    end_bit = varbit_info.get("msb", 31)

    return extract_bits(varp_value, start_bit, end_bit)


def get_varbit_by_name(name: str) -> int | None:
    """Get a varbit value by name."""
    if not _varbits_data:
        logger.error("Varbits data not loaded")
        return None

    # Search for varbit by name
    for varbit_id, varbit_info in _varbits_data.items():
        if isinstance(varbit_info, dict) and varbit_info.get("name") == name:
            return get_varbit_by_index(int(varbit_id))

    logger.error(f"Varbit '{name}' not found")
    return None


def list_varps(filter_name: str | None = None) -> dict[int, dict[str, Any]]:
    """List all available varps, optionally filtered by name."""
    if not _varps_data:
        return {}

    if filter_name:
        return {
            int(k): v
            for k, v in _varps_data.items()
            if isinstance(v, dict) and filter_name.lower() in v.get("name", "").lower()
        }

    return {int(k): v for k, v in _varps_data.items()}


def list_varbits(filter_name: str | None = None) -> dict[int, dict[str, Any]]:
    """List all available varbits, optionally filtered by name."""
    if not _varbits_data:
        return {}

    if filter_name:
        return {
            int(k): v
            for k, v in _varbits_data.items()
            if isinstance(v, dict) and filter_name.lower() in v.get("name", "").lower()
        }

    return {int(k): v for k, v in _varbits_data.items()}


def get_varc_value(varc_id: int) -> Any | None:
    """Get the current value of a varc from the event cache."""
    try:
        from escape.globals import get_client

        client = get_client()
        return client.cache.get_varc(varc_id)
    except Exception:
        return None


# Cache for VarClientID id -> name mapping (built on first use)
_varc_id_to_name: dict[int, str] | None = None


def _build_varc_cache() -> dict[int, str]:
    """Build varc id->name cache using fast __dict__ access."""
    global _varc_id_to_name

    if _varc_id_to_name is not None:
        return _varc_id_to_name

    _varc_id_to_name = {}
    try:
        from escape.generated.constants.varclient_id import VarClientID

        # Use __dict__ directly - much faster than dir() + getattr()
        for name, value in vars(VarClientID).items():
            if not name.startswith("_") and isinstance(value, int):
                _varc_id_to_name[value] = name
    except ImportError:
        pass

    return _varc_id_to_name


def get_varc_name(varc_id: int) -> str | None:
    """Get the name of a varc by its ID."""
    return _build_varc_cache().get(varc_id)


# Setter functions for cache_manager
def set_varps_data(data: dict[int, dict[str, Any]]) -> None:
    """Set the varps data (called by cache_manager during initialization)."""
    global _varps_data
    _varps_data = data


def set_varbits_data(data: dict[int, dict[str, Any]]) -> None:
    """Set the varbits data (called by cache_manager during initialization)."""
    global _varbits_data
    _varbits_data = data


def get_varps_data_count() -> int:
    """Get the number of loaded varps."""
    return len(_varps_data) if _varps_data else 0


def get_varbits_data_count() -> int:
    """Get the number of loaded varbits."""
    return len(_varbits_data) if _varbits_data else 0
