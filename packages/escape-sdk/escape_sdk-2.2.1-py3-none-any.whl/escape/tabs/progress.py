"""Progress tab module (Quest/Achievement Diaries)."""

from escape.types.gametab import GameTab, GameTabs


class Progress(GameTabs):
    """Progress tab for viewing quests and achievement diaries."""

    TAB_TYPE = GameTab.PROGRESS

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
progress = Progress()
