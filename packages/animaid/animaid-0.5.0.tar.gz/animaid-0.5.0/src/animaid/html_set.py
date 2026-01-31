"""HTMLSet - A set subclass with HTML rendering capabilities."""

from __future__ import annotations

import html
import uuid
from collections.abc import Iterable
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


class SetDirection(Enum):
    """Direction in which set items are rendered."""

    VERTICAL = "vertical"
    HORIZONTAL = "horizontal"
    VERTICAL_REVERSE = "vertical-reverse"
    HORIZONTAL_REVERSE = "horizontal-reverse"
    GRID = "grid"


class SetFormat(Enum):
    """Format for displaying set items."""

    PLAIN = "plain"  # Just items in divs
    BRACES = "braces"  # {a, b, c} style


class HTMLSet(HTMLObject, set):
    """A set subclass that renders as styled HTML.

    HTMLSet behaves like a regular Python set but includes
    methods for applying CSS styles and rendering to HTML.
    All styling methods modify the object in-place and return self
    for method chaining. Items are automatically deduplicated (set behavior).
    Mutations trigger notifications for reactive updates.

    Examples:
        >>> s = HTMLSet({1, 2, 3})
        >>> s.render()
        '<span>{1, 2, 3}</span>'

        >>> s.horizontal().pills().render()
        '<div style="display: flex; ...">...</div>'

        >>> HTMLSet([1, 1, 2, 2, 3])  # Duplicates removed
        HTMLSet({1, 2, 3})
    """

    _styles: dict[str, str]
    _item_styles: dict[str, str]
    _css_classes: list[str]
    _item_classes: list[str]
    _direction: SetDirection
    _format: SetFormat
    _grid_columns: int | None
    _separator: str | None
    _sorted: bool
    _obs_id: str

    def __init__(self, items: Iterable[Any] = (), **styles: str | CSSValue) -> None:
        """Initialize an HTMLSet.

        Args:
            items: The set items (any iterable, duplicates removed).
            **styles: CSS styles for the container.
        """
        super().__init__(items)
        self._styles = {}
        self._item_styles = {}
        self._css_classes = []
        self._item_classes = []
        self._direction = SetDirection.HORIZONTAL
        self._format = SetFormat.BRACES
        self._grid_columns = None
        self._separator = None
        self._sorted = False
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
        new_direction: SetDirection | None = None,
        new_format: SetFormat | None = None,
        new_grid_columns: int | None = None,
        new_separator: str | None = None,
        new_sorted: bool | None = None,
    ) -> Self:
        """Create a copy with modified settings.

        This method is used internally for operations that must return
        a new object (like set operations that return new sets).
        """
        result = HTMLSet(self)
        result._styles = self._styles.copy()
        result._item_styles = self._item_styles.copy()
        result._css_classes = self._css_classes.copy()
        result._item_classes = self._item_classes.copy()
        result._direction = self._direction
        result._format = self._format
        result._grid_columns = self._grid_columns
        result._separator = self._separator
        result._sorted = self._sorted
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
        if new_format is not None:
            result._format = new_format
        if new_grid_columns is not None:
            result._grid_columns = new_grid_columns
        if new_separator is not None:
            result._separator = new_separator
        if new_sorted is not None:
            result._sorted = new_sorted

        return result  # type: ignore[return-value]

    # -------------------------------------------------------------------------
    # HTMLObject interface
    # -------------------------------------------------------------------------

    def styled(self, **styles: str | CSSValue) -> Self:
        """Apply additional container styles in-place.

        Args:
            **styles: CSS property-value pairs for the container.

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
    # Format methods
    # -------------------------------------------------------------------------

    def plain(self) -> Self:
        """Apply plain format (without brace decoration) in-place."""
        self._format = SetFormat.PLAIN
        self._notify()
        return self

    def braces(self) -> Self:
        """Apply braces format (default) in-place."""
        self._format = SetFormat.BRACES
        self._notify()
        return self

    # -------------------------------------------------------------------------
    # Ordering methods
    # -------------------------------------------------------------------------

    def sorted(self) -> Self:
        """Apply sorted rendering order in-place."""
        self._sorted = True
        self._notify()
        return self

    def unsorted(self) -> Self:
        """Apply iteration order (no sorting) in-place."""
        self._sorted = False
        self._notify()
        return self

    # -------------------------------------------------------------------------
    # Direction methods
    # -------------------------------------------------------------------------

    def vertical(self) -> Self:
        """Apply vertical layout in-place."""
        self._direction = SetDirection.VERTICAL
        self._notify()
        return self

    def horizontal(self) -> Self:
        """Apply horizontal layout (default) in-place."""
        self._direction = SetDirection.HORIZONTAL
        self._notify()
        return self

    def vertical_reverse(self) -> Self:
        """Apply reversed vertical layout in-place."""
        self._direction = SetDirection.VERTICAL_REVERSE
        self._notify()
        return self

    def horizontal_reverse(self) -> Self:
        """Apply reversed horizontal layout in-place."""
        self._direction = SetDirection.HORIZONTAL_REVERSE
        self._notify()
        return self

    def grid(self, columns: int = 3) -> Self:
        """Apply CSS grid layout in-place.

        Args:
            columns: Number of columns in the grid.
        """
        self._direction = SetDirection.GRID
        self._grid_columns = columns
        self._notify()
        return self

    # -------------------------------------------------------------------------
    # Spacing methods
    # -------------------------------------------------------------------------

    def gap(self, value: SizeValue) -> Self:
        """Apply specified gap between items in-place."""
        self._styles["gap"] = _to_css(value)
        self._notify()
        return self

    def padding(self, value: SpacingValue) -> Self:
        """Apply padding inside the container in-place."""
        self._styles["padding"] = _to_css(value)
        self._notify()
        return self

    def margin(self, value: SpacingValue) -> Self:
        """Apply margin outside the container in-place."""
        self._styles["margin"] = _to_css(value)
        self._notify()
        return self

    def item_padding(self, value: SpacingValue) -> Self:
        """Apply padding inside each item in-place."""
        self._item_styles["padding"] = _to_css(value)
        self._notify()
        return self

    def item_margin(self, value: SpacingValue) -> Self:
        """Apply margin around each item in-place."""
        self._item_styles["margin"] = _to_css(value)
        self._notify()
        return self

    # -------------------------------------------------------------------------
    # Border methods
    # -------------------------------------------------------------------------

    def border(self, value: BorderValue) -> Self:
        """Apply border around the container in-place."""
        self._styles["border"] = _to_css(value)
        self._notify()
        return self

    def border_radius(self, value: SizeValue) -> Self:
        """Apply rounded corners on the container in-place."""
        self._styles["border-radius"] = _to_css(value)
        self._notify()
        return self

    def item_border(self, value: BorderValue) -> Self:
        """Apply border around each item in-place."""
        self._item_styles["border"] = _to_css(value)
        self._notify()
        return self

    def item_border_radius(self, value: SizeValue) -> Self:
        """Apply rounded corners on each item in-place."""
        self._item_styles["border-radius"] = _to_css(value)
        self._notify()
        return self

    def separator(self, value: BorderValue) -> Self:
        """Apply separator lines between items in-place."""
        self._separator = _to_css(value)
        self._notify()
        return self

    # -------------------------------------------------------------------------
    # Background and color methods
    # -------------------------------------------------------------------------

    def background(self, value: ColorValue) -> Self:
        """Apply background color on the container in-place."""
        self._styles["background-color"] = _to_css(value)
        self._notify()
        return self

    def item_background(self, value: ColorValue) -> Self:
        """Apply background color on each item in-place."""
        self._item_styles["background-color"] = _to_css(value)
        self._notify()
        return self

    def color(self, value: ColorValue) -> Self:
        """Apply text color in-place."""
        self._styles["color"] = _to_css(value)
        self._notify()
        return self

    # -------------------------------------------------------------------------
    # Item class methods
    # -------------------------------------------------------------------------

    def add_item_class(self, *class_names: str) -> Self:
        """Add CSS classes to each item in-place."""
        self._item_classes.extend(class_names)
        self._notify()
        return self

    # -------------------------------------------------------------------------
    # Alignment methods
    # -------------------------------------------------------------------------

    def align_items(self, value: AlignItems | str) -> Self:
        """Apply specified cross-axis alignment in-place."""
        self._styles["align-items"] = _to_css(value)
        self._notify()
        return self

    def justify_content(self, value: JustifyContent | str) -> Self:
        """Apply specified main-axis alignment in-place."""
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
        """Apply specified width in-place."""
        self._styles["width"] = _to_css(value)
        self._notify()
        return self

    def height(self, value: SizeValue) -> Self:
        """Apply specified height in-place."""
        self._styles["height"] = _to_css(value)
        self._notify()
        return self

    # -------------------------------------------------------------------------
    # Style Presets
    # -------------------------------------------------------------------------

    def pills(self) -> Self:
        """Apply pill/badge style in-place."""
        self._format = SetFormat.PLAIN
        self._direction = SetDirection.HORIZONTAL
        self._styles["gap"] = "8px"
        self._styles["flex-wrap"] = "wrap"
        self._item_styles["padding"] = "6px 14px"
        self._item_styles["border-radius"] = "20px"
        self._item_styles["background-color"] = "#e0e0e0"
        self._notify()
        return self

    def tags(self) -> Self:
        """Apply tags/labels style in-place."""
        self._format = SetFormat.PLAIN
        self._direction = SetDirection.HORIZONTAL
        self._styles["gap"] = "8px"
        self._styles["flex-wrap"] = "wrap"
        self._item_styles["padding"] = "4px 10px"
        self._item_styles["background-color"] = "#f5f5f5"
        self._item_styles["border-radius"] = "4px"
        self._notify()
        return self

    def inline(self) -> Self:
        """Apply inline style in-place."""
        self._format = SetFormat.PLAIN
        self._direction = SetDirection.HORIZONTAL
        self._styles["gap"] = "8px"
        self._styles["flex-wrap"] = "wrap"
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

    def _get_items(self) -> list[Any]:
        """Get items in render order."""
        items = list(self)
        if self._sorted:
            try:
                items = sorted(items, key=str)  # type: ignore[assignment]
            except TypeError:
                # If items can't be sorted, keep original order
                pass
        return items

    def _render_item(self, item: Any) -> str:
        """Render a single item to HTML."""
        if isinstance(item, HTMLObject):
            return item.render()
        elif isinstance(item, str):
            return html.escape(item)
        else:
            return html.escape(str(item))

    def _get_container_styles(self) -> dict[str, str]:
        """Build the complete container styles including layout."""
        styles = self._styles.copy()

        if self._format != SetFormat.BRACES:
            # Flexbox/grid layout for non-brace formats
            if self._direction == SetDirection.HORIZONTAL:
                styles.setdefault("display", "inline-flex")
                styles.setdefault("flex-direction", "row")
                styles.setdefault("align-items", "center")
            elif self._direction == SetDirection.HORIZONTAL_REVERSE:
                styles.setdefault("display", "inline-flex")
                styles.setdefault("flex-direction", "row-reverse")
                styles.setdefault("align-items", "center")
            elif self._direction == SetDirection.VERTICAL:
                styles.setdefault("display", "inline-flex")
                styles.setdefault("flex-direction", "column")
            elif self._direction == SetDirection.VERTICAL_REVERSE:
                styles.setdefault("display", "inline-flex")
                styles.setdefault("flex-direction", "column-reverse")
            elif self._direction == SetDirection.GRID:
                styles.setdefault("display", "inline-grid")
                cols = self._grid_columns or 3
                styles.setdefault("grid-template-columns", f"repeat({cols}, 1fr)")

        return styles

    def _build_item_style_string(self, index: int, total: int) -> str:
        """Build style string for an item, including separators."""
        styles = self._item_styles.copy()

        if self._separator:
            is_horizontal = self._direction in (
                SetDirection.HORIZONTAL,
                SetDirection.HORIZONTAL_REVERSE,
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

    def _render_braces(self) -> str:
        """Render with braces style: {a, b, c}."""
        items = self._get_items()

        if len(items) == 0:
            return "<span>{}</span>"

        items_html = []
        for item in items:
            items_html.append(self._render_item(item))

        content = ", ".join(items_html)
        attrs = self._build_attributes()

        if attrs:
            return f"<span {attrs}>{{{content}}}</span>"
        return f"<span>{{{content}}}</span>"

    def _render_plain(self) -> str:
        """Render as plain items in divs."""
        items = self._get_items()

        if len(items) == 0:
            attrs = self._build_attributes()
            if attrs:
                return f"<div {attrs}></div>"
            return "<div></div>"

        # Build container styles
        container_styles = self._get_container_styles()
        self._styles = container_styles

        # Build container opening tag
        attrs = self._build_attributes()
        if attrs:
            container_open = f"<div {attrs}>"
        else:
            container_open = "<div>"

        # Render items with commas between them
        total = len(items)
        items_html = []
        for i, item in enumerate(items):
            item_content = self._render_item(item)
            item_attrs = self._build_item_attributes(i, total)
            if item_attrs:
                items_html.append(f"<span {item_attrs}>{item_content}</span>")
            else:
                items_html.append(f"<span>{item_content}</span>")
            # Add comma separator after each item except the last
            if i < total - 1:
                items_html.append("<span>, </span>")

        return f"{container_open}{''.join(items_html)}</div>"

    def render(self) -> str:
        """Return HTML representation of this set.

        Returns:
            A string containing valid HTML.
        """
        if self._format == SetFormat.BRACES:
            return self._render_braces()
        else:  # PLAIN
            return self._render_plain()

    # -------------------------------------------------------------------------
    # Set operation overrides (non-mutating, return new sets)
    # -------------------------------------------------------------------------

    def union(self, *others: Iterable[Any]) -> Self:
        """Return union with other sets, preserving settings."""
        result = HTMLSet(set.union(self, *others))
        result._styles = self._styles.copy()
        result._item_styles = self._item_styles.copy()
        result._css_classes = self._css_classes.copy()
        result._item_classes = self._item_classes.copy()
        result._direction = self._direction
        result._format = self._format
        result._grid_columns = self._grid_columns
        result._separator = self._separator
        result._sorted = self._sorted
        result._obs_id = self._obs_id
        return result  # type: ignore[return-value]

    def intersection(self, *others: Iterable[Any]) -> Self:
        """Return intersection with other sets, preserving settings."""
        result = HTMLSet(set.intersection(self, *others))
        result._styles = self._styles.copy()
        result._item_styles = self._item_styles.copy()
        result._css_classes = self._css_classes.copy()
        result._item_classes = self._item_classes.copy()
        result._direction = self._direction
        result._format = self._format
        result._grid_columns = self._grid_columns
        result._separator = self._separator
        result._sorted = self._sorted
        result._obs_id = self._obs_id
        return result  # type: ignore[return-value]

    def difference(self, *others: Iterable[Any]) -> Self:
        """Return difference with other sets, preserving settings."""
        result = HTMLSet(set.difference(self, *others))
        result._styles = self._styles.copy()
        result._item_styles = self._item_styles.copy()
        result._css_classes = self._css_classes.copy()
        result._item_classes = self._item_classes.copy()
        result._direction = self._direction
        result._format = self._format
        result._grid_columns = self._grid_columns
        result._separator = self._separator
        result._sorted = self._sorted
        result._obs_id = self._obs_id
        return result  # type: ignore[return-value]

    def symmetric_difference(self, other: Iterable[Any]) -> Self:
        """Return symmetric difference with other set, preserving settings."""
        result = HTMLSet(set.symmetric_difference(self, other))
        result._styles = self._styles.copy()
        result._item_styles = self._item_styles.copy()
        result._css_classes = self._css_classes.copy()
        result._item_classes = self._item_classes.copy()
        result._direction = self._direction
        result._format = self._format
        result._grid_columns = self._grid_columns
        result._separator = self._separator
        result._sorted = self._sorted
        result._obs_id = self._obs_id
        return result  # type: ignore[return-value]

    def __or__(self, other: Iterable[Any]) -> Self:
        """Union operator |."""
        return self.union(other)

    def __and__(self, other: Iterable[Any]) -> Self:
        """Intersection operator &."""
        return self.intersection(other)

    def __sub__(self, other: Iterable[Any]) -> Self:
        """Difference operator -."""
        return self.difference(other)

    def __xor__(self, other: Iterable[Any]) -> Self:
        """Symmetric difference operator ^."""
        return self.symmetric_difference(other)

    # -------------------------------------------------------------------------
    # Observable mutating methods
    # -------------------------------------------------------------------------

    def add(self, item: Any) -> None:
        """Add item, notifying observers."""
        super().add(item)
        self._notify()

    def discard(self, item: Any) -> None:
        """Discard item, notifying observers."""
        super().discard(item)
        self._notify()

    def remove(self, item: Any) -> None:
        """Remove item, notifying observers."""
        super().remove(item)
        self._notify()

    def pop(self) -> Any:
        """Pop item, notifying observers."""
        result = super().pop()
        self._notify()
        return result

    def clear(self) -> None:
        """Clear set, notifying observers."""
        super().clear()
        self._notify()

    def update(self, *others: Iterable[Any]) -> None:
        """Update set, notifying observers."""
        super().update(*others)
        self._notify()

    def intersection_update(self, *others: Iterable[Any]) -> None:
        """Intersection update, notifying observers."""
        super().intersection_update(*others)
        self._notify()

    def difference_update(self, *others: Iterable[Any]) -> None:
        """Difference update, notifying observers."""
        super().difference_update(*others)
        self._notify()

    def symmetric_difference_update(self, other: Iterable[Any]) -> None:
        """Symmetric difference update, notifying observers."""
        super().symmetric_difference_update(other)
        self._notify()

    def __repr__(self) -> str:
        """Return a detailed representation for debugging."""
        items_repr = set.__repr__(set(self))
        extras = []
        if self._format != SetFormat.BRACES:
            extras.append(f"format={self._format.value}")
        if self._direction != SetDirection.HORIZONTAL:
            extras.append(f"direction={self._direction.value}")
        if self._sorted:
            extras.append("sorted=True")
        if self._styles:
            extras.append(f"styles={self._styles}")

        if extras:
            return f"HTMLSet({items_repr}, {', '.join(extras)})"
        return f"HTMLSet({items_repr})"
