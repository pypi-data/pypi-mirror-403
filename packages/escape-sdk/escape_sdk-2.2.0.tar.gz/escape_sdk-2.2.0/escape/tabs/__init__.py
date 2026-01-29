"""
GameTabs package - contains all game tab modules for OSRS.

Each tab inherits from the base GameTabs class and provides
tab-specific functionality for the Old School RuneScape interface.
"""

from escape.types.gametab import GameTab, GameTabs

from .account import Account, account
from .combat import Combat, combat
from .emotes import Emotes, emotes
from .equipment import Equipment, equipment
from .friends import Friends, friends
from .grouping import Grouping, grouping
from .inventory import Inventory, inventory
from .logout import Logout, logout
from .magic import Magic, magic
from .music import Music, music
from .prayer import Prayer, prayer
from .progress import Progress, progress
from .settings import Settings, settings
from .skills import Skills, skills


class Tabs:
    """Access point for all game tabs (inventory, equipment, prayer, etc.)."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def combat(self) -> Combat:
        """Combat tab."""
        return combat

    @property
    def skills(self) -> Skills:
        """Skills tab."""
        return skills

    @property
    def progress(self) -> Progress:
        """Progress tab."""
        return progress

    @property
    def inventory(self) -> Inventory:
        """Inventory tab."""
        return inventory

    @property
    def equipment(self) -> Equipment:
        """Equipment tab."""
        return equipment

    @property
    def prayer(self) -> Prayer:
        """Prayer tab."""
        return prayer

    @property
    def magic(self) -> Magic:
        """Magic tab."""
        return magic

    @property
    def grouping(self) -> Grouping:
        """Grouping tab."""
        return grouping

    @property
    def friends(self) -> Friends:
        """Friends tab."""
        return friends

    @property
    def account(self) -> Account:
        """Account tab."""
        return account

    @property
    def settings(self) -> Settings:
        """Settings tab."""
        return settings

    @property
    def logout(self) -> Logout:
        """Logout tab."""
        return logout

    @property
    def emotes(self) -> Emotes:
        """Emotes tab."""
        return emotes

    @property
    def music(self) -> Music:
        """Music tab."""
        return music

    def get_open_tab(self) -> GameTab | None:
        """Get the currently open tab, or None if unknown."""
        from escape.client import client

        index = client.cache.get_varc(client.var_client_id.TOPLEVEL_PANEL)
        return GameTab(index) if index in GameTab._value2member_map_ else None


# Module-level instance
tabs = Tabs()


__all__ = [
    "Account",
    "Combat",
    "Emotes",
    "Equipment",
    "Friends",
    "GameTab",
    "GameTabs",
    "Grouping",
    "Inventory",
    "Logout",
    "Magic",
    "Music",
    "Progress",
    "Settings",
    "Skills",
    "Tabs",
    "account",
    "combat",
    "emotes",
    "equipment",
    "friends",
    "grouping",
    "inventory",
    "logout",
    "magic",
    "music",
    "progress",
    "settings",
    "skills",
    "tabs",
]
