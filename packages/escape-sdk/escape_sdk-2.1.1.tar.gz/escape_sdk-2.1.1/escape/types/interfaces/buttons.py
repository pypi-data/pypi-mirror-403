from escape.types.box import Box
from escape.types.widget import Widget, WidgetFields


class Buttons:
    """Interface class with optional scrollbox support."""

    def __init__(
        self,
        group: int,
        widget_ids: list[int],
        names: list[str],
        can_move: bool = False,
        menu_text: str | None = None,
    ):
        self.group = group
        self.can_move = can_move
        self.menu_text = menu_text
        self.buttons: list[Widget] = []
        self.names = names

        for id in widget_ids:
            w = Widget(id).enable(WidgetFields.get_bounds)
            self.buttons.append(w)

        self.boxes: list[Box | None] = []
        self.is_ready = False

    def get_widget_info(self) -> list:
        return Widget.get_batch(self.buttons)

    def get_button_names(self) -> list[str]:
        return self.names

    def set_boxes(self) -> None:
        info = self.get_widget_info()
        self.boxes = []
        for w in info:
            b = w.get("bounds", [0, 0, 0, 0])
            if b[0] > 0 and b[1] > 0:
                box = Box.from_rect(*b)
                self.boxes.append(box)
            else:
                self.boxes.append(None)
        if all(box is not None for box in self.boxes):
            self.is_ready = True

    def interact(self, button_name: str = "", index: int = -1, menu_option: str = "") -> bool:
        if not self.is_ready or self.can_move:
            self.set_boxes()

        if index >= 0 and index < len(self.boxes):
            box = self.boxes[index]
            if box:
                target_text = self.menu_text if self.menu_text else button_name
                return box.click_option(target_text)
        else:
            for i, box in enumerate(self.boxes):
                if box and ((button_name.lower() in self.names[i].lower()) or menu_option):
                    target_text = self.menu_text if self.menu_text else button_name
                    if menu_option:
                        target_text = menu_option
                    return box.click_option(target_text)
        return False
