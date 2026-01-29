"""Main Client class that provides access to all game modules."""

import os
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING

from escape._internal.api import RuneLiteAPI
from escape._internal.cache_manager import ensure_generated_in_path, ensure_resources_loaded
from escape._internal.logger import logger
from escape._internal.resources import objects as objects_module
from escape._internal.resources import varps as varps_module


def _ensure_generated_symlink() -> None:
    """
    Ensure the escape/generated symlink points to ~/.cache/escape/generated.

    If the symlink is broken or missing, it will be recreated.
    """
    escape_dir = Path(__file__).parent
    generated_link = escape_dir / "generated"

    # Determine target cache directory
    xdg_cache = os.getenv("XDG_CACHE_HOME")
    cache_base = Path(xdg_cache) if xdg_cache else Path.home() / ".cache"
    generated_target = cache_base / "escape" / "generated"

    # Ensure target directory exists
    generated_target.mkdir(parents=True, exist_ok=True)

    # Check if symlink is valid
    needs_creation = False
    if generated_link.is_symlink():
        try:
            if generated_link.resolve() != generated_target.resolve():
                needs_creation = True
                generated_link.unlink()
        except OSError:
            # Broken symlink
            needs_creation = True
            generated_link.unlink()
    elif generated_link.exists():
        if generated_link.is_file():
            # Regular file (possibly leftover), remove it
            needs_creation = True
            generated_link.unlink()
        else:
            # Real directory - don't touch it
            return
    else:
        needs_creation = True

    if needs_creation:
        generated_link.symlink_to(generated_target)


# Ensure symlink is active before importing generated modules
ensure_generated_in_path()
_ensure_generated_symlink()

# Check for game resource updates
if not ensure_resources_loaded():
    logger.warning("Some resources failed to load")

GLOBAL_API_INSTANCE: RuneLiteAPI = RuneLiteAPI()

if TYPE_CHECKING:
    from escape._internal.cache.event_cache import EventCache
    from escape.generated.constants.animation_id import AnimationID
    from escape.generated.constants.interface_id import InterfaceID
    from escape.generated.constants.item_id import ItemID
    from escape.generated.constants.npc_id import NpcID
    from escape.generated.constants.object_id import ObjectID
    from escape.generated.constants.sprite_id import SpriteID
    from escape.generated.constants.varclient_id import VarClientID
    from escape.input import Input
    from escape.interactions import Interactions
    from escape.interfaces import Interfaces
    from escape.navigation import Navigation
    from escape.player import Player
    from escape.tabs import Tabs
    from escape.world import World


