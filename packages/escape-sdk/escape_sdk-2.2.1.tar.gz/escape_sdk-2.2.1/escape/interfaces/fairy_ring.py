from escape._internal.logger import logger
from escape.client import client
from escape.types.box import Box
from escape.types.widget import Widget, WidgetFields
from escape.utilities.timing import wait_until


class FairyRingInterface:
    """Interface for the Fairy Ring transportation system."""

    def __init__(self):
        self.group = client.interface_id.FAIRYRINGS
        self.abcd_button = Widget(client.interface_id.Fairyrings.ROOT_MODEL3).enable(
            WidgetFields.get_rotation_y
        )
        self.ijlk_button = Widget(client.interface_id.Fairyrings.ROOT_MODEL4).enable(
            WidgetFields.get_rotation_y
        )
        self.pqrs_button = Widget(client.interface_id.Fairyrings.ROOT_MODEL5).enable(
            WidgetFields.get_rotation_y
        )

        self.abcd_clockwise = Widget(client.interface_id.Fairyrings._1_CLOCKWISE).enable(
            WidgetFields.get_bounds
        )
        self.ijlk_clockwise = Widget(client.interface_id.Fairyrings._2_CLOCKWISE).enable(
            WidgetFields.get_bounds
        )
        self.pqrs_clockwise = Widget(client.interface_id.Fairyrings._3_CLOCKWISE).enable(
            WidgetFields.get_bounds
        )

        self.abcd_anti_clockwise = Widget(client.interface_id.Fairyrings._1_ANTICLOCKWISE).enable(
            WidgetFields.get_bounds
        )
        self.ijlk_anti_clockwise = Widget(client.interface_id.Fairyrings._2_ANTICLOCKWISE).enable(
            WidgetFields.get_bounds
        )
        self.pqrs_anti_clockwise = Widget(client.interface_id.Fairyrings._3_ANTICLOCKWISE).enable(
            WidgetFields.get_bounds
        )

        self.destination_button = Widget(client.interface_id.Fairyrings.CONFIRM).enable(
            WidgetFields.get_bounds
        )

        self.buttons = [
            self.abcd_button,
            self.ijlk_button,
            self.pqrs_button,
            self.abcd_clockwise,
            self.ijlk_clockwise,
            self.pqrs_clockwise,
            self.abcd_anti_clockwise,
            self.ijlk_anti_clockwise,
            self.pqrs_anti_clockwise,
            self.destination_button,
        ]

        self.letter_strings = ["ABCD", "IJKL", "PQRS"]

        self.cached_info = {}

    def _rotation_to_letter(self, rotation_y: int, index: int) -> str:
        letters = self.letter_strings[index]
        if rotation_y == 0:
            return letters[0]
        elif rotation_y == 512:
            return letters[1]
        elif rotation_y == 1024:
            return letters[2]
        elif rotation_y == 1536:
            return letters[3]
        return "Z"

    def _get_all_info(self) -> list[dict]:
        return Widget.get_batch(self.buttons)

    def get_current_code(self) -> str:
        info = self.cached_info
        code = ""
        for i in range(3):
            rotation_y = info[i].get("rotationY", -1)
            code += self._rotation_to_letter(rotation_y, i)
        return code

    def _from_letter_to_letter(self, letter: str, target: str) -> int:
        """
        Find most efficient way to go from letter to letter target.

        positive is clockwise, negative is anti-clockwise.

        A + clockwise -> D
        """
        for i in range(3):
            letters = self.letter_strings[i]
            if letter in letters and target in letters:
                break
        current_index = letters.index(letter)
        target_index = letters.index(target)

        anticlockwise_steps = (target_index - current_index) % 4
        clockwise_steps = (current_index - target_index) % 4

        return clockwise_steps if clockwise_steps <= anticlockwise_steps else -anticlockwise_steps

    def _check_index_to_target(self, index: int, target: str) -> bool:
        self.cached_info = self._get_all_info()
        current_code = self.get_current_code()
        return current_code[index] == target

    def _next_letter(self, letter: str, clockwise: bool, index: int) -> str:
        letters = self.letter_strings[index]
        current_index = letters.index(letter)
        next_index = (current_index - 1) % 4 if clockwise else (current_index + 1) % 4
        return letters[next_index]

    def _rotate_to_sequence(self, target_code: str) -> bool:
        all_info = self.cached_info
        current_code = self.get_current_code()
        logger.info(f"Current code: {current_code}, Target code: {target_code}")
        if "Z" in current_code:
            logger.error("Error: Invalid current code detected")
            return False

        for i in range(3):
            current_letter = current_code[i]
            target_letter = target_code[i]
            steps = self._from_letter_to_letter(current_letter, target_letter)
            for _ in range(abs(steps)):
                current_letter = self.get_current_code()[i]
                if steps > 0:
                    button = all_info[i + 3].get(
                        "bounds", [0, 0, 0, 0]
                    )  # Clockwise buttons are at index 3,4,5
                    next_letter = self._next_letter(current_letter, True, i)
                else:
                    button = all_info[i + 6].get(
                        "bounds", [0, 0, 0, 0]
                    )  # Anti-clockwise buttons are at index 6,7,8
                    next_letter = self._next_letter(current_letter, False, i)
                box = Box.from_rect(*button)
                s = "Rotate clockwise" if steps > 0 else "Rotate counter-clockwise"
                if box.click_option(s):
                    wait_until(
                        lambda i=i, nl=next_letter: self._check_index_to_target(i, nl), timeout=5
                    )
                else:
                    return False
        self.cached_info = self._get_all_info()
        return self.get_current_code() == target_code

    def interact(self, target_code: str) -> bool:
        """Dial a fairy ring code and confirm teleport."""
        self.cached_info = self._get_all_info()
        if self._rotate_to_sequence(target_code):
            dest_button_bounds = self.cached_info[9].get("bounds", [0, 0, 0, 0])
            box = Box.from_rect(*dest_button_bounds)
            box.click_option("Confirm")
            return True
        return False


fairy_ring = FairyRingInterface()
