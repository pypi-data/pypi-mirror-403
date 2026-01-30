import escape.utilities.timing as timing
from escape.client import client
from escape.types.box import Box
from escape.types.widget import Widget, WidgetFields


class GeneralInterface:
    """Interface class with optional scrollbox support."""

    def __init__(
        self,
        group: int,
        button_ids: list[int],
        get_children: bool = True,
        wrong_text: str = "5f5f5d",
        menu_text: str | None = None,
        scrollbox: int | None = None,
        max_scroll: int = 10,
        use_actions: bool = False,
    ):
        self.group = group
        self.get_children = get_children
        self.wrong_text = wrong_text
        self.menu_text = menu_text
        self.scrollbox = scrollbox
        self.max_scroll = max_scroll
        self.use_actions = use_actions
        self.buttons: list[Widget] = []

        for id in button_ids:
            w = (
                Widget(id)
                .enable(WidgetFields.get_bounds)
                .enable(
                    WidgetFields.get_actions if use_actions else WidgetFields.get_text,
                )
            )
            self.buttons.append(w)

    def get_widget_info(self) -> list:
        return (
            Widget.get_batch_children(self.buttons)
            if self.get_children
            else Widget.get_batch(self.buttons)
        )

    def is_open(self) -> bool:
        return self.group in client.interfaces.get_open_interfaces()

    def is_right_option(self, w: dict, text: str = "") -> bool:
        if self.use_actions:
            actions = w.get("actions", []) or []
            if not text:
                return any(actions)
            return any(text in a for a in actions if a)
        t = w.get("text", "")
        return (text in t if text else bool(t)) and self.wrong_text not in t

    def _get_scrollbox(self) -> Box | None:
        if not self.scrollbox:
            return None
        widget_info = Widget(self.scrollbox).enable(WidgetFields.get_bounds).get()
        if not widget_info:
            return None
        b = widget_info.get("bounds", [0, 0, 0, 0])
        return Box.from_rect(*b) if b[2] > 0 and b[3] > 0 else None

    def _scroll(self, sb: Box, up: bool = False) -> None:
        sb.hover()
        client.input.mouse.scroll(up=up, count=1)
        timing.sleep(0.1)

    def _find_widget(self, text: str, idx: int) -> dict | None:
        """Find widget by index or text."""
        info = self.get_widget_info()
        if 0 <= idx < len(info):
            w = info[idx]
            return w if not text or self.is_right_option(w, text) else None
        for w in info:
            if self.is_right_option(w, text):
                return w
        return None

    def _make_visible(self, text: str, idx: int, sb: Box | None) -> Box | None:
        """Find option and scroll until visible. Returns clickable Box or None."""
        w = self._find_widget(text, idx)
        if not w:
            return None

        for _ in range(self.max_scroll + 1):
            b = w.get("bounds", [0, 0, 0, 0])
            if b[2] > 0 and b[3] > 0:
                box = Box.from_rect(*b)
                if not sb or sb.contains(box):
                    return box
                self._scroll(sb, up=box.y1 < sb.y1)
            w = self._find_widget(text, idx)
            if not w:
                return None
        return None

    def interact(self, option_text: str = "", index: int = -1) -> bool:
        if not self.is_open():
            return False
        box = self._make_visible(option_text, index, self._get_scrollbox())
        return box.click_option(self.menu_text or option_text) if box else False
