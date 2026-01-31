"""HTMLDict - A dict subclass with HTML rendering capabilities."""

from __future__ import annotations

import html
import uuid
from enum import Enum
from typing import Any, Self

from animaid.css_types import (
    BorderValue,
    ColorValue,
    CSSValue,
    SizeValue,
    SpacingValue,
)
from animaid.html_object import HTMLObject


def _to_css(value: object) -> str:
    """Convert a value to its CSS string representation."""
    if hasattr(value, "to_css"):
        return str(value.to_css())
    return str(value)


class DictFormat(Enum):
    """Format for rendering the dictionary."""

    DEFINITION_LIST = "dl"  # <dl><dt>key</dt><dd>value</dd></dl>
    TABLE = "table"  # <table><tr><td>key</td><td>value</td></tr></table>
    DIVS = "divs"  # Flexbox divs


class DictLayout(Enum):
    """Layout direction for dictionary entries."""

    VERTICAL = "vertical"  # Entries stacked vertically
    HORIZONTAL = "horizontal"  # Entries side by side
    GRID = "grid"  # Grid layout


class HTMLDict(HTMLObject, dict):
    """A dict subclass that renders as styled HTML.

    HTMLDict behaves like a regular Python dict but includes
    methods for applying CSS styles and rendering to HTML.
    All styling methods modify the object in-place and return self
    for method chaining. Supports definition list, table, and flexbox layouts.

    Examples:
        >>> d = HTMLDict({"name": "Alice", "age": 30})
        >>> d.render()
        '<dl><dt>name</dt><dd>Alice</dd><dt>age</dt><dd>30</dd></dl>'

        >>> d.as_table().render()
        '<table><tr><td>name</td><td>Alice</td></tr>...</table>'

        >>> d.key_bold().key_color("blue").render()
        '<dl><dt style="font-weight: bold; color: blue">name</dt>...'
    """

    _styles: dict[str, str]
    _key_styles: dict[str, str]
    _value_styles: dict[str, str]
    _css_classes: list[str]
    _key_classes: list[str]
    _value_classes: list[str]
    _format: DictFormat
    _layout: DictLayout
    _grid_columns: int
    _key_value_separator: str
    _entry_separator: str | None
    _show_keys: bool
    _obs_id: str

    def __init__(
        self, data: dict[Any, Any] | None = None, **styles: str | CSSValue
    ) -> None:
        """Initialize an HTMLDict.

        Args:
            data: Initial dictionary data.
            **styles: CSS styles for the container (underscores to hyphens).
                      Accepts both strings and CSS type objects (Color, Size, etc.)
        """
        super().__init__(data or {})
        self._styles = {}
        self._key_styles = {}
        self._value_styles = {}
        self._css_classes = []
        self._key_classes = []
        self._value_classes = []
        self._format = DictFormat.DEFINITION_LIST
        self._layout = DictLayout.VERTICAL
        self._grid_columns = 2
        self._key_value_separator = ""
        self._entry_separator = None
        self._show_keys = True
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
        new_key_styles: dict[str, str] | None = None,
        new_value_styles: dict[str, str] | None = None,
        new_classes: list[str] | None = None,
        new_key_classes: list[str] | None = None,
        new_value_classes: list[str] | None = None,
        new_format: DictFormat | None = None,
        new_layout: DictLayout | None = None,
        new_grid_columns: int | None = None,
        new_key_value_separator: str | None = None,
        new_entry_separator: str | None = None,
        new_show_keys: bool | None = None,
    ) -> Self:
        """Create a copy with modified settings.

        This method is used internally for operations that must return
        a new object (like merging dicts with | operator).
        """
        result = HTMLDict(dict(self))
        result._styles = self._styles.copy()
        result._key_styles = self._key_styles.copy()
        result._value_styles = self._value_styles.copy()
        result._css_classes = self._css_classes.copy()
        result._key_classes = self._key_classes.copy()
        result._value_classes = self._value_classes.copy()
        result._format = self._format
        result._layout = self._layout
        result._grid_columns = self._grid_columns
        result._key_value_separator = self._key_value_separator
        result._entry_separator = self._entry_separator
        result._show_keys = self._show_keys
        result._obs_id = self._obs_id  # Preserve ID so updates still work

        if new_styles:
            result._styles.update(new_styles)
        if new_key_styles:
            result._key_styles.update(new_key_styles)
        if new_value_styles:
            result._value_styles.update(new_value_styles)
        if new_classes:
            result._css_classes.extend(new_classes)
        if new_key_classes:
            result._key_classes.extend(new_key_classes)
        if new_value_classes:
            result._value_classes.extend(new_value_classes)
        if new_format is not None:
            result._format = new_format
        if new_layout is not None:
            result._layout = new_layout
        if new_grid_columns is not None:
            result._grid_columns = new_grid_columns
        if new_key_value_separator is not None:
            result._key_value_separator = new_key_value_separator
        if new_entry_separator is not None:
            result._entry_separator = new_entry_separator
        if new_show_keys is not None:
            result._show_keys = new_show_keys

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
    # Format methods
    # -------------------------------------------------------------------------

    def as_definition_list(self) -> Self:
        """Apply definition list (<dl>) format in-place."""
        self._format = DictFormat.DEFINITION_LIST
        self._notify()
        return self

    def as_table(self) -> Self:
        """Apply table (<table>) format in-place."""
        self._format = DictFormat.TABLE
        self._notify()
        return self

    def as_divs(self) -> Self:
        """Apply flexbox divs format in-place."""
        self._format = DictFormat.DIVS
        self._notify()
        return self

    # -------------------------------------------------------------------------
    # Layout methods
    # -------------------------------------------------------------------------

    def vertical(self) -> Self:
        """Apply vertical layout (entries stacked) in-place."""
        self._layout = DictLayout.VERTICAL
        self._notify()
        return self

    def horizontal(self) -> Self:
        """Apply horizontal layout (entries side by side) in-place."""
        self._layout = DictLayout.HORIZONTAL
        self._format = DictFormat.DIVS
        self._notify()
        return self

    def grid(self, columns: int = 2) -> Self:
        """Apply grid layout in-place.

        Args:
            columns: Number of key-value pairs per row.
        """
        self._layout = DictLayout.GRID
        self._format = DictFormat.DIVS
        self._grid_columns = columns
        self._notify()
        return self

    # -------------------------------------------------------------------------
    # Key styling methods
    # -------------------------------------------------------------------------

    def key_styled(self, **styles: str | CSSValue) -> Self:
        """Apply styles to keys in-place.

        Args:
            **styles: CSS property-value pairs for keys.
                      Accepts both strings and CSS type objects (Color, Size, etc.)
        """
        for key, value in styles.items():
            css_key = key.replace("_", "-")
            self._key_styles[css_key] = _to_css(value)
        self._notify()
        return self

    def key_bold(self) -> Self:
        """Apply bold style to keys in-place."""
        self._key_styles["font-weight"] = "bold"
        self._notify()
        return self

    def key_italic(self) -> Self:
        """Apply italic style to keys in-place."""
        self._key_styles["font-style"] = "italic"
        self._notify()
        return self

    def key_color(self, value: ColorValue) -> Self:
        """Apply color to keys in-place.

        Args:
            value: CSS color value (e.g., "blue", Color.blue, Color.hex("#00f")).
        """
        self._key_styles["color"] = _to_css(value)
        self._notify()
        return self

    def key_background(self, value: ColorValue) -> Self:
        """Apply background color to keys in-place.

        Args:
            value: CSS color value (e.g., "yellow", Color.yellow).
        """
        self._key_styles["background-color"] = _to_css(value)
        self._notify()
        return self

    def key_width(self, value: SizeValue) -> Self:
        """Apply fixed key width in-place.

        Args:
            value: CSS width value (e.g., "100px", Size.px(100)).
        """
        css_value = _to_css(value)
        self._key_styles["width"] = css_value
        self._key_styles["min-width"] = css_value
        self._notify()
        return self

    def key_padding(self, value: SpacingValue) -> Self:
        """Apply padding to keys in-place.

        Args:
            value: CSS padding value (e.g., "10px", Size.px(10), Spacing.all(10)).
        """
        self._key_styles["padding"] = _to_css(value)
        self._notify()
        return self

    def add_key_class(self, *class_names: str) -> Self:
        """Add CSS classes to keys in-place.

        Args:
            *class_names: CSS class names to add to keys.
        """
        self._key_classes.extend(class_names)
        self._notify()
        return self

    def hide_keys(self) -> Self:
        """Hide keys and only render values in-place."""
        self._show_keys = False
        self._notify()
        return self

    # -------------------------------------------------------------------------
    # Value styling methods
    # -------------------------------------------------------------------------

    def value_styled(self, **styles: str | CSSValue) -> Self:
        """Apply styles to values in-place.

        Args:
            **styles: CSS property-value pairs for values.
                      Accepts both strings and CSS type objects (Color, Size, etc.)
        """
        for key, value in styles.items():
            css_key = key.replace("_", "-")
            self._value_styles[css_key] = _to_css(value)
        self._notify()
        return self

    def value_bold(self) -> Self:
        """Apply bold style to values in-place."""
        self._value_styles["font-weight"] = "bold"
        self._notify()
        return self

    def value_italic(self) -> Self:
        """Apply italic style to values in-place."""
        self._value_styles["font-style"] = "italic"
        self._notify()
        return self

    def value_color(self, value: ColorValue) -> Self:
        """Apply color to values in-place.

        Args:
            value: CSS color value (e.g., "green", Color.green).
        """
        self._value_styles["color"] = _to_css(value)
        self._notify()
        return self

    def value_background(self, value: ColorValue) -> Self:
        """Apply background color to values in-place.

        Args:
            value: CSS color value (e.g., "lightgray", Color.hex("#eee")).
        """
        self._value_styles["background-color"] = _to_css(value)
        self._notify()
        return self

    def value_padding(self, value: SpacingValue) -> Self:
        """Apply padding to values in-place.

        Args:
            value: CSS padding value (e.g., "10px", Size.px(10), Spacing.all(10)).
        """
        self._value_styles["padding"] = _to_css(value)
        self._notify()
        return self

    def add_value_class(self, *class_names: str) -> Self:
        """Add CSS classes to values in-place.

        Args:
            *class_names: CSS class names to add to values.
        """
        self._value_classes.extend(class_names)
        self._notify()
        return self

    # -------------------------------------------------------------------------
    # Separator methods
    # -------------------------------------------------------------------------

    def separator(self, value: str) -> Self:
        """Apply a separator between key and value in-place.

        Args:
            value: Separator string (e.g., ":", " -> ", " = ").
        """
        self._key_value_separator = value
        self._notify()
        return self

    def entry_separator(self, value: BorderValue) -> Self:
        """Apply separator between entries (border) in-place.

        Args:
            value: CSS border value for separator (e.g., "1px solid gray").
        """
        self._entry_separator = _to_css(value)
        self._notify()
        return self

    # -------------------------------------------------------------------------
    # Container styling methods
    # -------------------------------------------------------------------------

    def gap(self, value: SizeValue) -> Self:
        """Apply gap between entries in-place.

        Args:
            value: CSS gap value (e.g., "10px", Size.px(10), Size.rem(1)).
        """
        self._styles["gap"] = _to_css(value)
        self._notify()
        return self

    def padding(self, value: SpacingValue) -> Self:
        """Apply container padding in-place.

        Args:
            value: CSS padding value (e.g., "10px", Size.px(10)).
        """
        self._styles["padding"] = _to_css(value)
        self._notify()
        return self

    def margin(self, value: SpacingValue) -> Self:
        """Apply container margin in-place.

        Args:
            value: CSS margin value (e.g., "10px", Size.px(10), Spacing.all(10)).
        """
        self._styles["margin"] = _to_css(value)
        self._notify()
        return self

    def border(self, value: BorderValue) -> Self:
        """Apply container border in-place.

        Args:
            value: CSS border value (e.g., "1px solid black", Border.solid()).
        """
        self._styles["border"] = _to_css(value)
        self._notify()
        return self

    def border_radius(self, value: SizeValue) -> Self:
        """Apply rounded container corners in-place.

        Args:
            value: CSS border-radius value (e.g., "5px", Size.px(5), Size.percent(50)).
        """
        self._styles["border-radius"] = _to_css(value)
        self._notify()
        return self

    def background(self, value: ColorValue) -> Self:
        """Apply container background in-place.

        Args:
            value: CSS color value (e.g., "white", Color.white, Color.hex("#fff")).
        """
        self._styles["background-color"] = _to_css(value)
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

    def width(self, value: SizeValue) -> Self:
        """Apply container width in-place.

        Args:
            value: CSS width value (e.g., "300px", Size.px(300), Size.percent(100)).
        """
        self._styles["width"] = _to_css(value)
        self._notify()
        return self

    def max_width(self, value: SizeValue) -> Self:
        """Apply maximum width in-place.

        Args:
            value: CSS max-width value (e.g., "500px", Size.px(500), Size.vw(80)).
        """
        self._styles["max-width"] = _to_css(value)
        self._notify()
        return self

    # -------------------------------------------------------------------------
    # Style Presets (beginner-friendly)
    # -------------------------------------------------------------------------

    def card(self) -> Self:
        """Apply card style with shadow and rounded corners in-place.

        Creates a visually appealing card-style display.
        """
        self._format = DictFormat.DIVS
        self._styles["padding"] = "16px"
        self._styles["border"] = "1px solid #e0e0e0"
        self._styles["border-radius"] = "8px"
        self._styles["background-color"] = "white"
        self._styles["gap"] = "8px"
        self._key_styles["font-weight"] = "bold"
        self._key_value_separator = ": "
        self._notify()
        return self

    def simple(self) -> Self:
        """Apply simple key: value formatting in-place.

        Clean, minimal display with colon separators.
        """
        self._key_value_separator = ": "
        self._key_styles["font-weight"] = "bold"
        self._styles["gap"] = "4px"
        self._notify()
        return self

    def striped(self) -> Self:
        """Apply striped table style in-place.

        Creates an alternating row colors table.
        """
        self._format = DictFormat.TABLE
        self._styles["border"] = "1px solid #e0e0e0"
        self._key_styles["padding"] = "8px 12px"
        self._value_styles["padding"] = "8px 12px"
        self._key_styles["background-color"] = "#f5f5f5"
        self._key_styles["font-weight"] = "bold"
        self._notify()
        return self

    def compact(self) -> Self:
        """Apply compact spacing style in-place.

        Minimal padding and spacing for dense displays.
        """
        self._styles["gap"] = "2px"
        self._key_styles["padding"] = "2px 4px"
        self._value_styles["padding"] = "2px 4px"
        self._notify()
        return self

    def spaced(self) -> Self:
        """Apply generous spacing style in-place.

        More padding and gaps for readability.
        """
        self._styles["gap"] = "12px"
        self._key_styles["padding"] = "8px"
        self._value_styles["padding"] = "8px"
        self._notify()
        return self

    def labeled(self) -> Self:
        """Apply label-style keys in-place.

        Keys are styled as small labels above values.
        """
        self._format = DictFormat.DIVS
        self._layout = DictLayout.VERTICAL
        self._styles["gap"] = "16px"
        self._key_styles["font-size"] = "0.75em"
        self._key_styles["color"] = "#757575"
        self._key_styles["text-transform"] = "uppercase"
        self._key_styles["letter-spacing"] = "0.05em"
        self._value_styles["font-size"] = "1.1em"
        self._notify()
        return self

    def inline(self) -> Self:
        """Apply inline horizontal display in-place.

        All key-value pairs on one line.
        """
        self._layout = DictLayout.HORIZONTAL
        self._format = DictFormat.DIVS
        self._styles["gap"] = "16px"
        self._key_value_separator = ": "
        self._key_styles["font-weight"] = "bold"
        self._notify()
        return self

    def bordered(self) -> Self:
        """Apply bordered cells style in-place.

        Each key-value pair has visible borders.
        """
        self._format = DictFormat.TABLE
        self._styles["border"] = "1px solid #e0e0e0"
        self._styles["border-collapse"] = "collapse"
        self._key_styles["border"] = "1px solid #e0e0e0"
        self._key_styles["padding"] = "8px"
        self._value_styles["border"] = "1px solid #e0e0e0"
        self._value_styles["padding"] = "8px"
        self._notify()
        return self

    # -------------------------------------------------------------------------
    # Rendering
    # -------------------------------------------------------------------------

    def _render_item(self, item: Any) -> str:
        """Render a single value to HTML.

        Args:
            item: The value to render.

        Returns:
            HTML string for the value.
        """
        if isinstance(item, HTMLObject):
            return item.render()
        elif isinstance(item, str):
            return html.escape(item)
        else:
            return html.escape(str(item))

    def _build_key_style_string(self) -> str:
        """Build CSS style string for keys."""
        if not self._key_styles:
            return ""
        return "; ".join(f"{k}: {v}" for k, v in self._key_styles.items())

    def _build_value_style_string(self) -> str:
        """Build CSS style string for values."""
        if not self._value_styles:
            return ""
        return "; ".join(f"{k}: {v}" for k, v in self._value_styles.items())

    def _build_key_attributes(self) -> str:
        """Build attribute string for key elements."""
        parts = []
        if self._key_classes:
            parts.append(f'class="{" ".join(self._key_classes)}"')
        style_str = self._build_key_style_string()
        if style_str:
            parts.append(f'style="{style_str}"')
        return " ".join(parts)

    def _build_value_attributes(self, index: int, total: int) -> str:
        """Build attribute string for value elements."""
        parts = []
        if self._value_classes:
            parts.append(f'class="{" ".join(self._value_classes)}"')

        styles = self._value_styles.copy()

        # Add entry separator if not last item
        if self._entry_separator and index < total - 1:
            if self._layout == DictLayout.HORIZONTAL:
                styles["border-right"] = self._entry_separator
            else:
                styles["border-bottom"] = self._entry_separator

        if styles:
            style_str = "; ".join(f"{k}: {v}" for k, v in styles.items())
            parts.append(f'style="{style_str}"')

        return " ".join(parts)

    def _get_container_styles(self) -> dict[str, str]:
        """Build container styles including layout."""
        styles = self._styles.copy()

        if self._format == DictFormat.DIVS:
            if self._layout == DictLayout.HORIZONTAL:
                styles.setdefault("display", "flex")
                styles.setdefault("flex-direction", "row")
                styles.setdefault("flex-wrap", "wrap")
            elif self._layout == DictLayout.GRID:
                styles.setdefault("display", "grid")
                # Each entry is key + value, so multiply columns by 2
                cols = self._grid_columns * 2 if self._show_keys else self._grid_columns
                styles.setdefault("grid-template-columns", f"repeat({cols}, auto)")
            else:
                styles.setdefault("display", "flex")
                styles.setdefault("flex-direction", "column")

        return styles

    def _render_as_definition_list(self) -> str:
        """Render as a definition list."""
        container_styles = self._get_container_styles()
        self._styles = container_styles

        attrs = self._build_attributes()
        key_attrs = self._build_key_attributes()
        total = len(self)

        items_html = []
        for i, (key, value) in enumerate(self.items()):
            key_html = html.escape(str(key))
            value_html = self._render_item(value)
            value_attrs = self._build_value_attributes(i, total)

            if self._key_value_separator:
                key_html += self._key_value_separator

            if self._show_keys:
                if key_attrs:
                    items_html.append(f"<dt {key_attrs}>{key_html}</dt>")
                else:
                    items_html.append(f"<dt>{key_html}</dt>")

            if value_attrs:
                items_html.append(f"<dd {value_attrs}>{value_html}</dd>")
            else:
                items_html.append(f"<dd>{value_html}</dd>")

        if attrs:
            return f"<dl {attrs}>{''.join(items_html)}</dl>"
        return f"<dl>{''.join(items_html)}</dl>"

    def _render_as_table(self) -> str:
        """Render as a table."""
        container_styles = self._get_container_styles()
        self._styles = container_styles

        attrs = self._build_attributes()
        key_attrs = self._build_key_attributes()
        total = len(self)

        rows_html = []
        for i, (key, value) in enumerate(self.items()):
            key_html = html.escape(str(key))
            value_html = self._render_item(value)
            value_attrs = self._build_value_attributes(i, total)

            if self._key_value_separator:
                key_html += self._key_value_separator

            row_parts = []
            if self._show_keys:
                if key_attrs:
                    row_parts.append(f"<td {key_attrs}>{key_html}</td>")
                else:
                    row_parts.append(f"<td>{key_html}</td>")

            if value_attrs:
                row_parts.append(f"<td {value_attrs}>{value_html}</td>")
            else:
                row_parts.append(f"<td>{value_html}</td>")

            rows_html.append(f"<tr>{''.join(row_parts)}</tr>")

        if attrs:
            return f"<table {attrs}>{''.join(rows_html)}</table>"
        return f"<table>{''.join(rows_html)}</table>"

    def _render_as_divs(self) -> str:
        """Render as flexbox divs."""
        container_styles = self._get_container_styles()
        self._styles = container_styles

        attrs = self._build_attributes()
        key_attrs = self._build_key_attributes()
        total = len(self)

        items_html = []
        for i, (key, value) in enumerate(self.items()):
            key_html = html.escape(str(key))
            value_html = self._render_item(value)
            value_attrs = self._build_value_attributes(i, total)

            if self._key_value_separator:
                key_html += self._key_value_separator

            if self._show_keys:
                if key_attrs:
                    items_html.append(f"<div {key_attrs}>{key_html}</div>")
                else:
                    items_html.append(f"<div>{key_html}</div>")

            if value_attrs:
                items_html.append(f"<div {value_attrs}>{value_html}</div>")
            else:
                items_html.append(f"<div>{value_html}</div>")

        if attrs:
            return f"<div {attrs}>{''.join(items_html)}</div>"
        return f"<div>{''.join(items_html)}</div>"

    def render(self) -> str:
        """Return HTML representation of this dictionary.

        Returns:
            A string containing valid HTML.
        """
        if len(self) == 0:
            if self._format == DictFormat.DEFINITION_LIST:
                return "<dl></dl>"
            elif self._format == DictFormat.TABLE:
                return "<table></table>"
            else:
                return "<div></div>"

        if self._format == DictFormat.DEFINITION_LIST:
            return self._render_as_definition_list()
        elif self._format == DictFormat.TABLE:
            return self._render_as_table()
        else:
            return self._render_as_divs()

    # -------------------------------------------------------------------------
    # Dict operation overrides
    # -------------------------------------------------------------------------

    def __or__(self, other: dict[Any, Any]) -> Self:
        """Merge dicts with | operator, preserving settings."""
        result = HTMLDict(dict.__or__(self, other))
        result._styles = self._styles.copy()
        result._key_styles = self._key_styles.copy()
        result._value_styles = self._value_styles.copy()
        result._css_classes = self._css_classes.copy()
        result._key_classes = self._key_classes.copy()
        result._value_classes = self._value_classes.copy()
        result._format = self._format
        result._layout = self._layout
        result._grid_columns = self._grid_columns
        result._key_value_separator = self._key_value_separator
        result._entry_separator = self._entry_separator
        result._show_keys = self._show_keys
        result._obs_id = self._obs_id
        return result  # type: ignore[return-value]

    # -------------------------------------------------------------------------
    # Observable mutating methods
    # -------------------------------------------------------------------------

    def __setitem__(self, key: Any, value: Any) -> None:
        """Set item, notifying observers."""
        super().__setitem__(key, value)
        self._notify()

    def __delitem__(self, key: Any) -> None:
        """Delete item, notifying observers."""
        super().__delitem__(key)
        self._notify()

    def update(self, *args: Any, **kwargs: Any) -> None:
        """Update dict, notifying observers."""
        super().update(*args, **kwargs)
        self._notify()

    def pop(self, key: Any, *default: Any) -> Any:
        """Pop item, notifying observers."""
        result = super().pop(key, *default)
        self._notify()
        return result

    def popitem(self) -> tuple[Any, Any]:
        """Pop item, notifying observers."""
        result = super().popitem()
        self._notify()
        return result

    def clear(self) -> None:
        """Clear dict, notifying observers."""
        super().clear()
        self._notify()

    def setdefault(self, key: Any, default: Any = None) -> Any:
        """Set default, notifying observers."""
        result = super().setdefault(key, default)
        self._notify()
        return result

    def __repr__(self) -> str:
        """Return a detailed representation for debugging."""
        dict_repr = dict.__repr__(self)
        extras = []
        if self._format != DictFormat.DEFINITION_LIST:
            extras.append(f"format={self._format.value}")
        if self._layout != DictLayout.VERTICAL:
            extras.append(f"layout={self._layout.value}")
        if self._styles:
            extras.append(f"styles={self._styles}")

        if extras:
            return f"HTMLDict({dict_repr}, {', '.join(extras)})"
        return f"HTMLDict({dict_repr})"
