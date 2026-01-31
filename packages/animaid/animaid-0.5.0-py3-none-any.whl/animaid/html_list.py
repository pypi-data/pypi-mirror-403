"""HTMLList - A list subclass with HTML rendering capabilities."""

from __future__ import annotations

import html
import uuid
from enum import Enum
from typing import Any, Self

from animaid.css_types import (
    AlignItems,
    BorderValue,
    ColorValue,
    CSSValue,
    JustifyContent,
    SizeValue,
    SpacingValue,
)
from animaid.html_object import HTMLObject


def _to_css(value: object) -> str:
    """Convert a value to its CSS string representation."""
    if hasattr(value, "to_css"):
        return str(value.to_css())
    return str(value)


class ListDirection(Enum):
    """Direction in which list items are rendered."""

    VERTICAL = "vertical"
    HORIZONTAL = "horizontal"
    VERTICAL_REVERSE = "vertical-reverse"
    HORIZONTAL_REVERSE = "horizontal-reverse"
    GRID = "grid"


class ListType(Enum):
    """Type of HTML list structure."""

    UNORDERED = "ul"  # <ul><li>...</li></ul>
    ORDERED = "ol"  # <ol><li>...</li></ol>
    PLAIN = "div"  # <div><div>...</div></div> with flexbox


