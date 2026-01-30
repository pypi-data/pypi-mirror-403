"""Global access to Client (deprecated: use escape.client instead)."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from escape._internal.cache.event_cache import EventCache


def get_client():
    """Get the Client instance (deprecated)."""
    from escape.client import client

    return client


def get_api():
    """Get the RuneLiteAPI instance."""
    from escape._internal.api import RuneLiteAPI

    return RuneLiteAPI()


def get_event_cache() -> "EventCache":
    """Get the EventCache instance from the Client."""
    from escape.client import client

    return client.cache


# Convenience exports
__all__ = [
    "get_api",
    "get_client",
    "get_event_cache",
]
