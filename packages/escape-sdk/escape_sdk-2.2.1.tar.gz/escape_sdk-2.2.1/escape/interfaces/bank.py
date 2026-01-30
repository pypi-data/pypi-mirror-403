"""Banking module - handles all banking operations."""

import math
import random

from escape._internal.logger import logger
from escape.client import client
from escape.types.box import Box, create_grid
from escape.types.item import Item, ItemIdentifier
from escape.types.itemcontainer import ItemContainer
from escape.types.widget import Widget, WidgetFields
from escape.utilities import timing


class BankItem:
    """Represents an item to withdraw from the bank."""

    def __init__(self, identifier: ItemIdentifier, quantity: int, noted: bool = False):
        """Initialize a bank item for withdrawal."""
        self.identifier = identifier
        self.quantity = quantity
        self.noted = noted

    # Backwards compatibility
    @property
    def item_id(self) -> ItemIdentifier:
        """Deprecated: Use identifier instead."""
        return self.identifier


class Bank(ItemContainer):
    """Banking operations for deposits, withdrawals, and bank management."""

    # Expose BankItem as a class attribute for easy access
    BankItem = BankItem
    CONTAINER_ID = 95  # RuneLite bank container ID

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self):
        self.containerId = self.CONTAINER_ID
        self.slotCount = 920
        self._items = []

        self.deposit_all_button = Box(425, 295, 461, 331)
        self.deposit_gear_button = Box(462, 295, 498, 331)
        self.withdraw_item_button = Box(121, 310, 171, 332)
        self.withdraw_note_button = Box(172, 310, 222, 332)
        self.withdraw_1_button = Box(221, 310, 246, 332)
        self.withdraw_5_button = Box(246, 310, 271, 332)
        self.withdraw_10_button = Box(271, 310, 296, 332)
        self.withdraw_x_button = Box(296, 310, 321, 332)
        self.withdraw_all_button = Box(321, 310, 346, 332)
        self.quantity_buttons = {
            "1": self.withdraw_1_button,
            "5": self.withdraw_5_button,
            "10": self.withdraw_10_button,
            "X": self.withdraw_x_button,
            "All": self.withdraw_all_button,
        }
        self.search_button = Box(386, 295, 422, 331)
        self.settings_button = Box(467, 48, 492, 73)
        self.tab_buttons = create_grid(
            start_x=62, start_y=45, width=36, height=32, columns=9, rows=1, spacing_x=5, spacing_y=0
        )
        self.is_setup = False

        self.bank_area = Box(62, 83, 482, 293)
        self.bank_cache = {"lasttime": 0, "items": [], "quantities": []}

        self.capacity_widget = Widget(client.interface_id.Bankmain.CAPACITY)
        self.capacity_widget.enable(WidgetFields.get_text)

        self.item_widget = Widget(client.interface_id.Bankmain.ITEMS)
        self.item_widget.enable(WidgetFields.get_bounds)
        self.item_widget.enable(WidgetFields.is_hidden)

    def __init__(self):
        """Override to prevent ItemContainer.__init__ from running."""
        pass

    @property
    def items(self) -> list[Item | None]:
        cached = client.cache.get_item_container(self.CONTAINER_ID)
        if cached is None:
            self._items = []
            return self._items
        self._items = cached.items
        return self._items

    def is_open(self) -> bool:
        """Check if bank interface is open."""
        if client.interface_id.BANKMAIN in client.interfaces.get_open_interfaces():
            if not self.is_setup:
                text = self.capacity_widget.get().get("text", None)

                if text:
                    self.slotCount = int(text)
                    self.is_setup = True
            return True

        return False

    def get_open_tab(self) -> int | None:
        """Get currently open bank tab."""
        if not self.is_open():
            return None

        return client.resources.varps.get_varbit_by_name("BANK_CURRENTTAB")

    def get_itemcount_in_tab(self, tab_index: int) -> int:
        if tab_index > 8 or tab_index < 0:
            raise ValueError("tab_index must be between 0 and 8")

        if tab_index == 0:
            tabcounts = 0
            for i in range(1, 9):
                count = client.resources.varps.get_varbit_by_name(f"BANK_TAB_{i}")
                if count is None:
                    count = 0
                tabcounts += count
            return self.get_total_count() - tabcounts

        return client.resources.varps.get_varbit_by_name(f"BANK_TAB_{tab_index}")

    def get_current_x_amount(self) -> int:
        return client.resources.varps.get_varbit_by_name("BANK_REQUESTEDQUANTITY")

    def set_noted_mode(self, noted: bool) -> bool:
        if not self.is_open():
            return False

        currently_noted = client.resources.varps.get_varbit_by_name("BANK_WITHDRAWNOTES") > 0

        logger.info(f"Setting noted mode to {noted}, currently {currently_noted}")

        if not currently_noted and noted:
            self.withdraw_note_button.click()

        if currently_noted and not noted:
            self.withdraw_item_button.click()

        return timing.wait_until(
            lambda: client.resources.varps.get_varbit_by_name("BANK_WITHDRAWNOTES")
            == (1 if noted else 0),
            timeout=2.0,
        )

    def is_search_open(self) -> bool:
        if not self.is_open():
            return False

        return client.resources.varps.get_varc_value(client.var_client_id.MESLAYERMODE) == 11

    def is_x_query_open(self) -> bool:
        if not self.is_open():
            return False

        return client.resources.varps.get_varc_value(client.var_client_id.MESLAYERMODE) == 7

    def get_search_text(self) -> str:
        if not self.is_search_open():
            return ""

        return client.resources.varps.get_varc_value(client.var_client_id.MESLAYERINPUT)

    def open_search(self) -> bool:
        if not self.is_open():
            return False

        if self.is_search_open():
            return True

        self.search_button.click()

        return self.is_search_open()

    def search_item(self, text: str) -> bool:
        if not self.open_search():
            return False

        client.input.keyboard.type(text)

        return timing.wait_until(lambda: self.get_search_text() == text, timeout=0.5)

    def itemcounts_per_tab(self):
        counts = []

        counts.append(self.get_itemcount_in_tab(0))

        for i in range(1, 9):
            counts.append(self.get_itemcount_in_tab(i))
        return counts

    def get_index(self, identifier: ItemIdentifier) -> int | None:
        """Get the slot index of an item in the bank."""
        if not self.contains_item(identifier):
            return None

        return self.find_item_slot(identifier)

    def get_item_box(self, identifier: ItemIdentifier) -> Box | None:
        """Get the bounding box of an item in the bank."""
        index = self.get_index(identifier)

        if index is None:
            return None

        result = self.item_widget.get_child(index)
        try:
            print(result)
            if result["is_hidden"]:
                return None
            rectdata = result["bounds"]
            return Box(
                rectdata[0],
                rectdata[1],
                rectdata[0] + rectdata[2],
                rectdata[1] + rectdata[3],
            )
        except Exception as e:
            logger.error(f"Error getting item area: {e}")
            return None

    def is_box_clickable(self, box: Box) -> bool:
        return 83 <= box.y1 <= 257

    def get_scroll_count(self, box: Box) -> tuple[int, bool]:
        """Calculate scroll count and direction to make box visible."""
        step = 45
        min_y, max_y = 83, 257
        y = box.y1

        # Already visible
        if 83 <= y <= 257:
            return 0, False  # direction irrelevant

        if y < min_y:
            # Need to INCREASE y -> scroll_up
            scroll_up = True
            k_min = math.ceil((min_y - y) / step)  # smallest k so y + k*step >= 83
            k_max = math.floor((max_y - y) / step)  # largest  k so y + k*step <= 257
            if k_max < k_min:
                k_max = k_min  # safety
            k = random.randint(k_min, k_max)
            return k, scroll_up

        else:  # y > max_y
            # Need to DECREASE y -> scroll_down
            scroll_up = False
            k_min = math.ceil((y - max_y) / step)  # smallest k so y - k*step <= 257
            k_max = math.floor((y - min_y) / step)  # largest  k so y - k*step >= 83
            if k_max < k_min:
                k_max = k_min  # safety
            k = random.randint(k_min, k_max)
            return k, scroll_up

    def make_item_visible(self, identifier: ItemIdentifier) -> Box | None:
        """Scroll the bank view to make an item visible and clickable."""
        if not self.contains_item(identifier):
            raise ValueError("Item not found in bank")

        box = self.get_item_box(identifier)

        if box is None:
            tab_index = self.get_tab_index(identifier)
            if tab_index is None:
                return None
            if not self.open_tab(tab_index):
                return None
            box = self.get_item_box(identifier)
            if box is None:
                return None

        scroll_count, scroll_up = self.get_scroll_count(box)

        if scroll_count != 0:
            self.bank_area.hover()

            client.input.mouse.scroll(up=scroll_up, count=scroll_count)
            timing.sleep(0.05)

            # Verify visibility
            box = self.get_item_box(identifier)
            if box is None:
                return None

        logger.info(f"found box: {box}")

        if box is not None and self.is_box_clickable(box):
            return box
        else:
            return None

    def get_tab_index(self, identifier: ItemIdentifier) -> int | None:
        """Get the bank tab index containing an item."""
        index = self.get_index(identifier)

        if index is None:
            return None

        tabcounts = self.itemcounts_per_tab()

        cumcount = 0
        for i in range(1, 0):
            cumcount += tabcounts[i]
            if index < cumcount:
                return i

        return None

    def open_tab(self, tab_index: int) -> bool:
        """Open a specific bank tab."""
        if not self.is_open():
            return False

        if tab_index < 0 or tab_index > 8:
            raise ValueError("tab_index must be between 0 and 8")

        if self.get_open_tab() == tab_index:
            return True

        self.tab_buttons[tab_index].click()

        return timing.wait_until(lambda: self.get_open_tab() == tab_index, timeout=2.0)

    def set_withdraw_quantity(self, quantity: str, wait: bool = True) -> bool:
        """Set the withdraw quantity mode."""
        if not self.is_open():
            return False

        allowed = ["1", "5", "10", "X", "All"]

        if quantity not in allowed:
            raise ValueError("quantity must be one of '1', '5', '10', 'X', 'All'")

        index = allowed.index(quantity)

        self.quantity_buttons[quantity].click()

        if not wait:
            return True

        return timing.wait_until(
            lambda: client.resources.varps.get_varbit_by_name("BANK_QUANTITY_TYPE") == index,
            timeout=1,
        )

    def check_items_deposited(self, start_count) -> bool:
        current_count = client.tabs.inventory.get_total_quantity()
        logger.info(f"start count: {start_count}, current count: {current_count}")
        return current_count < start_count

    def deposit_all(self, wait: bool = True) -> bool:
        """Deposit all items in inventory."""
        if not self.is_open():
            return False

        start = client.tabs.inventory.get_total_quantity()

        if start == 0:
            return True  # Nothing to deposit

        self.deposit_all_button.click()

        if not wait:
            return True

        return timing.wait_until(lambda: self.check_items_deposited(start), timeout=2.0)

    def deposit_equipment(self, wait: bool = True) -> bool:
        """Deposit all worn equipment."""
        if not self.is_open():
            return False

        start = client.tabs.equipment.get_total_count()

        self.deposit_gear_button.click()

        if not wait:
            return True

        return timing.wait_until(
            lambda: client.tabs.equipment.get_total_count() < start, timeout=2.0
        )

    def withdraw_items(self, bank_items: list[BankItem], safe: bool = True) -> bool:
        """Withdraw multiple items from the bank."""
        if not self.is_open():
            return False

        for bank_item in bank_items:
            identifier = bank_item.identifier
            quantity = bank_item.quantity
            noted = bank_item.noted

            if not self.contains_item(identifier):
                if safe:
                    raise ValueError(f"Item {identifier} not found in bank!")
                return False

            slot = self.find_item_slot(identifier)
            if slot is not None:
                item = self.items[slot]
                if item is None or item.quantity < quantity:
                    if safe:
                        raise ValueError(f"Not enough quantity of {identifier} in bank!")
                    return False

            if not self.is_open():
                return False

            area = self.make_item_visible(identifier)

            self.set_noted_mode(noted)

            if area is None:
                return False

            area.hover()
            client.interactions.menu.wait_has_option("Withdraw")

            if quantity == 1:
                client.interactions.menu.click_option("Withdraw-1")
            elif quantity == 5:
                client.interactions.menu.click_option("Withdraw-5")
            elif quantity == 10:
                client.interactions.menu.click_option("Withdraw-10")
            elif quantity <= 0:
                client.interactions.menu.click_option("Withdraw-All")
            elif self.get_current_x_amount() == quantity:
                client.interactions.menu.click_option(f"Withdraw-{quantity}")
            else:
                client.interactions.menu.click_option("Withdraw-X")
                timing.wait_until(lambda: self.is_x_query_open(), timeout=3.0)
                client.input.keyboard.type(str(quantity))
                client.input.keyboard.press_enter()

        return True

    def withdraw_item(self, bank_item: BankItem, safe: bool = True) -> bool:
        """Withdraw a single item from the bank."""
        return self.withdraw_items([bank_item], safe=safe)


# Module-level instance
bank = Bank()
