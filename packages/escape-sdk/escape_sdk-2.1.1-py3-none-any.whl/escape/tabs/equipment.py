"""Equipment tab module."""

from enum import Enum

from escape.client import client
from escape.types.box import Box
from escape.types.gametab import GameTab, GameTabs
from escape.types.interfaces.buttons import Buttons
from escape.types.item import Item
from escape.types.itemcontainer import ItemContainer


class EquipmentSlots(Enum):
    """Enumeration of equipment slots."""

    HEAD = 0
    CAPE = 1
    NECK = 2
    WEAPON = 3
    TORSO = 4
    SHIELD = 5
    LEGS = 7
    HANDS = 9
    FEET = 10
    RING = 12
    AMMO = 13
    EXTRA_AMMO = 14


class Equipment(GameTabs, ItemContainer):
    """Equipment tab for viewing and managing worn items."""

    TAB_TYPE = GameTab.EQUIPMENT
    CONTAINER_ID = 94

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self):
        """Actual initialization, runs once."""
        GameTabs.__init__(self)
        self.containerId = self.CONTAINER_ID
        self.bottom_buttons = Buttons(
            client.interface_id.WORNITEMS,
            [
                client.interface_id.Wornitems.EQUIPMENT,
                client.interface_id.Wornitems.PRICECHECKER,
                client.interface_id.Wornitems.DEATHKEEP,
                client.interface_id.Wornitems.CALL_FOLLOWER,
            ],
            [
                "View equipment stats",
                "View guide prices",
                "View items kept on death",
                "Call follower",
            ],
        )

        self.slots = Buttons(
            client.interface_id.WORNITEMS,
            [
                client.interface_id.Wornitems.SLOT0,
                client.interface_id.Wornitems.SLOT1,
                client.interface_id.Wornitems.SLOT2,
                client.interface_id.Wornitems.SLOT3,
                client.interface_id.Wornitems.SLOT4,
                client.interface_id.Wornitems.SLOT5,
                client.interface_id.Wornitems.SLOT7,
                client.interface_id.Wornitems.SLOT9,
                client.interface_id.Wornitems.SLOT10,
                client.interface_id.Wornitems.SLOT12,
                client.interface_id.Wornitems.SLOT13,
                client.interface_id.Wornitems.EXTRA_QUIVER_AMMO,
            ],
            list(EquipmentSlots.__members__.keys()),
            menu_text="Remove",
        )
        self.boxes: list[Box | None] = [
            Box(624, 209, 660, 245),
            Box(583, 248, 619, 284),
            Box(624, 248, 660, 284),
            Box(568, 287, 604, 323),
            Box(624, 287, 660, 323),
            Box(680, 287, 716, 323),
            Box(624, 327, 660, 363),
            Box(568, 367, 604, 403),
            Box(624, 367, 660, 403),
            Box(680, 367, 716, 403),
            Box(665, 248, 701, 284),
            Box(665, 209, 701, 245),
        ]
        self.is_ready = True

    @property
    def items(self) -> list[Item | None]:
        """Auto-sync items from cache when accessed."""
        cached = client.cache.get_item_container(self.CONTAINER_ID)
        if cached is None:
            self._items = []
            return self._items
        self._items = cached.items
        return self._items

    def open_equipment_view(self) -> bool:
        """Open the equipment view within the equipment tab."""
        if not self.open():
            return False

        return self.bottom_buttons.interact("View equipment stats")

    def open_price_checker(self) -> bool:
        """Open the price checker within the equipment tab."""
        if not self.open():
            return False

        return self.bottom_buttons.interact("View guide prices")

    def open_view_kept_on_death(self) -> bool:
        """Open the view kept on death within the equipment tab."""
        if not self.open():
            return False

        return self.bottom_buttons.interact("View items kept on death")

    def call_follower(self) -> bool:
        """Call the follower within the equipment tab."""
        if not self.open():
            return False

        return self.bottom_buttons.interact("Call follower")

    def remove_slot(self, slot: EquipmentSlots | str) -> bool:
        """Remove an item from a specific equipment slot."""
        if not self.open():
            return False

        slot_name = slot.name if isinstance(slot, EquipmentSlots) else slot
        return self.slots.interact(slot_name)

    def remove_slots(self, slots: list[EquipmentSlots | str]) -> int:
        """Remove items from multiple equipment slots, returning count removed."""
        if not self.open():
            return 0

        removed_count = 0
        for slot in slots:
            if self.remove_slot(slot):
                removed_count += 1
        return removed_count


# Module-level instance
equipment = Equipment()
