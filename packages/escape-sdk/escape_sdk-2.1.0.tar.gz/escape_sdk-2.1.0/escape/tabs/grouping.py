"""Grouping tab module (Clan/Group activities)."""

from escape.client import client
from escape.types.gametab import GameTab, GameTabs
from escape.types.interfaces.general_interface import GeneralInterface
from escape.types.widget import WidgetFields
from escape.utilities.timing import wait_until


class Grouping(GameTabs):
    """Grouping tab for clan chat and minigame teleports."""

    TAB_TYPE = GameTab.GROUPING

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self):
        """Actual initialization, runs once."""
        GameTabs.__init__(self)
        self.sub_tabs = GeneralInterface(
            client.interface_id.SIDE_CHANNELS,
            [
                client.interface_id.SideChannels.TAB_0,
                client.interface_id.SideChannels.TAB_1,
                client.interface_id.SideChannels.TAB_2,
                client.interface_id.SideChannels.TAB_3,
            ],
            get_children=False,
            use_actions=True,
        )

        for w in self.sub_tabs.buttons:
            w.enable(WidgetFields.get_on_op_listener)

        self.sub_tab_names = ["Chat-channel", "Your Clan", "View another clan", "Grouping"]

        self.dropdown_button = GeneralInterface(
            client.interface_id.GROUPING,
            [client.interface_id.Grouping.CURRENTGAME],
            get_children=False,
        )

        self.dropdown_selector = GeneralInterface(
            client.interface_id.GROUPING,
            [client.interface_id.Grouping.DROPDOWN_CONTENTS],
            get_children=True,
            menu_text="Select",
            scrollbox=client.interface_id.Grouping.DROPDOWN_CONTENTS,
        )

        self.teleport_button = GeneralInterface(
            client.interface_id.GROUPING,
            [client.interface_id.Grouping.TELEPORT_TEXT1],
            get_children=False,
            menu_text="Teleport",
        )

    def get_open_sub_tab(self) -> str | None:
        """Get the currently open sub-tab within the grouping tab.

        Returns:
            str | None: The name of the open sub-tab, or None if none are open.
        """
        if not self.open():
            return None

        info = self.sub_tabs.get_widget_info()

        for i, w in enumerate(info):
            if len(w.get("on_op_listener", [])) == 3:
                return self.sub_tab_names[i]
        return None

    def open_sub_tab(self, sub_tab: str) -> bool:
        """Open a specific sub-tab within the grouping tab.

        Args:
            sub_tab (str): The sub-tab substring to open.
        Returns:
            bool: True if the sub-tab was opened successfully, False otherwise.
        """
        if not self.is_open():
            self.open()

        for name in self.sub_tab_names:
            if sub_tab.lower() in name.lower():
                if self.get_open_sub_tab() == name:
                    return True
                elif self.sub_tabs.interact(sub_tab):
                    return wait_until(lambda n=name: self.get_open_sub_tab() == n, timeout=3.0)
        return False

    def get_selected_game(self) -> str | None:
        """Get the currently selected game from the grouping dropdown.

        Returns:
            str | None: The name of the selected game, or None if not found.
        """
        if not self.open() and not self.open_sub_tab("Grouping"):
            return None

        info = self.dropdown_button.get_widget_info()
        if not info:
            return None
        text = info[0].get("text", "")
        return text if text else None

    def is_game_selected(self, game_name: str) -> bool:
        selected_game = self.get_selected_game()
        return selected_game is not None and game_name.lower() in selected_game.lower()

    def dropdown_fully_loaded(self) -> bool:
        info = self.dropdown_selector.get_widget_info()
        return len(info) > 0 and info[-1].get("bounds")[0] >= 0

    def select_game(self, game_name: str) -> bool:
        """Select a game from the grouping dropdown.

        Args:
            game_name (str): The name of the game to select.
        Returns:
            bool: True if the game was selected successfully, False otherwise.
        """
        if not self.open() or not self.open_sub_tab("Group"):
            return False

        current_game = self.get_selected_game()
        if current_game and game_name.lower() in current_game.lower():
            return True  # Already selected

        if len(self.dropdown_selector.get_widget_info()) == 0 and (
            not self.dropdown_button.interact("")
            or not wait_until(self.dropdown_fully_loaded, timeout=3.0)
        ):
            return False
        if self.dropdown_selector.interact(game_name):
            return wait_until(lambda: self.is_game_selected(game_name), timeout=3.0)

        return False

    def click_teleport(self) -> bool:
        """Click the teleport button in the grouping tab.

        Returns:
            bool: True if the teleport action was successful, False otherwise.
        """
        if not self.open() or not self.open_sub_tab("Group"):
            return False

        return bool(self.teleport_button.interact("Teleport"))

    def teleport_to_minigame(self, game_name: str) -> bool:
        """Teleport to a specific minigame via the grouping tab.

        Args:
            game_name (str): The name of the minigame to teleport to.
        Returns:
            bool: True if the teleport action was successful, False otherwise.
        """
        if not self.select_game(game_name):
            return False

        return self.click_teleport()


# Module-level instance
grouping = Grouping()
