"""Pytest configuration and fixtures."""

import sys
from unittest.mock import MagicMock

# Mock inotify_simple before any imports (Linux-only library)
mock_inotify = MagicMock()
mock_inotify.INotify.return_value = MagicMock()
mock_inotify.flags = MagicMock()
sys.modules["inotify_simple"] = mock_inotify

# Mock os functions for /dev/shm paths (game infrastructure)
import builtins  # noqa: E402
import os  # noqa: E402

_original_exists = os.path.exists
_original_open = builtins.open


def _mock_exists(path):
    if "/dev/shm" in str(path):
        return True
    return _original_exists(path)


def _mock_open(path, *args, **kwargs):
    if "/dev/shm" in str(path):
        # Return empty bytes for shared memory files
        from io import BytesIO

        return BytesIO(b"")
    return _original_open(path, *args, **kwargs)


os.path.exists = _mock_exists
builtins.open = _mock_open

import pytest  # noqa: E402

from escape.client import Client  # noqa: E402


@pytest.fixture
def client():
    """
    Provide a Client instance for testing.

    The Client is a singleton that auto-connects during initialization.

    Returns:
        Client: The singleton client instance (already connected)
    """
    return Client()


@pytest.fixture
def connected_client(client):
    """
    Provide a connected Client instance.

    Args:
        client: Client fixture

    Returns:
        Client: A connected client instance
    """
    # Client auto-connects, so just ensure it's connected
    if not client.is_connected():
        client.connect()
    yield client
    # Don't disconnect - singleton should stay connected for other tests