class HTMLList(HTMLObject, list):
    """A list subclass that renders as styled HTML.

    HTMLList behaves like a regular Python list but includes
    methods for applying CSS styles and rendering to HTML.
    All styling methods modify the object in-place and return self
    for method chaining. Supports vertical, horizontal, and grid layouts.

    Examples:
        >>> items = HTMLList(["Apple", "Banana", "Cherry"])
        >>> items.render()
        '<ul><li>Apple</li><li>Banana</li><li>Cherry</li></ul>'

        >>> items.horizontal().gap("10px").render()
        '<div style="display: flex; flex-direction: row; gap: 10px">...</div>'

        >>> HTMLList([1, 2, 3]).ordered().render()
        '<ol><li>1</li><li>2</li><li>3</li></ol>'
    """

    _styles: dict[str, str]
    _item_styles: dict[str, str]
    _css_classes: list[str]
    _item_classes: list[str]
    _direction: ListDirection
    _list_type: ListType
    _grid_columns: int | None
    _separator: str | None
    _obs_id: str

    def __init__(
        self, items: list[Any] | None = None, **styles: str | CSSValue
    ) -> None:
        """Initialize an HTMLList.

        Args:
            items: Initial list items.
            **styles: CSS styles for the container (underscores to hyphens).
                      Accepts both strings and CSS type objects (Color, Size, etc.)
        """
        super().__init__(items or [])
        self._styles = {}
        self._item_styles = {}
        self._css_classes = []
        self._item_classes = []
        self._direction = ListDirection.VERTICAL
        self._list_type = ListType.UNORDERED
        self._grid_columns = None
        self._separator = None
        self._obs_id = str(uuid.uuid4())

        for key, value in styles.items():
            css_key = key.replace("_", "-")
            self._styles[css_key] = _to_css(value)

    def _notify(self) -> None:
        """Publish change notification via pypubsub."""
        try:
            from pubsub import pub

            pub.sendMessage("animaid.changed", obs_id=self._obs_id)
        except ImportError:
            pass  # pypubsub not installed

    def _copy_with_settings(
        self,
        new_styles: dict[str, str] | None = None,
        new_item_styles: dict[str, str] | None = None,
        new_classes: list[str] | None = None,
        new_item_classes: list[str] | None = None,
        new_direction: ListDirection | None = None,
        new_list_type: ListType | None = None,
        new_grid_columns: int | None = None,
        new_separator: str | None = None,
    ) -> Self:
        """Create a copy with modified settings.

        This method is used internally for operations that must return
        a new object (like slicing or concatenation).

        Args:
            new_styles: Container styles to merge.
            new_item_styles: Item styles to merge.
            new_classes: Classes to add to container.
            new_item_classes: Classes to add to items.
            new_direction: New layout direction.
            new_list_type: New list type.
            new_grid_columns: Grid column count.
            new_separator: Separator style between items.

        Returns:
            A new HTMLList with combined settings.
        """
        result = HTMLList(list(self))
        result._styles = self._styles.copy()
        result._item_styles = self._item_styles.copy()
        result._css_classes = self._css_classes.copy()
        result._item_classes = self._item_classes.copy()
        result._direction = self._direction
        result._list_type = self._list_type
        result._grid_columns = self._grid_columns
        result._separator = self._separator
        result._obs_id = self._obs_id  # Preserve ID so updates still work

        if new_styles:
            result._styles.update(new_styles)
        if new_item_styles:
            result._item_styles.update(new_item_styles)
        if new_classes:
            result._css_classes.extend(new_classes)
        if new_item_classes:
            result._item_classes.extend(new_item_classes)
        if new_direction is not None:
            result._direction = new_direction
        if new_list_type is not None:
            result._list_type = new_list_type
        if new_grid_columns is not None:
            result._grid_columns = new_grid_columns
        if new_separator is not None:
            result._separator = new_separator

        return result  # type: ignore[return-value]

    # -------------------------------------------------------------------------
    # HTMLObject interface
    # -------------------------------------------------------------------------

    def styled(self, **styles: str | CSSValue) -> Self:
        """Apply additional container styles in-place.

        Args:
            **styles: CSS property-value pairs for the container.
                      Accepts both strings and CSS type objects (Color, Size, etc.)

        Returns:
            Self for method chaining.
        """
        for key, value in styles.items():
            css_key = key.replace("_", "-")
            self._styles[css_key] = _to_css(value)
        self._notify()
        return self

    def add_class(self, *class_names: str) -> Self:
        """Add CSS classes on the container in-place.

        Args:
            *class_names: CSS class names to add.

        Returns:
            Self for method chaining.
        """
        self._css_classes.extend(class_names)
        self._notify()
        return self

    # -------------------------------------------------------------------------
    # Direction methods
    # -------------------------------------------------------------------------

    def vertical(self) -> Self:
        """Apply vertical layout (default) in-place.

        Items are stacked top to bottom.
        """
        self._direction = ListDirection.VERTICAL
        self._notify()
        return self

    def horizontal(self) -> Self:
        """Apply horizontal layout in-place.

        Items are arranged left to right using flexbox.
        """
        self._direction = ListDirection.HORIZONTAL
        self._list_type = ListType.PLAIN
        self._notify()
        return self

    def vertical_reverse(self) -> Self:
        """Apply reversed vertical layout in-place.

        Items are stacked bottom to top.
        """
        self._direction = ListDirection.VERTICAL_REVERSE
        self._list_type = ListType.PLAIN
        self._notify()
        return self

    def horizontal_reverse(self) -> Self:
        """Apply reversed horizontal layout in-place.

        Items are arranged right to left.
        """
        self._direction = ListDirection.HORIZONTAL_REVERSE
        self._list_type = ListType.PLAIN
        self._notify()
        return self

    def grid(self, columns: int = 3) -> Self:
        """Apply CSS grid layout in-place.

        Args:
            columns: Number of columns in the grid.

        Returns:
            Self for method chaining.
        """
        self._direction = ListDirection.GRID
        self._list_type = ListType.PLAIN
        self._grid_columns = columns
        self._notify()
        return self

    # -------------------------------------------------------------------------
    # List type methods
    # -------------------------------------------------------------------------

    def ordered(self) -> Self:
        """Apply ordered list (<ol>) format in-place."""
        self._list_type = ListType.ORDERED
        self._notify()
        return self

    def unordered(self) -> Self:
        """Apply unordered list (<ul>) format in-place."""
        self._list_type = ListType.UNORDERED
        self._notify()
        return self

    def plain(self) -> Self:
        """Apply plain div container (no bullets/numbers) in-place."""
        self._list_type = ListType.PLAIN
        self._notify()
        return self

    # -------------------------------------------------------------------------
    # Spacing methods
    # -------------------------------------------------------------------------

    def gap(self, value: SizeValue) -> Self:
        """Apply specified gap between items in-place.

        Args:
            value: CSS gap value (e.g., "10px", Size.px(10), Size.rem(1)).
        """
        self._styles["gap"] = _to_css(value)
        self._notify()
        return self

    def padding(self, value: SpacingValue) -> Self:
        """Apply padding inside the container in-place.

        Args:
            value: CSS padding value (e.g., "10px", Size.px(10)).
        """
        self._styles["padding"] = _to_css(value)
        self._notify()
        return self

    def margin(self, value: SpacingValue) -> Self:
        """Apply margin outside the container in-place.

        Args:
            value: CSS margin value (e.g., "10px", Size.px(10), Spacing.all(10)).
        """
        self._styles["margin"] = _to_css(value)
        self._notify()
        return self

    def item_padding(self, value: SpacingValue) -> Self:
        """Apply padding inside each item in-place.

        Args:
            value: CSS padding value for items.
        """
        self._item_styles["padding"] = _to_css(value)
        self._notify()
        return self

    def item_margin(self, value: SpacingValue) -> Self:
        """Apply margin around each item in-place.

        Args:
            value: CSS margin value for items.
        """
        self._item_styles["margin"] = _to_css(value)
        self._notify()
        return self

    # -------------------------------------------------------------------------
    # Border methods
    # -------------------------------------------------------------------------

    def border(self, value: BorderValue) -> Self:
        """Apply border around the container in-place.

        Args:
            value: CSS border value (e.g., "1px solid black", Border.solid()).
        """
        self._styles["border"] = _to_css(value)
        self._notify()
        return self

    def border_radius(self, value: SizeValue) -> Self:
        """Apply rounded corners on the container in-place.

        Args:
            value: CSS border-radius value (e.g., "5px", Size.px(5)).
        """
        self._styles["border-radius"] = _to_css(value)
        self._notify()
        return self

    def item_border(self, value: BorderValue) -> Self:
        """Apply border around each item in-place.

        Args:
            value: CSS border value for items.
        """
        self._item_styles["border"] = _to_css(value)
        self._notify()
        return self

    def item_border_radius(self, value: SizeValue) -> Self:
        """Apply rounded corners on each item in-place.

        Args:
            value: CSS border-radius value for items.
        """
        self._item_styles["border-radius"] = _to_css(value)
        self._notify()
        return self

    def separator(self, value: BorderValue) -> Self:
        """Apply separator lines between items in-place.

        Unlike item_border, this only adds borders between items,
        not on the outer edges.

        Args:
            value: CSS border value for separators.
        """
        self._separator = _to_css(value)
        self._notify()
        return self

    # -------------------------------------------------------------------------
    # Background and color methods
    # -------------------------------------------------------------------------

    def background(self, value: ColorValue) -> Self:
        """Apply background color on the container in-place.

        Args:
            value: CSS color value (e.g., "white", Color.white, Color.hex("#fff")).
        """
        self._styles["background-color"] = _to_css(value)
        self._notify()
        return self

    def item_background(self, value: ColorValue) -> Self:
        """Apply background color on each item in-place.

        Args:
            value: CSS color value.
        """
        self._item_styles["background-color"] = _to_css(value)
        self._notify()
        return self

    def color(self, value: ColorValue) -> Self:
        """Apply text color in-place.

        Args:
            value: CSS color value (e.g., "black", Color.black).
        """
        self._styles["color"] = _to_css(value)
        self._notify()
        return self

    # -------------------------------------------------------------------------
    # Item class methods
    # -------------------------------------------------------------------------

    def add_item_class(self, *class_names: str) -> Self:
        """Add CSS classes to each item in-place.

        Args:
            *class_names: CSS class names to add to items.
        """
        self._item_classes.extend(class_names)
        self._notify()
        return self

    # -------------------------------------------------------------------------
    # Alignment methods
    # -------------------------------------------------------------------------

    def align_items(self, value: AlignItems | str) -> Self:
        """Apply specified cross-axis alignment in-place.

        Args:
            value: CSS align-items value (e.g., "center", AlignItems.CENTER).
        """
        self._styles["align-items"] = _to_css(value)
        self._notify()
        return self

    def justify_content(self, value: JustifyContent | str) -> Self:
        """Apply specified main-axis alignment in-place.

        Args:
            value: CSS justify-content value (e.g., "space-between").
        """
        self._styles["justify-content"] = _to_css(value)
        self._notify()
        return self

    def center(self) -> Self:
        """Apply centered alignment on both axes in-place."""
        self._styles["align-items"] = "center"
        self._styles["justify-content"] = "center"
        self._notify()
        return self

    # -------------------------------------------------------------------------
    # Size methods
    # -------------------------------------------------------------------------

    def width(self, value: SizeValue) -> Self:
        """Apply specified width in-place.

        Args:
            value: CSS width value (e.g., "100px", Size.px(100), Size.percent(50)).
        """
        self._styles["width"] = _to_css(value)
        self._notify()
        return self

    def height(self, value: SizeValue) -> Self:
        """Apply specified height in-place.

        Args:
            value: CSS height value (e.g., "200px", Size.px(200), Size.vh(100)).
        """
        self._styles["height"] = _to_css(value)
        self._notify()
        return self

    def max_width(self, value: SizeValue) -> Self:
        """Apply maximum width constraint in-place.

        Args:
            value: CSS max-width value (e.g., "800px", Size.px(800)).
        """
        self._styles["max-width"] = _to_css(value)
        self._notify()
        return self

    # -------------------------------------------------------------------------
    # Style Presets (beginner-friendly)
    # -------------------------------------------------------------------------

    def cards(self) -> Self:
        """Apply card list style with shadows and spacing in-place.

        Creates a visually appealing list where each item looks like a card.
        """
        self._list_type = ListType.PLAIN
        self._direction = ListDirection.HORIZONTAL
        self._styles["gap"] = "16px"
        self._styles["flex-wrap"] = "wrap"
        self._item_styles["padding"] = "16px"
        self._item_styles["border"] = "1px solid #e0e0e0"
        self._item_styles["border-radius"] = "8px"
        self._item_styles["background-color"] = "white"
        self._notify()
        return self

    def pills(self) -> Self:
        """Apply pill/badge style in-place.

        Creates a horizontal list of pill-shaped items.
        """
        self._list_type = ListType.PLAIN
        self._direction = ListDirection.HORIZONTAL
        self._styles["gap"] = "8px"
        self._styles["flex-wrap"] = "wrap"
        self._item_styles["padding"] = "6px 14px"
        self._item_styles["border-radius"] = "20px"
        self._item_styles["background-color"] = "#e0e0e0"
        self._notify()
        return self

    def tags(self) -> Self:
        """Apply tags/labels style in-place.

        Creates a horizontal list of tag-style items.
        """
        self._list_type = ListType.PLAIN
        self._direction = ListDirection.HORIZONTAL
        self._styles["gap"] = "8px"
        self._styles["flex-wrap"] = "wrap"
        self._item_styles["padding"] = "4px 10px"
        self._item_styles["background-color"] = "#f5f5f5"
        self._item_styles["border-radius"] = "4px"
        self._notify()
        return self

    def menu(self) -> Self:
        """Apply vertical menu style in-place.

        Creates a clean vertical menu suitable for navigation.
        """
        self._list_type = ListType.PLAIN
        self._direction = ListDirection.VERTICAL
        self._item_styles["padding"] = "12px 16px"
        self._separator = "1px solid #e0e0e0"
        self._notify()
        return self

    def inline(self) -> Self:
        """Apply inline style in-place.

        Creates a simple inline list separated by spacing.
        """
        self._list_type = ListType.PLAIN
        self._direction = ListDirection.HORIZONTAL
        self._styles["gap"] = "8px"
        self._styles["flex-wrap"] = "wrap"
        self._notify()
        return self

    def numbered(self) -> Self:
        """Apply numbered list style in-place."""
        self._list_type = ListType.ORDERED
        self._styles["padding-left"] = "24px"
        self._item_styles["padding"] = "4px 0"
        self._notify()
        return self

    def bulleted(self) -> Self:
        """Apply bulleted list style in-place."""
        self._list_type = ListType.UNORDERED
        self._styles["padding-left"] = "24px"
        self._item_styles["padding"] = "4px 0"
        self._notify()
        return self

    def spaced(self) -> Self:
        """Apply generous spacing style in-place."""
        self._styles["gap"] = "16px"
        self._item_styles["padding"] = "8px"
        self._notify()
        return self

    def compact(self) -> Self:
        """Apply minimal spacing style in-place."""
        self._styles["gap"] = "4px"
        self._item_styles["padding"] = "2px"
        self._notify()
        return self

    # -------------------------------------------------------------------------
    # Rendering
    # -------------------------------------------------------------------------

    def _render_item(self, item: Any) -> str:
        """Render a single item to HTML.

        Args:
            item: The item to render.

        Returns:
            HTML string for the item.
        """
        if isinstance(item, HTMLObject):
            return item.render()
        elif isinstance(item, str):
            return html.escape(item)
        else:
            return html.escape(str(item))

    def _get_container_styles(self) -> dict[str, str]:
        """Build the complete container styles including layout."""
        styles = self._styles.copy()

        # Add layout-specific styles
        if self._list_type == ListType.PLAIN:
            if self._direction == ListDirection.HORIZONTAL:
                styles.setdefault("display", "flex")
                styles.setdefault("flex-direction", "row")
                styles.setdefault("flex-wrap", "wrap")
            elif self._direction == ListDirection.HORIZONTAL_REVERSE:
                styles.setdefault("display", "flex")
                styles.setdefault("flex-direction", "row-reverse")
                styles.setdefault("flex-wrap", "wrap")
            elif self._direction == ListDirection.VERTICAL:
                styles.setdefault("display", "flex")
                styles.setdefault("flex-direction", "column")
            elif self._direction == ListDirection.VERTICAL_REVERSE:
                styles.setdefault("display", "flex")
                styles.setdefault("flex-direction", "column-reverse")
            elif self._direction == ListDirection.GRID:
                styles.setdefault("display", "grid")
                cols = self._grid_columns or 3
                styles.setdefault("grid-template-columns", f"repeat({cols}, 1fr)")

        # Remove list styling for ul/ol if needed
        if self._list_type in (ListType.UNORDERED, ListType.ORDERED):
            if self._direction != ListDirection.VERTICAL:
                styles.setdefault("display", "flex")
                styles.setdefault("list-style", "none")
                styles.setdefault("padding-left", "0")
                if self._direction == ListDirection.HORIZONTAL:
                    styles.setdefault("flex-direction", "row")
                elif self._direction == ListDirection.HORIZONTAL_REVERSE:
                    styles.setdefault("flex-direction", "row-reverse")

        return styles

    def _build_item_style_string(self, index: int, total: int) -> str:
        """Build style string for an item, including separators.

        Args:
            index: Item index (0-based).
            total: Total number of items.

        Returns:
            CSS style attribute value.
        """
        styles = self._item_styles.copy()

        # Add separator styles
        if self._separator:
            is_horizontal = self._direction in (
                ListDirection.HORIZONTAL,
                ListDirection.HORIZONTAL_REVERSE,
            )
            is_last = index == total - 1

            if not is_last:
                if is_horizontal:
                    styles["border-right"] = self._separator
                else:
                    styles["border-bottom"] = self._separator

        if not styles:
            return ""
        return "; ".join(f"{k}: {v}" for k, v in styles.items())

    def _build_item_attributes(self, index: int, total: int) -> str:
        """Build complete attribute string for an item."""
        parts = []

        if self._item_classes:
            class_str = " ".join(self._item_classes)
            parts.append(f'class="{class_str}"')

        style_str = self._build_item_style_string(index, total)
        if style_str:
            parts.append(f'style="{style_str}"')

        return " ".join(parts)

    def render(self) -> str:
        """Return HTML representation of this list.

        Returns:
            A string containing valid HTML.
        """
        if len(self) == 0:
            # Empty list
            container_tag = self._list_type.value
            attrs = self._build_attributes()
            if attrs:
                return f"<{container_tag} {attrs}></{container_tag}>"
            return f"<{container_tag}></{container_tag}>"

        # Build container styles
        container_styles = self._get_container_styles()
        self._styles = container_styles

        # Determine tags
        container_tag = self._list_type.value
        uses_list_item = self._list_type in (ListType.UNORDERED, ListType.ORDERED)
        item_tag = "li" if uses_list_item else "div"

        # Build container opening tag
        attrs = self._build_attributes()
        if attrs:
            container_open = f"<{container_tag} {attrs}>"
        else:
            container_open = f"<{container_tag}>"

        # Render items
        total = len(self)
        items_html = []
        for i, item in enumerate(self):
            item_content = self._render_item(item)
            item_attrs = self._build_item_attributes(i, total)
            if item_attrs:
                tag_html = f"<{item_tag} {item_attrs}>{item_content}</{item_tag}>"
                items_html.append(tag_html)
            else:
                items_html.append(f"<{item_tag}>{item_content}</{item_tag}>")

        return f"{container_open}{''.join(items_html)}</{container_tag}>"

    # -------------------------------------------------------------------------
    # List operation overrides
    # -------------------------------------------------------------------------

    def __add__(self, other: list[Any]) -> Self:
        """Concatenate lists, preserving settings."""
        result = HTMLList(list.__add__(self, other))
        result._styles = self._styles.copy()
        result._item_styles = self._item_styles.copy()
        result._css_classes = self._css_classes.copy()
        result._item_classes = self._item_classes.copy()
        result._direction = self._direction
        result._list_type = self._list_type
        result._grid_columns = self._grid_columns
        result._separator = self._separator
        result._obs_id = self._obs_id
        return result  # type: ignore[return-value]

    def __getitem__(self, key: Any) -> Any:
        """Get item or slice.

        Single index returns the item itself.
        Slice returns a new HTMLList with settings preserved.
        """
        result = list.__getitem__(self, key)
        if isinstance(key, slice):
            new_list = HTMLList(result)
            new_list._styles = self._styles.copy()
            new_list._item_styles = self._item_styles.copy()
            new_list._css_classes = self._css_classes.copy()
            new_list._item_classes = self._item_classes.copy()
            new_list._direction = self._direction
            new_list._list_type = self._list_type
            new_list._grid_columns = self._grid_columns
            new_list._separator = self._separator
            new_list._obs_id = self._obs_id
            return new_list
        return result

    def __setitem__(self, key: Any, value: Any) -> None:
        """Set item, notifying observers."""
        super().__setitem__(key, value)
        self._notify()

    def __delitem__(self, key: Any) -> None:
        """Delete item, notifying observers."""
        super().__delitem__(key)
        self._notify()

    def append(self, item: Any) -> None:
        """Append item, notifying observers."""
        super().append(item)
        self._notify()

    def extend(self, items: Any) -> None:
        """Extend list, notifying observers."""
        super().extend(items)
        self._notify()

    def insert(self, index: Any, item: Any) -> None:
        """Insert item, notifying observers."""
        super().insert(index, item)
        self._notify()

    def remove(self, item: Any) -> None:
        """Remove item, notifying observers."""
        super().remove(item)
        self._notify()

    def pop(self, index: Any = -1) -> Any:
        """Pop item, notifying observers."""
        result = super().pop(index)
        self._notify()
        return result

    def clear(self) -> None:
        """Clear list, notifying observers."""
        super().clear()
        self._notify()

    def sort(self, *, key: Any = None, reverse: bool = False) -> None:
        """Sort list, notifying observers."""
        super().sort(key=key, reverse=reverse)
        self._notify()

    def reverse(self) -> None:
        """Reverse list, notifying observers."""
        super().reverse()
        self._notify()

    def __repr__(self) -> str:
        """Return a detailed representation for debugging."""
        items_repr = list.__repr__(self)
        extras = []
        if self._direction != ListDirection.VERTICAL:
            extras.append(f"direction={self._direction.value}")
        if self._list_type != ListType.UNORDERED:
            extras.append(f"type={self._list_type.value}")
        if self._styles:
            extras.append(f"styles={self._styles}")

        if extras:
            return f"HTMLList({items_repr}, {', '.join(extras)})"
        return f"HTMLList({items_repr})"
