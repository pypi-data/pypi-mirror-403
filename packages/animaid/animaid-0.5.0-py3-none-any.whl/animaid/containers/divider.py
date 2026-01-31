"""HTMLDivider - Visual separator for content."""

from __future__ import annotations

import html
import uuid

from animaid.css_types import Color, CSSValue, DividerStyle, Size
from animaid.html_object import HTMLObject


def _to_css(value: object) -> str:
    """Convert a value to its CSS string representation."""
    if hasattr(value, "to_css"):
        return str(value.to_css())
    return str(value)


class HTMLDivider(HTMLObject):
    """A visual separator (horizontal or vertical line).

    HTMLDivider creates a line to visually separate content sections.
    It can be horizontal (default) or vertical (for use in rows).

    Examples:
        >>> from animaid import HTMLDivider
        >>> divider = HTMLDivider()  # Simple horizontal line

        >>> # With label
        >>> divider = HTMLDivider("OR")

        >>> # Vertical divider for rows
        >>> divider = HTMLDivider().vertical()

        >>> # Styled divider
        >>> divider = HTMLDivider().dashed().color("gray")
    """

    _styles: dict[str, str]
    _css_classes: list[str]
    _label: str | None
    _is_vertical: bool
    _obs_id: str

    def __init__(
        self,
        label: str | None = None,
        **styles: str | CSSValue,
    ) -> None:
        """Create a new divider.

        Args:
            label: Optional text label to display in the middle of the divider.
            **styles: Initial CSS styles.
        """
        self._label = label
        self._is_vertical = False
        self._styles = {}
        self._css_classes = []
        self._obs_id = str(uuid.uuid4())

        # Default styles
        self._styles["border-color"] = "#e5e7eb"
        self._styles["border-style"] = DividerStyle.SOLID.to_css()

        for key, value in styles.items():
            css_key = key.replace("_", "-")
            self._styles[css_key] = _to_css(value)

    def _notify(self) -> None:
        """Publish change notification via pypubsub."""
        try:
            from pubsub import pub

            pub.sendMessage("animaid.changed", obs_id=self._obs_id)
        except ImportError:
            pass

    def render(self) -> str:
        """Render the divider.

        Returns:
            HTML string for the divider.
        """
        if self._is_vertical:
            return self._render_vertical()
        return self._render_horizontal()

    def _render_horizontal(self) -> str:
        """Render a horizontal divider."""
        border_color = self._styles.get("border-color", "#e5e7eb")
        border_style = self._styles.get("border-style", "solid")
        border_width = self._styles.get("border-width", "1px")
        margin = self._styles.get("margin", "16px 0")

        if self._label:
            # Divider with label: two lines with text in between
            escaped_label = html.escape(self._label)
            line_style = (
                f"flex: 1; border-bottom: {border_width} {border_style} {border_color};"
            )
            label_style = "padding: 0 12px; color: #6b7280; font-size: 0.875em;"
            return (
                f'<div style="display: flex; align-items: center; margin: {margin};">'
                f'<div style="{line_style}"></div>'
                f'<span style="{label_style}">{escaped_label}</span>'
                f'<div style="{line_style}"></div>'
                f"</div>"
            )
        else:
            # Simple horizontal rule
            style = f"border: none; border-top: {border_width} {border_style} {border_color}; margin: {margin};"
            return f'<hr style="{style}">'

    def _render_vertical(self) -> str:
        """Render a vertical divider."""
        border_color = self._styles.get("border-color", "#e5e7eb")
        border_style = self._styles.get("border-style", "solid")
        border_width = self._styles.get("border-width", "1px")
        margin = self._styles.get("margin", "0 16px")
        height = self._styles.get("height", "auto")
        align_self = self._styles.get("align-self", "stretch")

        style = (
            f"border-left: {border_width} {border_style} {border_color}; "
            f"margin: {margin}; height: {height}; align-self: {align_self};"
        )
        return f'<div style="{style}"></div>'

    def __html__(self) -> str:
        """Jinja2 auto-escaping protocol."""
        return self.render()

    # =========================================================================
    # Orientation Methods
    # =========================================================================

    def vertical(self) -> "HTMLDivider":
        """Make the divider vertical (for use in flex rows).

        Returns:
            Self for method chaining.
        """
        self._is_vertical = True
        self._notify()
        return self

    def horizontal(self) -> "HTMLDivider":
        """Make the divider horizontal (default).

        Returns:
            Self for method chaining.
        """
        self._is_vertical = False
        self._notify()
        return self

    # =========================================================================
    # Style Methods
    # =========================================================================

    def style(self, value: DividerStyle | str) -> "HTMLDivider":
        """Set the line style.

        Args:
            value: DividerStyle enum or CSS border-style string.

        Returns:
            Self for method chaining.
        """
        if isinstance(value, DividerStyle):
            self._styles["border-style"] = value.to_css()
        else:
            self._styles["border-style"] = value
        self._notify()
        return self

    def solid(self) -> "HTMLDivider":
        """Set solid line style.

        Returns:
            Self for method chaining.
        """
        self._styles["border-style"] = DividerStyle.SOLID.to_css()
        self._notify()
        return self

    def dashed(self) -> "HTMLDivider":
        """Set dashed line style.

        Returns:
            Self for method chaining.
        """
        self._styles["border-style"] = DividerStyle.DASHED.to_css()
        self._notify()
        return self

    def dotted(self) -> "HTMLDivider":
        """Set dotted line style.

        Returns:
            Self for method chaining.
        """
        self._styles["border-style"] = DividerStyle.DOTTED.to_css()
        self._notify()
        return self

    # =========================================================================
    # Color and Size Methods
    # =========================================================================

    def color(self, value: Color | str) -> "HTMLDivider":
        """Set the divider color.

        Args:
            value: Color enum or CSS color string.

        Returns:
            Self for method chaining.
        """
        self._styles["border-color"] = _to_css(value)
        self._notify()
        return self

    def thickness(self, size: Size | str | int) -> "HTMLDivider":
        """Set the divider thickness.

        Args:
            size: Thickness (Size, CSS string, or int pixels).

        Returns:
            Self for method chaining.
        """
        if isinstance(size, int):
            size = Size.px(size)
        self._styles["border-width"] = _to_css(size)
        self._notify()
        return self

    def margin(self, size: Size | str) -> "HTMLDivider":
        """Set the margin around the divider.

        Args:
            size: Margin size.

        Returns:
            Self for method chaining.
        """
        self._styles["margin"] = _to_css(size)
        self._notify()
        return self

    # =========================================================================
    # Label Methods
    # =========================================================================

    def set_label(self, text: str | None) -> "HTMLDivider":
        """Set or remove the divider label.

        Args:
            text: Label text, or None to remove.

        Returns:
            Self for method chaining.
        """
        self._label = text
        self._notify()
        return self

    # =========================================================================
    # Presets
    # =========================================================================

    def subtle(self) -> "HTMLDivider":
        """Apply subtle divider styling (lighter color).

        Returns:
            Self for method chaining.
        """
        self._styles["border-color"] = "#f3f4f6"
        self._notify()
        return self

    def bold(self) -> "HTMLDivider":
        """Apply bold divider styling (thicker, darker).

        Returns:
            Self for method chaining.
        """
        self._styles["border-color"] = "#374151"
        self._styles["border-width"] = "2px"
        self._notify()
        return self

    # =========================================================================
    # HTMLObject required methods
    # =========================================================================

    def styled(self, **styles: str | CSSValue) -> "HTMLDivider":
        """Apply additional inline styles.

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

    def add_class(self, *class_names: str) -> "HTMLDivider":
        """Add CSS classes.

        Args:
            *class_names: CSS class names to add.

        Returns:
            Self for method chaining.
        """
        for name in class_names:
            if name not in self._css_classes:
                self._css_classes.append(name)
        self._notify()
        return self
