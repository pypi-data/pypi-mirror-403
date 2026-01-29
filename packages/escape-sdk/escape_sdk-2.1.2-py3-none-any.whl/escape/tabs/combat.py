"""Combat tab module."""

from escape.types.gametab import GameTab, GameTabs


class Combat(GameTabs):
    """Combat tab for viewing combat stats and special attack."""

    TAB_TYPE = GameTab.COMBAT

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
combat = Combat()
