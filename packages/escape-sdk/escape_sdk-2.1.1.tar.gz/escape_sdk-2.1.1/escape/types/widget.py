import typing
from typing import ClassVar, Literal

from escape.globals import get_client

WidgetField = Literal[
    "getActions",
    "getAnimationId",
    "getBorderType",
    "getBounds",
    "getCanvasLocation",
    "getClickMask",
    "getContentType",
    "getDragDeadTime",
    "getDragDeadZone",
    "getDragParent",
    "getFont",
    "getFontId",
    "getHeight",
    "getHeightMode",
    "getId",
    "getIndex",
    "getItemId",
    "getItemQuantity",
    "getItemQuantityMode",
    "getLineHeight",
    "getModelId",
    "getModelType",
    "getModelZoom",
    "getName",
    "getNoClickThrough",
    "getNoScrollThrough",
    "getOnInvTransmitListener",
    "getOnKeyListener",
    "getOnLoadListener",
    "getOnOpListener",
    "getOnVarTransmitListener",
    "getOpacity",
    "getOriginalHeight",
    "getOriginalWidth",
    "getOriginalX",
    "getOriginalY",
    "getParent",
    "getParentId",
    "getRelativeX",
    "getRelativeY",
    "getRotationX",
    "getRotationY",
    "getRotationZ",
    "getScrollHeight",
    "getScrollWidth",
    "getScrollX",
    "getScrollY",
    "getSpriteId",
    "getSpriteTiling",
    "getStaticChildren",
    "getTargetPriority",
    "getTargetVerb",
    "getText",
    "getTextColor",
    "getTextShadowed",
    "getType",
    "getVarTransmitTrigger",
    "getWidth",
    "getWidthMode",
    "getXPositionMode",
    "getXTextAlignment",
    "getYPositionMode",
    "getYTextAlignment",
    "isHidden",
]


class _WidgetFields:
    """Provides autocomplete for widget field names."""

    # snake_case attributes (PEP 8 convention)
    get_actions: WidgetField = "getActions"
    get_animation_id: WidgetField = "getAnimationId"
    get_border_type: WidgetField = "getBorderType"
    get_bounds: WidgetField = "getBounds"
    get_canvas_location: WidgetField = "getCanvasLocation"
    get_click_mask: WidgetField = "getClickMask"
    get_content_type: WidgetField = "getContentType"
    get_drag_dead_time: WidgetField = "getDragDeadTime"
    get_drag_dead_zone: WidgetField = "getDragDeadZone"
    get_drag_parent: WidgetField = "getDragParent"
    get_font: WidgetField = "getFont"
    get_font_id: WidgetField = "getFontId"
    get_height: WidgetField = "getHeight"
    get_height_mode: WidgetField = "getHeightMode"
    get_id: WidgetField = "getId"
    get_index: WidgetField = "getIndex"
    get_item_id: WidgetField = "getItemId"
    get_item_quantity: WidgetField = "getItemQuantity"
    get_item_quantity_mode: WidgetField = "getItemQuantityMode"
    get_line_height: WidgetField = "getLineHeight"
    get_model_id: WidgetField = "getModelId"
    get_model_type: WidgetField = "getModelType"
    get_model_zoom: WidgetField = "getModelZoom"
    get_name: WidgetField = "getName"
    get_no_click_through: WidgetField = "getNoClickThrough"
    get_no_scroll_through: WidgetField = "getNoScrollThrough"
    get_on_inv_transmit_listener: WidgetField = "getOnInvTransmitListener"
    get_on_key_listener: WidgetField = "getOnKeyListener"
    get_on_load_listener: WidgetField = "getOnLoadListener"
    get_on_op_listener: WidgetField = "getOnOpListener"
    get_on_var_transmit_listener: WidgetField = "getOnVarTransmitListener"
    get_opacity: WidgetField = "getOpacity"
    get_original_height: WidgetField = "getOriginalHeight"
    get_original_width: WidgetField = "getOriginalWidth"
    get_original_x: WidgetField = "getOriginalX"
    get_original_y: WidgetField = "getOriginalY"
    get_parent: WidgetField = "getParent"
    get_parent_id: WidgetField = "getParentId"
    get_relative_x: WidgetField = "getRelativeX"
    get_relative_y: WidgetField = "getRelativeY"
    get_rotation_x: WidgetField = "getRotationX"
    get_rotation_y: WidgetField = "getRotationY"
    get_rotation_z: WidgetField = "getRotationZ"
    get_scroll_height: WidgetField = "getScrollHeight"
    get_scroll_width: WidgetField = "getScrollWidth"
    get_scroll_x: WidgetField = "getScrollX"
    get_scroll_y: WidgetField = "getScrollY"
    get_sprite_id: WidgetField = "getSpriteId"
    get_sprite_tiling: WidgetField = "getSpriteTiling"
    get_static_children: WidgetField = "getStaticChildren"
    get_target_priority: WidgetField = "getTargetPriority"
    get_target_verb: WidgetField = "getTargetVerb"
    get_text: WidgetField = "getText"
    get_text_color: WidgetField = "getTextColor"
    get_text_shadowed: WidgetField = "getTextShadowed"
    get_type: WidgetField = "getType"
    get_var_transmit_trigger: WidgetField = "getVarTransmitTrigger"
    get_width: WidgetField = "getWidth"
    get_width_mode: WidgetField = "getWidthMode"
    get_x_position_mode: WidgetField = "getXPositionMode"
    get_x_text_alignment: WidgetField = "getXTextAlignment"
    get_y_position_mode: WidgetField = "getYPositionMode"
    get_y_text_alignment: WidgetField = "getYTextAlignment"
    is_hidden: WidgetField = "isHidden"


