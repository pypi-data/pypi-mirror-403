"""Tests for the main Client class."""

from escape.client import Client


class TestClient:
    """Test suite for Client class."""

    def test_client_initialization(self):
        """Test that client initializes properly as a connected singleton."""
        client = Client()
        assert client is not None
        # Client auto-connects during initialization
        assert client.is_connected()

    def test_client_singleton(self):
        """Test that Client is a singleton."""
        client1 = Client()
        client2 = Client()
        assert client1 is client2

    def test_client_has_api(self, client):
        """Test client has API access."""
        assert client.api is not None

    def test_client_has_event_cache(self, client):
        """Test client has event cache."""
        assert client.event_cache is not None

    def test_client_disconnect_reconnect(self, client):
        """Test client disconnect and reconnect cycle."""
        assert client.is_connected()
        client.disconnect()
        assert not client.is_connected()
        client.connect()
        assert client.is_connected()
