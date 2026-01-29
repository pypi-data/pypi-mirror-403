"""Base GameTab class - parent class for all game tab modules."""

from enum import Enum

from escape.types.box import Box
from escape.utilities.timing import wait_until


class GameTab(Enum):
    """Enum representing all game tab types in OSRS."""

    COMBAT = 0
    SKILLS = 1
    PROGRESS = 2
    INVENTORY = 3
    EQUIPMENT = 4
    PRAYER = 5
    MAGIC = 6
    GROUPING = 7
    ACCOUNT = 8
    FRIENDS = 9
    LOGOUT = 10
    SETTINGS = 11
    EMOTES = 12
    MUSIC = 13


class GameTabs:
    """Base class for all game tabs in Old School RuneScape."""

    # Subclasses must override this
    TAB_TYPE: GameTab | None = None

    def __init__(self):
        """Initialize a GameTab instance with bounds and tab areas."""
        x = 547
        y = 205
        w = 190
        h = 261
        self.bounds = Box(x, y, x + w, y + h)
        # init as list of Boxes for each tab
        self.tab_box_array: list[Box] = []

        for i in range(7):
            tab_x = 530 + (i * 33)
            tab_y = 170
            tab_w = 27
            tab_h = 32
            self.tab_box_array.append(Box(tab_x, tab_y, tab_x + tab_w, tab_y + tab_h))

        for i in range(7):
            tab_x = 530 + (i * 33)
            tab_y = 470
            tab_w = 27
            tab_h = 32
            self.tab_box_array.append(Box(tab_x, tab_y, tab_x + tab_w, tab_y + tab_h))

        # Swap index 8 and 9 because the game is weird
        self.tab_box_array[8], self.tab_box_array[9] = self.tab_box_array[9], self.tab_box_array[8]

    def is_open(self) -> bool:
        """Check if this specific game tab is currently open."""
        from escape.client import client

        current_tab = client.tabs.get_open_tab()
        return current_tab == self.TAB_TYPE

    def hover(self) -> bool:
        """Hover over this specific game tab."""
        if self.TAB_TYPE is None:
            raise NotImplementedError("Subclass must set TAB_TYPE class attribute")

        # Hover over the tab's area
        tab_area = self.tab_box_array[self.TAB_TYPE.value]
        tab_area.hover()

        return True

    def open(self) -> bool:
        """Open this specific game tab."""
        if self.TAB_TYPE is None:
            raise NotImplementedError("Subclass must set TAB_TYPE class attribute")

        if self.is_open():
            return True  # Already open

        # Click on the tab's area (which automatically hovers first)
        tab_area = self.tab_box_array[self.TAB_TYPE.value]
        tab_area.click()

        return wait_until(self.is_open, timeout=0.1, poll_interval=0.001)
