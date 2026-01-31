"""HTMLTuple - A tuple subclass with HTML rendering capabilities."""

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


def _is_namedtuple(obj: Any) -> bool:
    """Check if an object is a namedtuple instance."""
    return (
        isinstance(obj, tuple) and hasattr(obj, "_fields") and hasattr(obj, "_asdict")
    )


class TupleDirection(Enum):
    """Direction in which tuple items are rendered."""

    VERTICAL = "vertical"
    HORIZONTAL = "horizontal"
    VERTICAL_REVERSE = "vertical-reverse"
    HORIZONTAL_REVERSE = "horizontal-reverse"
    GRID = "grid"


class TupleFormat(Enum):
    """Format for displaying tuple items."""

    PLAIN = "plain"  # Just items in divs
    PARENTHESES = "parentheses"  # (a, b, c) style
    LABELED = "labeled"  # For named tuples: field: value


class HTMLTuple(HTMLObject, tuple):
    """A tuple subclass that renders as styled HTML.

    HTMLTuple behaves like a regular Python tuple but includes
    methods for applying CSS styles and rendering to HTML.
    All styling methods modify the object in-place and return self
    for method chaining. Supports named tuples with field name display.

    Examples:
        >>> t = HTMLTuple((1, 2, 3))
        >>> t.render()
        '<div>(1, 2, 3)</div>'

        >>> t.horizontal().pills().render()
        '<div style="display: flex; ...">...</div>'

        >>> from collections import namedtuple
        >>> Point = namedtuple('Point', ['x', 'y'])
        >>> HTMLTuple(Point(10, 20)).labeled().render()
        '<dl><dt>x</dt><dd>10</dd><dt>y</dt><dd>20</dd></dl>'
    """

    _styles: dict[str, str]
    _item_styles: dict[str, str]
    _css_classes: list[str]
    _item_classes: list[str]
    _direction: TupleDirection
    _format: TupleFormat
    _grid_columns: int | None
    _separator: str | None
    _show_parens: bool
    _field_names: tuple[str, ...] | None
    _obs_id: str

    def __new__(cls, items: tuple[Any, ...] = (), **styles: str | CSSValue) -> Self:
        """Create a new HTMLTuple instance.

        Args:
            items: The tuple items.
            **styles: Initial CSS styles.

        Returns:
            A new HTMLTuple instance.
        """
        # Handle namedtuple - extract values
        if _is_namedtuple(items):
            instance = super().__new__(cls, items)
        else:
            instance = super().__new__(cls, items)
        return instance

    def __init__(self, items: tuple[Any, ...] = (), **styles: str | CSSValue) -> None:
        """Initialize an HTMLTuple.

        Args:
            items: The tuple items.
            **styles: CSS styles for the container.
        """
        # Note: tuple is immutable, so we can't call super().__init__
        self._styles = {}
        self._item_styles = {}
        self._css_classes = []
        self._item_classes = []
        self._direction = TupleDirection.HORIZONTAL
        self._format = TupleFormat.PARENTHESES
        self._grid_columns = None
        self._separator = None
        self._show_parens = True

        # Check for named tuple and store field names
        if _is_namedtuple(items):
            self._field_names = items._fields  # type: ignore[attr-defined]
        else:
            self._field_names = None

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
        new_direction: TupleDirection | None = None,
        new_format: TupleFormat | None = None,
        new_grid_columns: int | None = None,
        new_separator: str | None = None,
        new_show_parens: bool | None = None,
    ) -> Self:
        """Create a copy with modified settings.

        This method is used internally for operations that must return
        a new object (like slicing or concatenation).
        """
        result = HTMLTuple(tuple(self))
        result._styles = self._styles.copy()
        result._item_styles = self._item_styles.copy()
        result._css_classes = self._css_classes.copy()
        result._item_classes = self._item_classes.copy()
        result._direction = self._direction
        result._format = self._format
        result._grid_columns = self._grid_columns
        result._separator = self._separator
        result._show_parens = self._show_parens
        result._field_names = self._field_names
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
        if new_show_parens is not None:
            result._show_parens = new_show_parens

        return result  # type: ignore[return-value]

    # -------------------------------------------------------------------------
    # HTMLObject interface
    # -------------------------------------------------------------------------

    def styled(self, **styles: str | CSSValue) -> Self:
        """Apply additional container styles in-place."""
        for key, value in styles.items():
            css_key = key.replace("_", "-")
            self._styles[css_key] = _to_css(value)
        self._notify()
        return self

    def add_class(self, *class_names: str) -> Self:
        """Add CSS classes on the container in-place."""
        self._css_classes.extend(class_names)
        self._notify()
        return self

    # -------------------------------------------------------------------------
    # Format methods
    # -------------------------------------------------------------------------

    def plain(self) -> Self:
        """Apply plain format (without parentheses decoration) in-place."""
        self._format = TupleFormat.PLAIN
        self._show_parens = False
        self._notify()
        return self

    def parentheses(self) -> Self:
        """Apply parentheses format (default) in-place."""
        self._format = TupleFormat.PARENTHESES
        self._show_parens = True
        self._notify()
        return self

    def labeled(self) -> Self:
        """Apply labeled format showing field names in-place.

        For regular tuples, shows index numbers as labels.
        """
        self._format = TupleFormat.LABELED
        self._show_parens = False
        self._notify()
        return self

    # -------------------------------------------------------------------------
    # Direction methods
    # -------------------------------------------------------------------------

    def vertical(self) -> Self:
        """Apply vertical layout in-place."""
        self._direction = TupleDirection.VERTICAL
        self._notify()
        return self

    def horizontal(self) -> Self:
        """Apply horizontal layout (default) in-place."""
        self._direction = TupleDirection.HORIZONTAL
        self._notify()
        return self

    def vertical_reverse(self) -> Self:
        """Apply reversed vertical layout in-place."""
        self._direction = TupleDirection.VERTICAL_REVERSE
        self._notify()
        return self

    def horizontal_reverse(self) -> Self:
        """Apply reversed horizontal layout in-place."""
        self._direction = TupleDirection.HORIZONTAL_REVERSE
        self._notify()
        return self

    def grid(self, columns: int = 3) -> Self:
        """Apply CSS grid layout in-place."""
        self._direction = TupleDirection.GRID
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
        self._format = TupleFormat.PLAIN
        self._show_parens = False
        self._direction = TupleDirection.HORIZONTAL
        self._styles["gap"] = "8px"
        self._item_styles["padding"] = "6px 14px"
        self._item_styles["border-radius"] = "20px"
        self._item_styles["background-color"] = "#e0e0e0"
        self._styles["flex-wrap"] = "wrap"
        self._notify()
        return self

    def tags(self) -> Self:
        """Apply tags/labels style in-place."""
        self._format = TupleFormat.PLAIN
        self._show_parens = False
        self._direction = TupleDirection.HORIZONTAL
        self._styles["gap"] = "8px"
        self._item_styles["padding"] = "4px 10px"
        self._item_styles["background-color"] = "#f5f5f5"
        self._item_styles["border-radius"] = "4px"
        self._styles["flex-wrap"] = "wrap"
        self._notify()
        return self

    def inline(self) -> Self:
        """Apply inline style in-place."""
        self._format = TupleFormat.PLAIN
        self._show_parens = False
        self._direction = TupleDirection.HORIZONTAL
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

    def card(self) -> Self:
        """Apply card style for named tuple display in-place."""
        self._format = TupleFormat.LABELED
        self._show_parens = False
        self._styles["padding"] = "16px"
        self._styles["border"] = "1px solid #e0e0e0"
        self._styles["border-radius"] = "8px"
        self._styles["background-color"] = "white"
        self._notify()
        return self

    # -------------------------------------------------------------------------
    # Rendering
    # -------------------------------------------------------------------------

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

        if self._format != TupleFormat.LABELED:
            # Flexbox/grid layout for non-labeled formats
            if self._direction == TupleDirection.HORIZONTAL:
                styles.setdefault("display", "inline-flex")
                styles.setdefault("flex-direction", "row")
                styles.setdefault("align-items", "center")
            elif self._direction == TupleDirection.HORIZONTAL_REVERSE:
                styles.setdefault("display", "inline-flex")
                styles.setdefault("flex-direction", "row-reverse")
                styles.setdefault("align-items", "center")
            elif self._direction == TupleDirection.VERTICAL:
                styles.setdefault("display", "inline-flex")
                styles.setdefault("flex-direction", "column")
            elif self._direction == TupleDirection.VERTICAL_REVERSE:
                styles.setdefault("display", "inline-flex")
                styles.setdefault("flex-direction", "column-reverse")
            elif self._direction == TupleDirection.GRID:
                styles.setdefault("display", "inline-grid")
                cols = self._grid_columns or 3
                styles.setdefault("grid-template-columns", f"repeat({cols}, 1fr)")

        return styles

    def _build_item_style_string(self, index: int, total: int) -> str:
        """Build style string for an item, including separators."""
        styles = self._item_styles.copy()

        if self._separator:
            is_horizontal = self._direction in (
                TupleDirection.HORIZONTAL,
                TupleDirection.HORIZONTAL_REVERSE,
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

    def _get_labeled_container_styles(self) -> dict[str, str]:
        """Build container styles for labeled format."""
        styles = self._styles.copy()

        if self._direction == TupleDirection.HORIZONTAL:
            # Horizontal: use CSS grid with 2 columns per pair
            styles.setdefault("display", "inline-grid")
            styles.setdefault("grid-template-columns", "auto auto")
            styles.setdefault("column-gap", styles.pop("gap", "8px"))
            styles.setdefault("row-gap", "4px")
            styles.setdefault("align-items", "center")
        elif self._direction == TupleDirection.VERTICAL:
            # Vertical: single column layout
            styles.setdefault("display", "block")
        elif self._direction == TupleDirection.GRID:
            # Grid: multiple pairs per row
            cols = self._grid_columns or 3
            styles.setdefault("display", "inline-grid")
            styles.setdefault("grid-template-columns", f"repeat({cols}, auto auto)")
            styles.setdefault("gap", "8px")
            styles.setdefault("align-items", "center")

        return styles

    def _render_labeled(self) -> str:
        """Render as labeled format (like a definition list)."""
        if len(self) == 0:
            attrs = self._build_attributes()
            if attrs:
                return f"<dl {attrs}></dl>"
            return "<dl></dl>"

        # Get field names
        if self._field_names:
            labels = self._field_names
        else:
            labels = tuple(str(i) for i in range(len(self)))

        # Build container styles for dl
        container_styles = self._get_labeled_container_styles()
        self._styles = container_styles

        # Build content with styled dt/dd
        items_html = []
        dt_style = "margin: 0; font-weight: bold;"
        dd_style = "margin: 0; margin-left: 0;"

        for label, value in zip(labels, self):
            key_html = html.escape(str(label))
            value_html = self._render_item(value)
            dt = f'<dt style="{dt_style}">{key_html}</dt>'
            dd = f'<dd style="{dd_style}">{value_html}</dd>'
            items_html.append(f"{dt}{dd}")

        attrs = self._build_attributes()
        if attrs:
            return f"<dl {attrs}>{''.join(items_html)}</dl>"
        return f"<dl>{''.join(items_html)}</dl>"

    def _render_parentheses(self) -> str:
        """Render with parentheses style: (a, b, c)."""
        if len(self) == 0:
            return "<span>()</span>"

        items_html = []
        for item in self:
            items_html.append(self._render_item(item))

        content = ", ".join(items_html)
        attrs = self._build_attributes()

        if attrs:
            return f"<span {attrs}>({content})</span>"
        return f"<span>({content})</span>"

    def _render_plain(self) -> str:
        """Render as plain items in divs."""
        if len(self) == 0:
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
        total = len(self)
        items_html = []
        for i, item in enumerate(self):
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
        """Return HTML representation of this tuple.

        Returns:
            A string containing valid HTML.
        """
        if self._format == TupleFormat.LABELED:
            return self._render_labeled()
        elif self._format == TupleFormat.PARENTHESES:
            return self._render_parentheses()
        else:  # PLAIN
            return self._render_plain()

    # -------------------------------------------------------------------------
    # Tuple operation overrides
    # -------------------------------------------------------------------------

    def __add__(self, other: tuple[Any, ...]) -> Self:
        """Concatenate tuples, preserving settings."""
        result = HTMLTuple(tuple.__add__(self, other))
        result._styles = self._styles.copy()
        result._item_styles = self._item_styles.copy()
        result._css_classes = self._css_classes.copy()
        result._item_classes = self._item_classes.copy()
        result._direction = self._direction
        result._format = self._format
        result._grid_columns = self._grid_columns
        result._separator = self._separator
        result._show_parens = self._show_parens
        result._field_names = None  # Concatenation loses field names
        result._obs_id = self._obs_id  # Preserve ID so updates still work
        return result  # type: ignore[return-value]

    def __getitem__(self, key: Any) -> Any:  # type: ignore[override]
        """Get item or slice.

        Single index returns the item itself.
        Slice returns a new HTMLTuple with settings preserved.
        """
        result = tuple.__getitem__(self, key)
        if isinstance(key, slice):
            new_tuple = HTMLTuple(result)
            new_tuple._styles = self._styles.copy()
            new_tuple._item_styles = self._item_styles.copy()
            new_tuple._css_classes = self._css_classes.copy()
            new_tuple._item_classes = self._item_classes.copy()
            new_tuple._direction = self._direction
            new_tuple._format = self._format
            new_tuple._grid_columns = self._grid_columns
            new_tuple._separator = self._separator
            new_tuple._show_parens = self._show_parens
            # Slicing loses field name association
            new_tuple._field_names = None
            new_tuple._obs_id = self._obs_id  # Preserve ID so updates still work
            return new_tuple
        return result

    def __repr__(self) -> str:
        """Return a detailed representation for debugging."""
        items_repr = tuple.__repr__(self)
        extras = []
        if self._field_names:
            extras.append(f"fields={self._field_names}")
        if self._format != TupleFormat.PARENTHESES:
            extras.append(f"format={self._format.value}")
        if self._direction != TupleDirection.HORIZONTAL:
            extras.append(f"direction={self._direction.value}")
        if self._styles:
            extras.append(f"styles={self._styles}")

        if extras:
            return f"HTMLTuple({items_repr}, {', '.join(extras)})"
        return f"HTMLTuple({items_repr})"