class Client:
    """Main entry point providing access to all game modules."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self):
        """Actual initialization, runs once."""
        logger.info("Initializing Client")

        # Initialize API and connect
        self.api: RuneLiteAPI = GLOBAL_API_INSTANCE
        self.api.connect()

        self._connected = True

        # Initialize event cache and consumer
        from escape._internal.cache.event_cache import EventCache
        from escape._internal.events.consumer import EventConsumer

        self._event_cache = EventCache(event_history_size=100)
        self._event_consumer = EventConsumer(self._event_cache, warn_on_gaps=False)

        # Pre-import projection module before warmup to avoid import deadlock.
        # Warmup processes world_view_loaded which imports projection - if we don't
        # pre-import, the warmup thread blocks on import lock held by main thread.
        import escape.world.projection  # noqa: F401

        self._event_consumer.start(wait_for_warmup=True)

        # Register for automatic cleanup on exit
        from escape._internal.cleanup import register_api_for_cleanup

        register_api_for_cleanup(self.api)

        # Ensure cleanup happens on Ctrl+C
        from escape._internal.cleanup import ensure_cleanup_on_signal

        ensure_cleanup_on_signal()

        logger.success("Client ready")

    def wait_for_warmup(self, timeout: float = 5.0) -> bool:
        """Wait for event cache warmup to complete."""
        if self._event_consumer is None:
            return True
        return self._event_consumer.wait_for_warmup(timeout=timeout)

    def connect(self):
        """Connect to RuneLite bridge."""
        if not self._connected:
            logger.info("Connecting client to RuneLite")
            self.api.connect()
            self._connected = True
            logger.success("Client connected!")

    def disconnect(self):
        """Disconnect from RuneLite bridge and cleanup resources."""
        if self._connected:
            logger.info("Disconnecting client")

            # Stop event consumer if running
            if self._event_consumer is not None:
                self._event_consumer.stop()
                self._event_consumer = None

            self._connected = False
            logger.success("Client disconnected")

    def is_connected(self) -> bool:
        """
        Check if client is connected.

        Returns:
            bool: Connection status
        """
        return self._connected

    def query(self):
        """Create a query for API operations."""
        return self.api.query()

    @property
    def event_cache(self) -> "EventCache":
        """Access cached game state from events."""
        return self._event_cache

    @property
    def item_id(self) -> type["ItemID"]:
        """Access ItemID constants."""
        try:
            from .generated.constants import ItemID

            return ItemID
        except ImportError:
            from constants import ItemID  # type: ignore[import-not-found]

            return ItemID

    @property
    def object_id(self) -> type["ObjectID"]:
        """Access ObjectID constants."""
        try:
            from .generated.constants import ObjectID

            return ObjectID
        except ImportError:
            from constants import ObjectID  # type: ignore[import-not-found]

            return ObjectID

    @property
    def npc_id(self) -> type["NpcID"]:
        """Access NpcID constants."""
        try:
            from .generated.constants import NpcID

            return NpcID
        except ImportError:
            from constants import NpcID  # type: ignore[import-not-found]

            return NpcID

    @property
    def animation_id(self) -> type["AnimationID"]:
        """Access AnimationID constants."""
        try:
            from .generated.constants import AnimationID

            return AnimationID
        except ImportError:
            from constants import AnimationID  # type: ignore[import-not-found]

            return AnimationID

    @property
    def interface_id(self) -> type["InterfaceID"]:
        """Access InterfaceID constants."""
        try:
            from .generated.constants import InterfaceID

            return InterfaceID
        except ImportError:
            from constants import InterfaceID  # type: ignore[import-not-found]

            return InterfaceID

    @property
    def var_client_id(self) -> type["VarClientID"]:
        """Access VarClientID constants."""
        try:
            from .generated.constants import VarClientID

            return VarClientID
        except ImportError:
            from constants import VarClientID  # type: ignore[import-not-found]

            return VarClientID

    @property
    def sprite_id(self) -> type["SpriteID"]:
        """Access SpriteID constants."""
        try:
            from .generated.constants import SpriteID

            return SpriteID
        except ImportError:
            from constants import SpriteID  # type: ignore[import-not-found]

            return SpriteID

    @property
    def tabs(self) -> "Tabs":
        """Access game tabs (inventory, skills, prayer, etc.)."""
        from escape.tabs import tabs

        return tabs

    @property
    def input(self) -> "Input":
        """Access input controls (mouse, keyboard)."""
        from escape.input import input

        return input

    @property
    def world(self) -> "World":
        """Access 3D world entities (ground items, NPCs, objects)."""
        from escape.world import world

        return world

    @property
    def navigation(self) -> "Navigation":
        """Access pathfinding and walking utilities."""
        from escape.navigation import navigation

        return navigation

    @property
    def interactions(self) -> "Interactions":
        """Access game interactions (menu, widgets)."""
        from escape.interactions import interactions

        return interactions

    @property
    def interfaces(self) -> "Interfaces":
        """Access game interfaces (bank, GE, shop, etc.)."""
        from escape.interfaces import interfaces

        return interfaces

    @property
    def player(self) -> "Player":
        """Access local player state (position, energy, etc.)."""
        from escape.player.player import player

        return player

    @property
    def resources(self):
        """Access game resources (varps, objects)."""
        if not hasattr(self, "_resources_namespace"):
            self._resources_namespace = self._ResourcesNamespace()
        return self._resources_namespace

    class _ResourcesNamespace:
        """Namespace for accessing game resources."""

        @property
        def varps(self) -> ModuleType:
            """Access varps/varbits functions."""
            return varps_module

        @property
        def objects(self) -> ModuleType:
            """Access objects functions."""
            return objects_module

    @property
    def cache(self) -> "EventCache":
        """Event cache with instant access to game state and events."""
        return self._event_cache

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, *args):
        """Context manager exit."""
        self.disconnect()


# Module-level instance
client = Client()
