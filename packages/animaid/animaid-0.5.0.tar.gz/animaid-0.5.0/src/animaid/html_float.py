"""HTMLFloat - A float subclass with HTML rendering capabilities."""

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
    pass


def _to_css(value: object) -> str:
    """Convert a value to its CSS string representation."""
    if hasattr(value, "to_css"):
        return str(value.to_css())
    return str(value)


class HTMLFloat(HTMLObject, float):
    """A float subclass that renders as styled HTML.

    HTMLFloat behaves like a regular Python float but includes methods
    for applying CSS styles, number formatting, and rendering to HTML.
    All styling methods modify the object in-place and return self
    for method chaining.

    Examples:
        >>> n = HTMLFloat(3.14159)
        >>> n.bold().red().render()
        '<span style="font-weight: bold; color: red">3.14159</span>'

        >>> HTMLFloat(1234.5678).comma().render()
        '<span>1,234.5678</span>'

        >>> HTMLFloat(0.856).percent().render()
        '<span>85.60%</span>'

        >>> HTMLFloat(3.14159).decimal(2).render()
        '<span>3.14</span>'
    """

    _styles: dict[str, str]
    _css_classes: list[str]
    _tag: str
    _display_format: str
    _format_options: dict[str, object]
    _obs_id: str

    def __new__(cls, value: float = 0.0, **styles: str | CSSValue) -> Self:
        """Create a new HTMLFloat instance.

        Args:
            value: The float value.
            **styles: Initial CSS styles (underscores converted to hyphens).

        Returns:
            A new HTMLFloat instance.
        """
        instance = super().__new__(cls, value)
        return instance

    def __init__(self, value: float = 0.0, **styles: str | CSSValue) -> None:
        """Initialize styles for the HTMLFloat.

        Args:
            value: The float value (handled by __new__).
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
        """Create a copy of this HTMLFloat with modified settings.

        This method is used internally for operations that must return
        a new object (like arithmetic operations).

        Args:
            new_styles: Styles to merge with existing styles.
            new_classes: Classes to add to existing classes.
            new_tag: New HTML tag to use.
            new_format: New display format.
            new_format_options: New format options.

        Returns:
            A new HTMLFloat with combined settings.
        """
        result = HTMLFloat(float(self))
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
        """Format the float value based on display format settings."""
        value = float(self)

        if self._display_format == "comma":
            return f"{value:,}"
        elif self._display_format == "currency":
            symbol = self._format_options.get("symbol", "$")
            decimals = self._format_options.get("decimals", 2)
            return f"{symbol}{value:,.{decimals}f}"
        elif self._display_format == "percent":
            decimals = self._format_options.get("decimals", 2)
            return f"{value * 100:.{decimals}f}%"
        elif self._display_format == "decimal":
            places = self._format_options.get("places", 2)
            return f"{value:.{places}f}"
        elif self._display_format == "scientific":
            precision = self._format_options.get("precision", 2)
            return f"{value:.{precision}e}"
        elif self._display_format == "significant":
            figures = self._format_options.get("figures", 3)
            return f"{value:.{figures}g}"
        else:
            return str(value)

    def render(self) -> str:
        """Return HTML representation of this float.

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
            >>> HTMLFloat(1234567.89).comma().render()
            '<span>1,234,567.89</span>'
        """
        self._display_format = "comma"
        self._notify()
        return self

    def currency(self, symbol: str = "$", decimals: int = 2) -> Self:
        """Apply currency formatting in-place.

        Args:
            symbol: Currency symbol (default "$")
            decimals: Number of decimal places (default 2)

        Examples:
            >>> HTMLFloat(1000.5).currency().render()
            '<span>$1,000.50</span>'
            >>> HTMLFloat(1000.5).currency("€", 0).render()
            '<span>€1,000</span>'
        """
        self._display_format = "currency"
        self._format_options["symbol"] = symbol
        self._format_options["decimals"] = decimals
        self._notify()
        return self

    def percent(self, decimals: int = 2) -> Self:
        """Apply percentage formatting in-place.

        The value is multiplied by 100 for display.

        Args:
            decimals: Number of decimal places (default 2)

        Examples:
            >>> HTMLFloat(0.856).percent().render()
            '<span>85.60%</span>'
            >>> HTMLFloat(0.5).percent(0).render()
            '<span>50%</span>'
        """
        self._display_format = "percent"
        self._format_options["decimals"] = decimals
        self._notify()
        return self

    def decimal(self, places: int = 2) -> Self:
        """Apply fixed decimal places formatting in-place.

        Args:
            places: Number of decimal places (default 2)

        Examples:
            >>> HTMLFloat(3.14159).decimal(2).render()
            '<span>3.14</span>'
            >>> HTMLFloat(3.1).decimal(4).render()
            '<span>3.1000</span>'
        """
        self._display_format = "decimal"
        self._format_options["places"] = places
        self._notify()
        return self

    def scientific(self, precision: int = 2) -> Self:
        """Apply scientific notation formatting in-place.

        Args:
            precision: Number of decimal places in mantissa (default 2)

        Examples:
            >>> HTMLFloat(1234567.89).scientific().render()
            '<span>1.23e+06</span>'
        """
        self._display_format = "scientific"
        self._format_options["precision"] = precision
        self._notify()
        return self

    def significant(self, figures: int = 3) -> Self:
        """Apply significant figures formatting in-place.

        Args:
            figures: Number of significant figures (default 3)

        Examples:
            >>> HTMLFloat(3.14159).significant(3).render()
            '<span>3.14</span>'
            >>> HTMLFloat(0.00123456).significant(2).render()
            '<span>0.0012</span>'
        """
        self._display_format = "significant"
        self._format_options["figures"] = figures
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
    # Arithmetic Operations (always return HTMLFloat)
    # -------------------------------------------------------------------------

    def _preserve_settings(self, result: HTMLFloat) -> HTMLFloat:
        """Copy settings to a new HTMLFloat."""
        result._styles = self._styles.copy()
        result._css_classes = self._css_classes.copy()
        result._tag = self._tag
        result._display_format = self._display_format
        result._format_options = self._format_options.copy()
        result._obs_id = self._obs_id  # Preserve ID so updates still work
        return result

    def __add__(self, other: int | float) -> HTMLFloat:
        """Add: HTMLFloat + number."""
        result = HTMLFloat(float(self) + float(other))
        return self._preserve_settings(result)

    def __radd__(self, other: int | float) -> HTMLFloat:
        """Reverse add: number + HTMLFloat."""
        return self.__add__(other)

    def __sub__(self, other: int | float) -> HTMLFloat:
        """Subtract: HTMLFloat - number."""
        result = HTMLFloat(float(self) - float(other))
        return self._preserve_settings(result)

    def __rsub__(self, other: int | float) -> HTMLFloat:
        """Reverse subtract: number - HTMLFloat."""
        result = HTMLFloat(float(other) - float(self))
        return self._preserve_settings(result)

    def __mul__(self, other: int | float) -> HTMLFloat:
        """Multiply: HTMLFloat * number."""
        result = HTMLFloat(float(self) * float(other))
        return self._preserve_settings(result)

    def __rmul__(self, other: int | float) -> HTMLFloat:
        """Reverse multiply: number * HTMLFloat."""
        return self.__mul__(other)

    def __truediv__(self, other: int | float) -> HTMLFloat:
        """True divide: HTMLFloat / number."""
        result = HTMLFloat(float(self) / float(other))
        return self._preserve_settings(result)

    def __rtruediv__(self, other: int | float) -> HTMLFloat:
        """Reverse true divide: number / HTMLFloat."""
        result = HTMLFloat(float(other) / float(self))
        return self._preserve_settings(result)

    def __floordiv__(self, other: int | float) -> HTMLFloat:
        """Floor divide: HTMLFloat // number."""
        result = HTMLFloat(float(self) // float(other))
        return self._preserve_settings(result)

    def __rfloordiv__(self, other: int | float) -> HTMLFloat:
        """Reverse floor divide: number // HTMLFloat."""
        result = HTMLFloat(float(other) // float(self))
        return self._preserve_settings(result)

    def __mod__(self, other: int | float) -> HTMLFloat:
        """Modulo: HTMLFloat % number."""
        result = HTMLFloat(float(self) % float(other))
        return self._preserve_settings(result)

    def __rmod__(self, other: int | float) -> HTMLFloat:
        """Reverse modulo: number % HTMLFloat."""
        result = HTMLFloat(float(other) % float(self))
        return self._preserve_settings(result)

    def __pow__(self, other: Any) -> Any:  # type: ignore[override]
        """Power: HTMLFloat ** number."""
        result = HTMLFloat(float(self) ** float(other))
        return self._preserve_settings(result)

    def __neg__(self) -> HTMLFloat:
        """Negate: -HTMLFloat."""
        result = HTMLFloat(-float(self))
        return self._preserve_settings(result)

    def __pos__(self) -> HTMLFloat:
        """Positive: +HTMLFloat."""
        result = HTMLFloat(+float(self))
        return self._preserve_settings(result)

    def __abs__(self) -> HTMLFloat:
        """Absolute value: abs(HTMLFloat)."""
        result = HTMLFloat(abs(float(self)))
        return self._preserve_settings(result)

    def __repr__(self) -> str:
        """Return a detailed representation for debugging."""
        format_info = ""
        if self._display_format != "default":
            format_info = f", format={self._display_format!r}"
        styles_repr = ", ".join(f"{k}={v!r}" for k, v in self._styles.items())
        if styles_repr:
            return f"HTMLFloat({float(self)}{format_info}, {styles_repr})"
        return f"HTMLFloat({float(self)}{format_info})"
