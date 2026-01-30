"""Magic tab module."""

from escape._internal.logger import logger
from escape.client import client
from escape.types.box import Box
from escape.types.gametab import GameTab, GameTabs
from escape.types.widget import Widget, WidgetFields


class Magic(GameTabs):
    """Magic tab for viewing and casting spells."""

    TAB_TYPE = GameTab.MAGIC

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self):
        """Actual initialization, runs once."""
        GameTabs.__init__(self)

        magic_on_classes = [
            client.sprite_id.Magicon,
            client.sprite_id._2XStandardSpellsOn,
            client.sprite_id.Magicon2,
            client.sprite_id._2XAncientSpellsOn,
            client.sprite_id._2XLunarSpellsOn,
            client.sprite_id.LunarMagicOn,
            client.sprite_id.MagicNecroOn,
            client.sprite_id._2XNecroSpellsOn,
        ]

        magic_off_classes = [
            client.sprite_id.Magicoff,
            client.sprite_id._2XStandardSpellsOff,
            client.sprite_id.Magicoff2,
            client.sprite_id._2XAncientSpellsOff,
            client.sprite_id._2XLunarSpellsOff,
            client.sprite_id.LunarMagicOff,
            client.sprite_id.MagicNecroOff,
            client.sprite_id._2XNecroSpellsOff,
        ]

        self.on_sprites = {
            v for cls in magic_on_classes for v in vars(cls).values() if isinstance(v, int)
        }
        self.off_sprites = {
            v for cls in magic_off_classes for v in vars(cls).values() if isinstance(v, int)
        }

        self.spells = client.interface_id.MagicSpellbook

        self._allSpellWidgets = []

        for i in range(
            client.interface_id.MagicSpellbook.SPELLLAYER + 1,
            client.interface_id.MagicSpellbook.INFOLAYER,
        ):
            w = Widget(i)
            w.enable(WidgetFields.get_sprite_id)
            self._allSpellWidgets.append(w)

    def _get_info(self, spell: int):
        """Get spell info widget by spell ID."""
        w = Widget(spell)
        w.enable(WidgetFields.get_bounds)
        w.enable(WidgetFields.is_hidden)
        w.enable(WidgetFields.get_sprite_id)
        return w.get()

    def _get_all_visible_sprites(self):
        """Get all visible spell sprites."""
        res = Widget.get_batch(self._allSpellWidgets)
        return [w["spriteId"] for w in res]

    def get_castable_spell_ids(self):
        vis = self._get_all_visible_sprites()
        return set(vis).intersection(self.on_sprites)

    def _can_cast_spell(self, sprite_id: int) -> bool:
        """Check if a spell can be cast by its widget ID.

        Args:
            spell (int): The widget ID of the spell to check.
        Returns:
            bool: True if the spell can be cast, False otherwise.
        """
        return sprite_id in self.get_castable_spell_ids()

    def cast_spell(self, spell: int, option: str = "Cast") -> bool:
        """Cast a spell by its widget ID."""
        from time import time

        if not self.open():
            return False
        t = time()
        w = self._get_info(spell)
        logger.info(f"part 1 took {time() - t:.4f}s")
        if self._can_cast_spell(w["spriteId"]) and not w["is_hidden"]:
            bounds = w["bounds"]
            box = Box(bounds[0], bounds[1], bounds[0] + bounds[2], bounds[1] + bounds[3])
            print(box)
            logger.info(f"part 2 took {time() - t:.4f}s")
            res = box.click_option(option)
            logger.info(f"part 3 took {time() - t:.4f}s")
            return res

        return False


# Module-level instance
magic = Magic()
