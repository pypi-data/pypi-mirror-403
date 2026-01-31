"""HTMLInt - An int subclass with HTML rendering capabilities."""

from __future__ import annotations

import html
import uuid
from typing import TYPE_CHECKING, Any, Self

from animaid.css_types import (
    BorderValue,
    ColorValue,
    CSSValue,
    SizeValue,
    SpacingValue,
)
from animaid.html_object import HTMLObject

if TYPE_CHECKING:
    from animaid.html_float import HTMLFloat


def _to_css(value: object) -> str:
    """Convert a value to its CSS string representation."""
    if hasattr(value, "to_css"):
        return str(value.to_css())
    return str(value)


class HTMLInt(HTMLObject, int):
    """An int subclass that renders as styled HTML.

    HTMLInt behaves like a regular Python int but includes methods
    for applying CSS styles, number formatting, and rendering to HTML.
    All styling methods modify the object in-place and return self
    for method chaining.

    Examples:
        >>> n = HTMLInt(42)
        >>> n.bold().red().render()
        '<span style="font-weight: bold; color: red">42</span>'

        >>> HTMLInt(1234567).comma().render()
        '<span>1,234,567</span>'

        >>> HTMLInt(1000).currency("$").bold().render()
        '<span style="font-weight: bold">$1,000</span>'

        >>> HTMLInt(1).ordinal().render()
        '<span>1st</span>'
    """

    _styles: dict[str, str]
    _css_classes: list[str]
    _tag: str
    _display_format: str
    _format_options: dict[str, object]
    _obs_id: str

    def __new__(cls, value: int = 0, **styles: str | CSSValue) -> Self:
        """Create a new HTMLInt instance.

        Args:
            value: The integer value.
            **styles: Initial CSS styles (underscores converted to hyphens).

        Returns:
            A new HTMLInt instance.
        """
        instance = super().__new__(cls, value)
        return instance

    def __init__(self, value: int = 0, **styles: str | CSSValue) -> None:
        """Initialize styles for the HTMLInt.

        Args:
            value: The integer value (handled by __new__).
            **styles: CSS property-value pairs.
        """
        self._styles = {}
        self._css_classes = []
        self._tag = "span"
        self._display_format = "default"
        self._format_options = {}
        self._obs_id = str(uuid.uuid4())

        for key, val in styles.items():
            css_key = key.replace("_", "-")
            self._styles[css_key] = _to_css(val)

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
        new_classes: list[str] | None = None,
        new_tag: str | None = None,
        new_format: str | None = None,
        new_format_options: dict[str, object] | None = None,
    ) -> Self:
        """Create a copy of this HTMLInt with modified settings.

        This method is used internally for operations that must return
        a new object (like arithmetic operations).

        Args:
            new_styles: Styles to merge with existing styles.
            new_classes: Classes to add to existing classes.
            new_tag: New HTML tag to use.
            new_format: New display format.
            new_format_options: New format options.

        Returns:
            A new HTMLInt with combined settings.
        """
        result = HTMLInt(int(self))
        result._styles = self._styles.copy()
        result._css_classes = self._css_classes.copy()
        result._tag = self._tag
        result._display_format = self._display_format
        result._format_options = self._format_options.copy()
        result._obs_id = self._obs_id  # Preserve ID so updates still work

        if new_styles:
            result._styles.update(new_styles)
        if new_classes:
            result._css_classes.extend(new_classes)
        if new_tag:
            result._tag = new_tag
        if new_format:
            result._display_format = new_format
        if new_format_options:
            result._format_options.update(new_format_options)

        return result  # type: ignore[return-value]

    def styled(self, **styles: str | CSSValue) -> Self:
        """Apply additional inline styles in-place.

        Args:
            **styles: CSS property-value pairs.

        Returns:
            Self for method chaining.
        """
        for key, value in styles.items():
            css_key = key.replace("_", "-")
            self._styles[css_key] = _to_css(value)
        self._notify()
        return self

    def add_class(self, *class_names: str) -> Self:
        """Add CSS classes in-place.

        Args:
            *class_names: CSS class names to add.

        Returns:
            Self for method chaining.
        """
        self._css_classes.extend(class_names)
        self._notify()
        return self

    def tag(self, tag_name: str) -> Self:
        """Change the HTML tag in-place.

        Args:
            tag_name: The HTML tag to use (e.g., "div", "p", "strong").

        Returns:
            Self for method chaining.
        """
        self._tag = tag_name
        self._notify()
        return self

    def _format_value(self) -> str:
        """Format the integer value based on display format settings."""
        value = int(self)

        if self._display_format == "comma":
            return f"{value:,}"
        elif self._display_format == "currency":
            symbol = self._format_options.get("symbol", "$")
            return f"{symbol}{value:,}"
        elif self._display_format == "percent":
            return f"{value}%"
        elif self._display_format == "ordinal":
            return self._to_ordinal(value)
        elif self._display_format == "padded":
            width = self._format_options.get("width", 2)
            return f"{value:0{width}d}"
        else:
            return str(value)

    @staticmethod
    def _to_ordinal(n: int) -> str:
        """Convert an integer to its ordinal string (1st, 2nd, 3rd, etc.)."""
        if 11 <= abs(n) % 100 <= 13:
            suffix = "th"
        else:
            suffix = {1: "st", 2: "nd", 3: "rd"}.get(abs(n) % 10, "th")
        return f"{n}{suffix}"

    def render(self) -> str:
        """Return HTML representation of this integer.

        Returns:
            A string containing valid HTML.
        """
        content = html.escape(self._format_value())
        attrs = self._build_attributes()

        if attrs:
            return f"<{self._tag} {attrs}>{content}</{self._tag}>"
        else:
            return f"<{self._tag}>{content}</{self._tag}>"

    # -------------------------------------------------------------------------
    # Number Formatting Methods
    # -------------------------------------------------------------------------

    def comma(self) -> Self:
        """Apply thousand separator formatting in-place.

        Examples:
            >>> HTMLInt(1234567).comma().render()
            '<span>1,234,567</span>'
        """
        self._display_format = "comma"
        self._notify()
        return self

    def currency(self, symbol: str = "$") -> Self:
        """Apply currency formatting in-place.

        Args:
            symbol: Currency symbol (default "$")

        Examples:
            >>> HTMLInt(1000).currency().render()
            '<span>$1,000</span>'
            >>> HTMLInt(1000).currency("€").render()
            '<span>€1,000</span>'
        """
        self._display_format = "currency"
        self._format_options["symbol"] = symbol
        self._notify()
        return self

    def percent(self) -> Self:
        """Apply percentage formatting in-place.

        Examples:
            >>> HTMLInt(85).percent().render()
            '<span>85%</span>'
        """
        self._display_format = "percent"
        self._notify()
        return self

    def ordinal(self) -> Self:
        """Apply ordinal formatting (1st, 2nd, 3rd, etc.) in-place.

        Examples:
            >>> HTMLInt(1).ordinal().render()
            '<span>1st</span>'
            >>> HTMLInt(22).ordinal().render()
            '<span>22nd</span>'
        """
        self._display_format = "ordinal"
        self._notify()
        return self

    def padded(self, width: int = 2) -> Self:
        """Apply zero-padding formatting in-place.

        Args:
            width: Minimum width (default 2)

        Examples:
            >>> HTMLInt(7).padded(3).render()
            '<span>007</span>'
        """
        self._display_format = "padded"
        self._format_options["width"] = width
        self._notify()
        return self

    # -------------------------------------------------------------------------
    # Style Methods (no-argument styles)
    # -------------------------------------------------------------------------

    def bold(self) -> Self:
        """Apply bold text style in-place."""
        self._styles["font-weight"] = "bold"
        self._notify()
        return self

    def italic(self) -> Self:
        """Apply italic text style in-place."""
        self._styles["font-style"] = "italic"
        self._notify()
        return self

    def underline(self) -> Self:
        """Apply underline text style in-place."""
        self._styles["text-decoration"] = "underline"
        self._notify()
        return self

    def strikethrough(self) -> Self:
        """Apply strikethrough text style in-place."""
        self._styles["text-decoration"] = "line-through"
        self._notify()
        return self

    def monospace(self) -> Self:
        """Apply monospace font in-place."""
        self._styles["font-family"] = "monospace"
        self._notify()
        return self

    # -------------------------------------------------------------------------
    # Color Shortcuts
    # -------------------------------------------------------------------------

    def red(self) -> Self:
        """Apply red text color in-place."""
        self._styles["color"] = "red"
        self._notify()
        return self

    def blue(self) -> Self:
        """Apply blue text color in-place."""
        self._styles["color"] = "blue"
        self._notify()
        return self

    def green(self) -> Self:
        """Apply green text color in-place."""
        self._styles["color"] = "green"
        self._notify()
        return self

    def yellow(self) -> Self:
        """Apply yellow text color in-place."""
        self._styles["color"] = "#b8860b"
        self._notify()
        return self

    def orange(self) -> Self:
        """Apply orange text color in-place."""
        self._styles["color"] = "orange"
        self._notify()
        return self

    def purple(self) -> Self:
        """Apply purple text color in-place."""
        self._styles["color"] = "purple"
        self._notify()
        return self

    def gray(self) -> Self:
        """Apply gray text color in-place."""
        self._styles["color"] = "gray"
        self._notify()
        return self

    def white(self) -> Self:
        """Apply white text color in-place."""
        self._styles["color"] = "white"
        self._notify()
        return self

    def black(self) -> Self:
        """Apply black text color in-place."""
        self._styles["color"] = "black"
        self._notify()
        return self

    # -------------------------------------------------------------------------
    # Size Shortcuts
    # -------------------------------------------------------------------------

    def xs(self) -> Self:
        """Apply extra-small text size (12px) in-place."""
        self._styles["font-size"] = "12px"
        self._notify()
        return self

    def small(self) -> Self:
        """Apply small text size (14px) in-place."""
        self._styles["font-size"] = "14px"
        self._notify()
        return self

    def medium(self) -> Self:
        """Apply medium text size (16px) in-place."""
        self._styles["font-size"] = "16px"
        self._notify()
        return self

    def large(self) -> Self:
        """Apply large text size (20px) in-place."""
        self._styles["font-size"] = "20px"
        self._notify()
        return self

    def xl(self) -> Self:
        """Apply extra-large text size (24px) in-place."""
        self._styles["font-size"] = "24px"
        self._notify()
        return self

    def xxl(self) -> Self:
        """Apply 2x extra-large text size (32px) in-place."""
        self._styles["font-size"] = "32px"
        self._notify()
        return self

    # -------------------------------------------------------------------------
    # Style Presets
    # -------------------------------------------------------------------------

    def success(self) -> Self:
        """Apply success style (green) in-place."""
        self._styles["color"] = "#2e7d32"
        self._styles["background-color"] = "#e8f5e9"
        self._styles["padding"] = "2px 6px"
        self._styles["border-radius"] = "4px"
        self._notify()
        return self

    def warning(self) -> Self:
        """Apply warning style (orange) in-place."""
        self._styles["color"] = "#e65100"
        self._styles["background-color"] = "#fff3e0"
        self._styles["padding"] = "2px 6px"
        self._styles["border-radius"] = "4px"
        self._notify()
        return self

    def error(self) -> Self:
        """Apply error style (red) in-place."""
        self._styles["color"] = "#c62828"
        self._styles["background-color"] = "#ffebee"
        self._styles["padding"] = "2px 6px"
        self._styles["border-radius"] = "4px"
        self._notify()
        return self

    def info(self) -> Self:
        """Apply info style (blue) in-place."""
        self._styles["color"] = "#1565c0"
        self._styles["background-color"] = "#e3f2fd"
        self._styles["padding"] = "2px 6px"
        self._styles["border-radius"] = "4px"
        self._notify()
        return self

    def badge(self) -> Self:
        """Apply badge/pill style in-place."""
        self._styles["background-color"] = "#e0e0e0"
        self._styles["padding"] = "4px 10px"
        self._styles["border-radius"] = "12px"
        self._styles["font-size"] = "0.85em"
        self._styles["font-weight"] = "500"
        self._notify()
        return self

    # -------------------------------------------------------------------------
    # Style Methods (require value arguments)
    # -------------------------------------------------------------------------

    def color(self, value: ColorValue) -> Self:
        """Apply specified text color in-place."""
        self._styles["color"] = _to_css(value)
        self._notify()
        return self

    def background(self, value: ColorValue) -> Self:
        """Apply specified background color in-place."""
        self._styles["background-color"] = _to_css(value)
        self._notify()
        return self

    def font_size(self, value: SizeValue) -> Self:
        """Apply specified font size in-place."""
        self._styles["font-size"] = _to_css(value)
        self._notify()
        return self

    def padding(self, value: SpacingValue) -> Self:
        """Apply specified padding in-place."""
        self._styles["padding"] = _to_css(value)
        self._notify()
        return self

    def margin(self, value: SpacingValue) -> Self:
        """Apply specified margin in-place."""
        self._styles["margin"] = _to_css(value)
        self._notify()
        return self

    def border(self, value: BorderValue) -> Self:
        """Apply specified border in-place."""
        self._styles["border"] = _to_css(value)
        self._notify()
        return self

    def border_radius(self, value: SizeValue) -> Self:
        """Apply specified border radius in-place."""
        self._styles["border-radius"] = _to_css(value)
        self._notify()
        return self

    # -------------------------------------------------------------------------
    # Arithmetic Operations (return HTMLInt or HTMLFloat)
    # -------------------------------------------------------------------------

    def _preserve_settings(self, result: HTMLInt | HTMLFloat) -> HTMLInt | HTMLFloat:
        """Copy settings to a new HTMLInt or HTMLFloat."""
        result._styles = self._styles.copy()
        result._css_classes = self._css_classes.copy()
        result._tag = self._tag
        result._display_format = self._display_format
        result._format_options = self._format_options.copy()
        result._obs_id = self._obs_id  # Preserve ID so updates still work
        return result

    def __add__(self, other: Any) -> Any:  # type: ignore[override]
        """Add: HTMLInt + number."""
        from animaid.html_float import HTMLFloat

        result: Any
        if isinstance(other, float) and not isinstance(other, int):
            result = HTMLFloat(int(self) + other)
            return self._preserve_settings(result)
        elif isinstance(other, HTMLFloat):
            result = HTMLFloat(int(self) + float(other))
            return self._preserve_settings(result)
        else:
            result = HTMLInt(int.__add__(self, int(other)))
            return self._preserve_settings(result)

    def __radd__(self, other: Any) -> Any:  # type: ignore[override]
        """Reverse add: number + HTMLInt."""
        return self.__add__(other)

    def __sub__(self, other: Any) -> Any:  # type: ignore[override]
        """Subtract: HTMLInt - number."""
        from animaid.html_float import HTMLFloat

        result: Any
        if isinstance(other, float) and not isinstance(other, int):
            result = HTMLFloat(int(self) - other)
            return self._preserve_settings(result)
        elif isinstance(other, HTMLFloat):
            result = HTMLFloat(int(self) - float(other))
            return self._preserve_settings(result)
        else:
            result = HTMLInt(int.__sub__(self, int(other)))
            return self._preserve_settings(result)

    def __rsub__(self, other: Any) -> Any:  # type: ignore[override]
        """Reverse subtract: number - HTMLInt."""
        from animaid.html_float import HTMLFloat

        result: Any
        if isinstance(other, float):
            result = HTMLFloat(other - int(self))
            return self._preserve_settings(result)
        else:
            result = HTMLInt(other - int(self))
            return self._preserve_settings(result)

    def __mul__(self, other: Any) -> Any:  # type: ignore[override]
        """Multiply: HTMLInt * number."""
        from animaid.html_float import HTMLFloat

        result: Any
        if isinstance(other, float) and not isinstance(other, int):
            result = HTMLFloat(int(self) * other)
            return self._preserve_settings(result)
        elif isinstance(other, HTMLFloat):
            result = HTMLFloat(int(self) * float(other))
            return self._preserve_settings(result)
        else:
            result = HTMLInt(int.__mul__(self, int(other)))
            return self._preserve_settings(result)

    def __rmul__(self, other: Any) -> Any:  # type: ignore[override]
        """Reverse multiply: number * HTMLInt."""
        return self.__mul__(other)

    def __truediv__(self, other: Any) -> Any:  # type: ignore[override]
        """True divide: HTMLInt / number (always returns HTMLFloat)."""
        from animaid.html_float import HTMLFloat

        result = HTMLFloat(int(self) / other)
        return self._preserve_settings(result)

    def __rtruediv__(self, other: Any) -> Any:  # type: ignore[override]
        """Reverse true divide: number / HTMLInt."""
        from animaid.html_float import HTMLFloat

        result = HTMLFloat(other / int(self))
        return self._preserve_settings(result)

    def __floordiv__(self, other: Any) -> Any:  # type: ignore[override]
        """Floor divide: HTMLInt // number."""
        result = HTMLInt(int(self) // int(other))
        return self._preserve_settings(result)

    def __rfloordiv__(self, other: Any) -> Any:  # type: ignore[override]
        """Reverse floor divide: number // HTMLInt."""
        result = HTMLInt(int(other) // int(self))
        return self._preserve_settings(result)

    def __mod__(self, other: Any) -> Any:  # type: ignore[override]
        """Modulo: HTMLInt % number."""
        result = HTMLInt(int.__mod__(self, other))
        return self._preserve_settings(result)

    def __rmod__(self, other: Any) -> Any:  # type: ignore[override]
        """Reverse modulo: number % HTMLInt."""
        result = HTMLInt(other % int(self))
        return self._preserve_settings(result)

    def __pow__(self, other: Any) -> Any:  # type: ignore[override]
        """Power: HTMLInt ** number."""
        result = HTMLInt(int.__pow__(self, other))
        return self._preserve_settings(result)

    def __neg__(self) -> Any:
        """Negate: -HTMLInt."""
        result = HTMLInt(-int(self))
        return self._preserve_settings(result)

    def __pos__(self) -> Any:
        """Positive: +HTMLInt."""
        result = HTMLInt(+int(self))
        return self._preserve_settings(result)

    def __abs__(self) -> Any:
        """Absolute value: abs(HTMLInt)."""
        result = HTMLInt(abs(int(self)))
        return self._preserve_settings(result)

    def __repr__(self) -> str:
        """Return a detailed representation for debugging."""
        format_info = ""
        if self._display_format != "default":
            format_info = f", format={self._display_format!r}"
        styles_repr = ", ".join(f"{k}={v!r}" for k, v in self._styles.items())
        if styles_repr:
            return f"HTMLInt({int(self)}{format_info}, {styles_repr})"
        return f"HTMLInt({int(self)}{format_info})"
