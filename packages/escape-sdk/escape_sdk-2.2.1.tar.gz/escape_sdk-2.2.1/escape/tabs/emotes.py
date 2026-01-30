"""Emotes tab module."""

from escape.types.gametab import GameTab, GameTabs


class Emotes(GameTabs):
    """Emotes tab for performing emote animations."""

    TAB_TYPE = GameTab.EMOTES

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self):
        """Actual initialization, runs once."""
        GameTabs.__init__(self)


# Module-level instance
emotes = Emotes()
