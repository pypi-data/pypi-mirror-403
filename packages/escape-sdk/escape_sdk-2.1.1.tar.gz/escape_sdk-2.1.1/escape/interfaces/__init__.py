"""Overlay windows - bank, GE, shop, dialogue, etc."""

from escape.client import client
from escape.interfaces.bank import Bank, bank
from escape.interfaces.fairy_ring import FairyRingInterface, fairy_ring
from escape.types.interfaces.general_interface import GeneralInterface
from escape.types.widget import Widget

# Lazy-loaded reverse lookup: group_id -> name
_interface_id_to_name: dict[int, str] | None = None


def _get_interface_id_to_name_map() -> dict[int, str]:
    """Build and cache a reverse lookup map from interface group ID to name."""
    global _interface_id_to_name

    if _interface_id_to_name is not None:
        return _interface_id_to_name

    _interface_id_to_name = {}

    try:
        from escape.generated.constants.interface_id import InterfaceID

        # Iterate over class attributes that are integers (group IDs)
        for name in dir(InterfaceID):
            if name.startswith("_") and not name.startswith("__"):
                # Handle names like _100GUIDE_EGGS_OVERLAY (start with underscore + digit)
                value = getattr(InterfaceID, name)
                if isinstance(value, int):
                    # Remove leading underscore for display
                    _interface_id_to_name[value] = name[1:]
            elif not name.startswith("_") and name.isupper():
                value = getattr(InterfaceID, name)
                if isinstance(value, int):
                    _interface_id_to_name[value] = name
    except ImportError:
        pass

    return _interface_id_to_name


def get_interface_name(group_id: int) -> str | None:
    """Get the interface name for a group ID."""
    return _get_interface_id_to_name_map().get(group_id)


class ScrollInterface(GeneralInterface):
    """Interface for scroll-type overlays."""

    def __init__(self):
        super().__init__(
            client.interface_id.MENU,
            [client.interface_id.Menu.LJ_LAYER1],
            get_children=False,
            menu_text="Continue",
            scrollbox=client.interface_id.Menu.LJ_LAYER1,
        )


class GliderInterface(GeneralInterface):
    """Interface for the gnome glider map."""

    def __init__(self):
        super().__init__(
            client.interface_id.GLIDERMAP,
            [
                client.interface_id.Glidermap.GRANDTREE_BUTTON,
                client.interface_id.Glidermap.WHITEWOLFMOUNTAIN_BUTTON,
                client.interface_id.Glidermap.VARROCK_BUTTON,
                client.interface_id.Glidermap.ALKHARID_BUTTON,
                client.interface_id.Glidermap.KARAMJA_BUTTON,
                client.interface_id.Glidermap.OGREAREA_BUTTON,
                client.interface_id.Glidermap.APEATOLL_BUTTON,
            ],
            get_children=False,
        )

        self.names = [
            "Ta Quir Priw",
            "Sindarpos",
            "Lemanto Andra",
            "Kar-Hewo",
            "Gandius",
            "Lemantolly Undri",
            "Ookookolly Undri",
        ]

    def get_widget_info(self) -> list[dict]:
        res = Widget.get_batch(self.buttons)

        for i in range(len(res)):
            res[i]["text"] = self.names[i]
        return res

    def is_right_option(self, widget_info, option_text=""):
        b = widget_info.get("bounds", "")
        text = widget_info.get("text", "")
        if option_text:
            return option_text in text and b[0] >= 0


class Interfaces:
    """Overlay interfaces: bank, fairy ring, spirit tree, etc."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self):
        self.spirit_tree = ScrollInterface()
        self.mushtree = GeneralInterface(
            client.interface_id.FOSSIL_MUSHTREES,
            [
                client.interface_id.FossilMushtrees.TREE1,
                client.interface_id.FossilMushtrees.TREE2,
                client.interface_id.FossilMushtrees.TREE3,
                client.interface_id.FossilMushtrees.TREE4,
            ],
            get_children=False,
            wrong_text="Not yet",
            menu_text="Continue",
        )
        self.zeah_minecart = ScrollInterface()
        self.jewellery_box = GeneralInterface(
            client.interface_id.POH_JEWELLERY_BOX,
            [
                client.interface_id.PohJewelleryBox.DUELING,
                client.interface_id.PohJewelleryBox.GAMING,
                client.interface_id.PohJewelleryBox.COMBAT,
                client.interface_id.PohJewelleryBox.SKILLS,
                client.interface_id.PohJewelleryBox.WEALTH,
                client.interface_id.PohJewelleryBox.GLORY,
            ],
            get_children=True,
            wrong_text="</str>",
        )
        self.gnome_glider = GliderInterface()
        self.charter_ship = GeneralInterface(
            client.interface_id.CHARTERING_MENU_SIDE,
            [client.interface_id.CharteringMenuSide.LIST_CONTENT],
            get_children=True,
            scrollbox=client.interface_id.CharteringMenuSide.LIST_CONTENT,
        )
        self.quetzal = GeneralInterface(
            client.interface_id.QUETZAL_MENU,
            [client.interface_id.QuetzalMenu.ICONS],
            get_children=True,
            use_actions=True,
        )

    @property
    def bank(self) -> Bank:
        """Bank interface."""
        return bank

    @property
    def fairy_ring(self) -> "FairyRingInterface":
        """Fairy ring interface."""
        return fairy_ring

    def get_open_interfaces(self) -> list[int]:
        """Get a list of currently open interface IDs."""
        return list(client.cache.get_open_widgets())

    def get_open_interface_names(self) -> list[str]:
        """Get a list of currently open interface names."""
        names = []
        for group_id in self.get_open_interfaces():
            name = get_interface_name(group_id)
            if name:
                names.append(name)
            else:
                names.append(f"UNKNOWN_{group_id}")
        return names


# Module-level instance
interfaces = Interfaces()


__all__ = ["Bank", "Interfaces", "bank", "get_interface_name", "interfaces"]
