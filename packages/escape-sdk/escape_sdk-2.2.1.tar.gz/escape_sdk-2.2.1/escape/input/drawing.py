"""Drawing module - renders shapes directly on RuneLite via Java bridge."""

import numpy as np
from PIL import Image


class Drawing:
    """Drawing utility for rendering debug overlays on RuneLite."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self):
        """Actual initialization, runs once."""
        pass

    def _invoke(self, method: str, signature: str, args: list) -> dict | None:
        """Invoke a method on the Java Drawing class."""
        from escape.client import client

        return client.api.invoke_custom_method(
            target="drawing",
            method=method,
            signature=signature,
            args=args,
            async_exec=True,
            declaring_class="Drawing",
        )

    def add_box(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        argb_color: int,
        filled: bool,
        tag: str | None = None,
    ) -> None:
        """Draw a rectangle at screen coordinates."""
        if tag is None:
            self._invoke(
                "addBox",
                "(IIIIIZ)V",
                [x, y, width, height, argb_color, filled],
            )
        else:
            self._invoke(
                "addBox",
                "(IIIIIZLjava/lang/String;)V",
                [x, y, width, height, argb_color, filled, tag],
            )

    def add_circle(
        self,
        x: int,
        y: int,
        radius: int,
        argb_color: int,
        filled: bool,
        tag: str | None = None,
    ) -> None:
        """Draw a circle at screen coordinates."""
        if tag is None:
            self._invoke(
                "addCircle",
                "(IIIIZ)V",
                [x, y, radius, argb_color, filled],
            )
        else:
            self._invoke(
                "addCircle",
                "(IIIIZLjava/lang/String;)V",
                [x, y, radius, argb_color, filled, tag],
            )

    def add_line(
        self,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        argb_color: int,
        thickness: int,
        tag: str | None = None,
    ) -> None:
        """Draw a line between two points."""
        if tag is None:
            self._invoke(
                "addLine",
                "(IIIIII)V",
                [x1, y1, x2, y2, argb_color, thickness],
            )
        else:
            self._invoke(
                "addLine",
                "(IIIIIILjava/lang/String;)V",
                [x1, y1, x2, y2, argb_color, thickness, tag],
            )

    def add_polygon(
        self,
        x_points: list[int],
        y_points: list[int],
        argb_color: int,
        filled: bool,
        tag: str | None = None,
    ) -> None:
        """Draw a polygon from vertex arrays."""
        if tag is None:
            self._invoke(
                "addPolygon",
                "([I[IIZ)V",
                [x_points, y_points, argb_color, filled],
            )
        else:
            self._invoke(
                "addPolygon",
                "([I[IIZLjava/lang/String;)V",
                [x_points, y_points, argb_color, filled, tag],
            )

    def add_text(
        self,
        text: str,
        x: int,
        y: int,
        argb_color: int,
        font_size: int = 0,
        tag: str | None = None,
    ) -> None:
        """Draw text at screen coordinates."""
        if tag is None and font_size == 0:
            self._invoke(
                "addText",
                "(Ljava/lang/String;III)V",
                [text, x, y, argb_color],
            )
        else:
            self._invoke(
                "addText",
                "(Ljava/lang/String;IIIILjava/lang/String;)V",
                [text, x, y, argb_color, font_size, tag],
            )

    def add_image(
        self,
        argb_pixels: list[int],
        img_width: int,
        img_height: int,
        x: int,
        y: int,
        tag: str | None = None,
    ) -> None:
        """Draw an image from ARGB pixel array."""
        if tag is None:
            self._invoke(
                "addImage",
                "([IIIII)V",
                [argb_pixels, img_width, img_height, x, y],
            )
        else:
            self._invoke(
                "addImage",
                "([IIIIILjava/lang/String;)V",
                [argb_pixels, img_width, img_height, x, y, tag],
            )

    def add_image_from_path(
        self,
        path: str,
        x: int,
        y: int,
        tag: str | None = None,
    ) -> None:
        """Draw an image from a file path."""
        img = Image.open(path).convert("RGBA")
        pixels = np.array(img)

        # Convert RGBA to ARGB int array (0xAARRGGBB)
        argb = (
            (pixels[:, :, 3].astype(np.uint32) << 24)
            | (pixels[:, :, 0].astype(np.uint32) << 16)
            | (pixels[:, :, 1].astype(np.uint32) << 8)
            | pixels[:, :, 2].astype(np.uint32)
        )

        # Convert to signed 32-bit integers (Java expects signed ints)
        argb_signed = argb.astype(np.int32)

        width, height = img.size
        pixel_list = argb_signed.flatten().tolist()

        self.add_image(pixel_list, width, height, x, y, tag)

    def clear(self) -> None:
        """Clear all drawings."""
        self._invoke("clear", "()V", [])

    def clear_tag(self, tag: str) -> None:
        """Clear only drawings with a specific tag."""
        self._invoke("clearTag", "(Ljava/lang/String;)V", [tag])

    def get_count(self) -> int:
        """Get the number of active draw commands."""
        result = self._invoke("getCount", "()I", [])
        if result and "value" in result:
            return result["value"]
        return 0


# Module-level instance
drawing = Drawing()
