"""HTMLString - A str subclass with HTML rendering capabilities."""

from __future__ import annotations

import html
import uuid
from typing import Any, Self

from animaid.css_types import (
    BorderValue,
    ColorValue,
    CSSValue,
    Display,
    SizeValue,
    SpacingValue,
)
from animaid.html_object import HTMLObject


def _to_css(value: object) -> str:
    """Convert a value to its CSS string representation."""
    if hasattr(value, "to_css"):
        return str(value.to_css())
    return str(value)


class HTMLString(HTMLObject, str):
    """A string subclass that renders as styled HTML.

    HTMLString behaves like a regular Python string but includes
    methods for applying CSS styles and rendering to HTML.
    All styling methods modify the object in-place and return self
    for method chaining.

    Examples:
        >>> s = HTMLString("Hello World")
        >>> s.bold().color("red").render()
        '<span style="font-weight: bold; color: red">Hello World</span>'

        >>> s = HTMLString("Click me", color="blue", text_decoration="underline")
        >>> s.render()
        '<span style="color: blue; text-decoration: underline">Click me</span>'
    """

    _styles: dict[str, str]
    _css_classes: list[str]
    _tag: str
    _obs_id: str

    def __new__(cls, content: str = "", **styles: str | CSSValue) -> Self:
        """Create a new HTMLString instance.

        Args:
            content: The string content.
            **styles: Initial CSS styles (underscores converted to hyphens).
                      Accepts both strings and CSS type objects (Color, Size, etc.)

        Returns:
            A new HTMLString instance.
        """
        instance = super().__new__(cls, content)
        return instance

    def __init__(self, content: str = "", **styles: str | CSSValue) -> None:
        """Initialize styles for the HTMLString.

        Args:
            content: The string content (handled by __new__).
            **styles: CSS property-value pairs, e.g., font_size="16px".
                      Accepts both strings and CSS type objects.
        """
        self._styles = {}
        self._css_classes = []
        self._tag = "span"
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

    def _copy_with_styles(
        self,
        new_styles: dict[str, str] | None = None,
        new_classes: list[str] | None = None,
        new_tag: str | None = None,
    ) -> Self:
        """Create a copy of this HTMLString with modified styles.

        This method is used internally for operations that must return
        a new object (like slicing or concatenation).

        Args:
            new_styles: Styles to merge with existing styles.
            new_classes: Classes to add to existing classes.
            new_tag: New HTML tag to use.

        Returns:
            A new HTMLString with combined styles/classes.
        """
        result = HTMLString(str(self))
        result._styles = self._styles.copy()
        result._css_classes = self._css_classes.copy()
        result._tag = self._tag
        result._obs_id = self._obs_id  # Preserve ID so updates still work

        if new_styles:
            result._styles.update(new_styles)
        if new_classes:
            result._css_classes.extend(new_classes)
        if new_tag:
            result._tag = new_tag

        return result  # type: ignore[return-value]

    def styled(self, **styles: str | CSSValue) -> Self:
        """Apply additional inline styles in-place.

        Style names use Python convention (underscores) and are
        converted to CSS convention (hyphens) automatically.

        Args:
            **styles: CSS property-value pairs. Accepts strings and CSS types.
                      e.g., font_size="16px" or font_size=Size.px(16)

        Returns:
            Self for method chaining.

        Example:
            >>> s = HTMLString("Hello").styled(color="red", font_size="20px")
            >>> s.render()
            '<span style="color: red; font-size: 20px">Hello</span>'

            >>> s = HTMLString("Hello").styled(color=Color.red, font_size=Size.px(20))
            >>> s.render()
            '<span style="color: red; font-size: 20px">Hello</span>'
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

        Example:
            >>> s = HTMLString("Hello").add_class("highlight", "important")
            >>> s.render()
            '<span class="highlight important">Hello</span>'
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

        Example:
            >>> s = HTMLString("Hello").tag("strong").render()
            '<strong>Hello</strong>'
        """
        self._tag = tag_name
        self._notify()
        return self

    def render(self) -> str:
        """Return HTML representation of this string.

        The string content is HTML-escaped to prevent XSS.

        Returns:
            A string containing valid HTML.

        Example:
            >>> HTMLString("<script>alert('xss')</script>").render()
            '<span>&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;</span>'
        """
        escaped_content = html.escape(str(self))
        attrs = self._build_attributes()

        if attrs:
            return f"<{self._tag} {attrs}>{escaped_content}</{self._tag}>"
        else:
            return f"<{self._tag}>{escaped_content}</{self._tag}>"

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

    def uppercase(self) -> Self:
        """Apply uppercase text transform in-place."""
        self._styles["text-transform"] = "uppercase"
        self._notify()
        return self

    def lowercase(self) -> Self:
        """Apply lowercase text transform in-place."""
        self._styles["text-transform"] = "lowercase"
        self._notify()
        return self

    def capitalize(self) -> Self:  # type: ignore[override]
        """Apply capitalize text transform in-place."""
        self._styles["text-transform"] = "capitalize"
        self._notify()
        return self

    def nowrap(self) -> Self:
        """Apply nowrap white-space style in-place."""
        self._styles["white-space"] = "nowrap"
        self._notify()
        return self

    def monospace(self) -> Self:
        """Apply monospace font in-place."""
        self._styles["font-family"] = "monospace"
        self._notify()
        return self

    # -------------------------------------------------------------------------
    # Color Shortcuts (beginner-friendly)
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
        self._styles["color"] = "#b8860b"  # Dark golden for readability
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

    def pink(self) -> Self:
        """Apply pink text color in-place."""
        self._styles["color"] = "deeppink"
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
    # Background Color Shortcuts (beginner-friendly)
    # -------------------------------------------------------------------------

    def bg_red(self) -> Self:
        """Apply red background in-place."""
        self._styles["background-color"] = "#ffebee"
        self._notify()
        return self

    def bg_blue(self) -> Self:
        """Apply blue background in-place."""
        self._styles["background-color"] = "#e3f2fd"
        self._notify()
        return self

    def bg_green(self) -> Self:
        """Apply green background in-place."""
        self._styles["background-color"] = "#e8f5e9"
        self._notify()
        return self

    def bg_yellow(self) -> Self:
        """Apply yellow background in-place."""
        self._styles["background-color"] = "#fffde7"
        self._notify()
        return self

    def bg_orange(self) -> Self:
        """Apply orange background in-place."""
        self._styles["background-color"] = "#fff3e0"
        self._notify()
        return self

    def bg_purple(self) -> Self:
        """Apply purple background in-place."""
        self._styles["background-color"] = "#f3e5f5"
        self._notify()
        return self

    def bg_pink(self) -> Self:
        """Apply pink background in-place."""
        self._styles["background-color"] = "#fce4ec"
        self._notify()
        return self

    def bg_gray(self) -> Self:
        """Apply gray background in-place."""
        self._styles["background-color"] = "#f5f5f5"
        self._notify()
        return self

    def bg_white(self) -> Self:
        """Apply white background in-place."""
        self._styles["background-color"] = "white"
        self._notify()
        return self

    def bg_black(self) -> Self:
        """Apply black background in-place."""
        self._styles["background-color"] = "black"
        self._notify()
        return self

    # -------------------------------------------------------------------------
    # Size Shortcuts (beginner-friendly)
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
    # Common Style Presets (beginner-friendly)
    # -------------------------------------------------------------------------

    def highlight(self) -> Self:
        """Apply highlight style (yellow background) in-place."""
        self._styles["background-color"] = "#fff59d"
        self._styles["padding"] = "2px 4px"
        self._notify()
        return self

    def code(self) -> Self:
        """Apply inline code style in-place."""
        self._styles["font-family"] = "monospace"
        self._styles["background-color"] = "#f5f5f5"
        self._styles["padding"] = "2px 6px"
        self._styles["border-radius"] = "4px"
        self._styles["font-size"] = "0.9em"
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

    def muted(self) -> Self:
        """Apply muted/secondary text style in-place."""
        self._styles["color"] = "#757575"
        self._styles["font-size"] = "0.9em"
        self._notify()
        return self

    def link(self) -> Self:
        """Apply link style in-place."""
        self._styles["color"] = "#1976d2"
        self._styles["text-decoration"] = "underline"
        self._notify()
        return self

    # -------------------------------------------------------------------------
    # Style Methods (require value arguments)
    # -------------------------------------------------------------------------

    def color(self, value: ColorValue) -> Self:
        """Apply specified text color in-place.

        Args:
            value: CSS color value (e.g., "red", "#ff0000", Color.red)
        """
        self._styles["color"] = _to_css(value)
        self._notify()
        return self

    def background(self, value: ColorValue) -> Self:
        """Apply specified background color in-place.

        Args:
            value: CSS color value (e.g., "yellow", Color.yellow)
        """
        self._styles["background-color"] = _to_css(value)
        self._notify()
        return self

    def font_size(self, value: SizeValue) -> Self:
        """Apply specified font size in-place.

        Args:
            value: CSS size value (e.g., "16px", Size.px(16), Size.em(1.2))
        """
        self._styles["font-size"] = _to_css(value)
        self._notify()
        return self

    def font_family(self, value: str) -> Self:
        """Apply specified font family in-place.

        Args:
            value: CSS font-family value.
        """
        self._styles["font-family"] = value
        self._notify()
        return self

    def padding(self, value: SpacingValue) -> Self:
        """Apply specified padding in-place.

        Args:
            value: CSS padding value (e.g., "10px", Size.px(10))
        """
        self._styles["padding"] = _to_css(value)
        self._notify()
        return self

    def margin(self, value: SpacingValue) -> Self:
        """Apply specified margin in-place.

        Args:
            value: CSS margin value (e.g., "10px", Size.px(10), Spacing.all(10))
        """
        self._styles["margin"] = _to_css(value)
        self._notify()
        return self

    def border(self, value: BorderValue) -> Self:
        """Apply specified border in-place.

        Args:
            value: CSS border value (e.g., "1px solid black", Border.solid())
        """
        self._styles["border"] = _to_css(value)
        self._notify()
        return self

    def border_radius(self, value: SizeValue) -> Self:
        """Apply specified border radius in-place.

        Args:
            value: CSS border-radius value (e.g., "5px", Size.px(5), Size.percent(50))
        """
        self._styles["border-radius"] = _to_css(value)
        self._notify()
        return self

    def opacity(self, value: str | float) -> Self:
        """Apply specified opacity in-place.

        Args:
            value: CSS opacity value (0.0 to 1.0)
        """
        self._styles["opacity"] = str(value)
        self._notify()
        return self

    def width(self, value: SizeValue) -> Self:
        """Apply specified width in-place.

        Args:
            value: CSS width value (e.g., "100px", Size.px(100), Size.percent(50))
        """
        self._styles["width"] = _to_css(value)
        self._notify()
        return self

    def height(self, value: SizeValue) -> Self:
        """Apply specified height in-place.

        Args:
            value: CSS height value (e.g., "50px", Size.px(50), Size.vh(100))
        """
        self._styles["height"] = _to_css(value)
        self._notify()
        return self

    def display(self, value: Display | str) -> Self:
        """Apply specified display mode in-place.

        Args:
            value: CSS display value (e.g., "block", "flex", Display.FLEX)
        """
        self._styles["display"] = _to_css(value)
        self._notify()
        return self

    # -------------------------------------------------------------------------
    # String operation overrides to preserve HTMLString type
    # -------------------------------------------------------------------------

    def __add__(self, other: str) -> Self:
        """Concatenate strings, preserving styles for this string's content."""
        result = HTMLString(str.__add__(self, other))
        result._styles = self._styles.copy()
        result._css_classes = self._css_classes.copy()
        result._tag = self._tag
        return result  # type: ignore[return-value]

    def __radd__(self, other: str) -> Self:
        """Handle other + HTMLString."""
        result = HTMLString(str.__add__(other, self))
        result._styles = self._styles.copy()
        result._css_classes = self._css_classes.copy()
        result._tag = self._tag
        return result  # type: ignore[return-value]

    def __getitem__(self, key: Any) -> Self:  # type: ignore[override]
        """Slice the string, preserving styles."""
        result = HTMLString(str.__getitem__(self, key))
        result._styles = self._styles.copy()
        result._css_classes = self._css_classes.copy()
        result._tag = self._tag
        return result  # type: ignore[return-value]

    def __repr__(self) -> str:
        """Return a detailed representation for debugging."""
        styles_repr = ", ".join(f"{k}={v!r}" for k, v in self._styles.items())
        if styles_repr:
            return f"HTMLString({str.__repr__(self)}, {styles_repr})"
        return f"HTMLString({str.__repr__(self)})"