# Module-level instance for IDE autocomplete
WidgetFields = _WidgetFields()


class Widget:
    """Python-side mask builder for widget property queries."""

    _FIELDS: ClassVar[list[WidgetField]] = list(typing.get_args(WidgetField))  # keeps exact order
    _FIELD_BITS: ClassVar[dict[str, int]] = {name: 1 << i for i, name in enumerate(_FIELDS)}

    def __init__(self, id):
        self._mask = 0
        self.id = id

    @property
    def mask(self) -> int:
        """Return the combined Java bitmask."""
        return self._mask

    def enable(self, field: WidgetField) -> "Widget":
        """Enable a specific getter flag."""
        self._mask |= self._FIELD_BITS[field]
        return self

    def disable(self, field: WidgetField) -> "Widget":
        """Disable a specific getter flag."""
        self._mask &= ~self._FIELD_BITS[field]
        return self

    def clear(self) -> "Widget":
        """Reset to 0."""
        self._mask = 0
        return self

    def enable_all(self) -> "Widget":
        """Enable all fields."""
        self._mask = (1 << len(self._FIELDS)) - 1
        return self

    @classmethod
    def from_names(cls, widget_id: int, *fields: WidgetField) -> "Widget":
        """Build a mask in one line."""
        w = cls(widget_id)
        for f in fields:
            w.enable(f)
        return w

    def as_dict(self) -> dict[str, bool]:
        """Return {field: enabled?}."""
        return {name: bool(self._mask & bit) for name, bit in self._FIELD_BITS.items()}

    def get(self) -> dict[str, typing.Any]:
        client = get_client()
        result = client.api.invoke_custom_method(
            target="WidgetInspector",
            method="getWidgetProperties",
            signature="(IJ)[B",
            args=[self.id, self.mask],
            async_exec=self.get_async_mode(),
        )

        return result

    def get_child(self, child_index: int) -> dict[str, typing.Any]:
        client = get_client()
        result = client.api.invoke_custom_method(
            target="WidgetInspector",
            method="getWidgetChild",
            signature="(IIJ)[B",
            args=[self.id, child_index, self.mask],
            async_exec=self.get_async_mode(),
        )

        return result

    def get_children(self) -> list[dict[str, typing.Any]]:
        client = get_client()
        result = client.api.invoke_custom_method(
            target="WidgetInspector",
            method="getWidgetChildren",
            signature="(IJ)[B",
            args=[self.id, self.mask],
            async_exec=self.get_async_mode(),
        )

        return result

    def get_children_masked(self, childmask: list[int]) -> list[dict[str, typing.Any]]:
        client = get_client()
        result = client.api.invoke_custom_method(
            target="WidgetInspector",
            method="getWidgetChildrenMasked",
            signature="(I[IJ)[B",
            args=[self.id, childmask, self.mask],
            async_exec=self.get_async_mode(),
        )

        return result

    def get_async_mode(self) -> bool:
        """Return False if mask includes getParent/getParentId (requires sync)."""
        parent_fields = self._FIELD_BITS["getParent"] | self._FIELD_BITS["getParentId"]
        return (self._mask & parent_fields) == 0

    @staticmethod
    def get_batch(widgets: list["Widget"]) -> list[dict[str, typing.Any]]:
        """Get properties for multiple widgets in a single batch request."""
        if not widgets:
            return []

        ids = [w.id for w in widgets]
        masks = [w.mask for w in widgets]

        # Check if any widget has parent fields - if so, use sync mode
        parent_fields = Widget._FIELD_BITS["getParent"] | Widget._FIELD_BITS["getParentId"]
        async_safe = all((w.mask & parent_fields) == 0 for w in widgets)

        client = get_client()
        result = client.api.invoke_custom_method(
            target="WidgetInspector",
            method="getWidgetPropertiesBatch",
            signature="([I[J)[B",
            args=[ids, masks],
            async_exec=async_safe,
        )

        return result if result else []

    @staticmethod
    def get_batch_children(widgets: list["Widget"]) -> list[dict[str, typing.Any]]:
        """Get children properties for multiple widgets in a single batch request."""
        if not widgets:
            return []

        ids = [w.id for w in widgets]
        masks = [w.mask for w in widgets]

        # Check if any widget has parent fields - if so, use sync mode
        parent_fields = Widget._FIELD_BITS["getParent"] | Widget._FIELD_BITS["getParentId"]
        async_safe = all((w.mask & parent_fields) == 0 for w in widgets)

        client = get_client()
        result = client.api.invoke_custom_method(
            target="WidgetInspector",
            method="getWidgetChildrenBatch",
            signature="([I[J)[B",
            args=[ids, masks],
            async_exec=async_safe,
        )

        return result if result else []
