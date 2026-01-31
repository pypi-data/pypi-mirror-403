"""HTMLSpacer - Empty space for layout control."""

from __future__ import annotations

import uuid

from animaid.css_types import CSSValue, Size
from animaid.html_object import HTMLObject


def _to_css(value: object) -> str:
    """Convert a value to its CSS string representation."""
    if hasattr(value, "to_css"):
        return str(value.to_css())
    return str(value)


class HTMLSpacer(HTMLObject):
    """An empty space element for layout control.

    HTMLSpacer creates invisible space between elements. It can be
    fixed-size or flexible (expands to fill available space in flex containers).

    Examples:
        >>> from animaid import HTMLSpacer, HTMLRow, HTMLButton

        >>> # Fixed height spacer
        >>> spacer = HTMLSpacer().height(20)

        >>> # Flexible spacer (pushes items apart in flex containers)
        >>> row = HTMLRow([
        ...     HTMLButton("Left"),
        ...     HTMLSpacer().flex(),  # Takes remaining space
        ...     HTMLButton("Right"),
        ... ])

        >>> # Fixed width spacer in a row
        >>> row = HTMLRow([item1, HTMLSpacer().width(50), item2])
    """

    _styles: dict[str, str]
    _css_classes: list[str]
    _obs_id: str

    def __init__(self, **styles: str | CSSValue) -> None:
        """Create a new spacer.

        Args:
            **styles: Initial CSS styles.
        """
        self._styles = {}
        self._css_classes = []
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
            pass

    def render(self) -> str:
        """Render the spacer.

        Returns:
            HTML string for the spacer div.
        """
        style_parts = []
        for key, value in self._styles.items():
            style_parts.append(f"{key}: {value}")

        if style_parts:
            style_str = "; ".join(style_parts)
            return f'<div style="{style_str}"></div>'
        return "<div></div>"

    def __html__(self) -> str:
        """Jinja2 auto-escaping protocol."""
        return self.render()

    # =========================================================================
    # Size Methods
    # =========================================================================

    def height(self, size: Size | str | int) -> "HTMLSpacer":
        """Set a fixed height.

        Args:
            size: Height (Size, CSS string, or int pixels).

        Returns:
            Self for method chaining.
        """
        if isinstance(size, int):
            size = Size.px(size)
        self._styles["height"] = _to_css(size)
        self._notify()
        return self

    def width(self, size: Size | str | int) -> "HTMLSpacer":
        """Set a fixed width.

        Args:
            size: Width (Size, CSS string, or int pixels).

        Returns:
            Self for method chaining.
        """
        if isinstance(size, int):
            size = Size.px(size)
        self._styles["width"] = _to_css(size)
        self._notify()
        return self

    def size(self, width: Size | str | int, height: Size | str | int) -> "HTMLSpacer":
        """Set both width and height.

        Args:
            width: Width value.
            height: Height value.

        Returns:
            Self for method chaining.
        """
        self.width(width)
        self.height(height)
        return self

    # =========================================================================
    # Flex Methods
    # =========================================================================

    def flex(self, grow: int = 1) -> "HTMLSpacer":
        """Make the spacer flexible (expands to fill available space).

        In a flex container (HTMLRow or HTMLColumn), a flex spacer will
        expand to take up any remaining space, pushing other items apart.

        Args:
            grow: Flex grow value (default 1).

        Returns:
            Self for method chaining.

        Example:
            >>> # Push button to the right
            >>> row = HTMLRow([
            ...     HTMLString("Title"),
            ...     HTMLSpacer().flex(),
            ...     HTMLButton("Action"),
            ... ])
        """
        self._styles["flex"] = str(grow)
        self._notify()
        return self

    def grow(self, value: int = 1) -> "HTMLSpacer":
        """Set flex-grow value.

        Args:
            value: Flex grow value.

        Returns:
            Self for method chaining.
        """
        self._styles["flex-grow"] = str(value)
        self._notify()
        return self

    def shrink(self, value: int = 0) -> "HTMLSpacer":
        """Set flex-shrink value.

        Args:
            value: Flex shrink value.

        Returns:
            Self for method chaining.
        """
        self._styles["flex-shrink"] = str(value)
        self._notify()
        return self

    # =========================================================================
    # Presets
    # =========================================================================

    def xs(self) -> "HTMLSpacer":
        """Extra small spacer (4px).

        Returns:
            Self for method chaining.
        """
        self._styles["height"] = "4px"
        self._styles["width"] = "4px"
        self._notify()
        return self

    def sm(self) -> "HTMLSpacer":
        """Small spacer (8px).

        Returns:
            Self for method chaining.
        """
        self._styles["height"] = "8px"
        self._styles["width"] = "8px"
        self._notify()
        return self

    def md(self) -> "HTMLSpacer":
        """Medium spacer (16px).

        Returns:
            Self for method chaining.
        """
        self._styles["height"] = "16px"
        self._styles["width"] = "16px"
        self._notify()
        return self

    def lg(self) -> "HTMLSpacer":
        """Large spacer (24px).

        Returns:
            Self for method chaining.
        """
        self._styles["height"] = "24px"
        self._styles["width"] = "24px"
        self._notify()
        return self

    def xl(self) -> "HTMLSpacer":
        """Extra large spacer (32px).

        Returns:
            Self for method chaining.
        """
        self._styles["height"] = "32px"
        self._styles["width"] = "32px"
        self._notify()
        return self

    # =========================================================================
    # HTMLObject required methods
    # =========================================================================

    def styled(self, **styles: str | CSSValue) -> "HTMLSpacer":
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

    def add_class(self, *class_names: str) -> "HTMLSpacer":
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
