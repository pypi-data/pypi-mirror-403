"""HTMLRow - Horizontal flex container."""

from __future__ import annotations

from typing import Any

from animaid.containers.base import HTMLContainer, _to_css
from animaid.css_types import (
    AlignItems,
    CSSValue,
    FlexWrap,
    JustifyContent,
    Size,
    Spacing,
)


class HTMLRow(HTMLContainer):
    """A horizontal flex container for arranging items in a row.

    HTMLRow uses CSS flexbox with `flex-direction: row` to arrange
    children horizontally. It provides methods for controlling
    alignment, justification, wrapping, and spacing.

    Examples:
        >>> from animaid import HTMLRow, HTMLButton
        >>> row = HTMLRow([
        ...     HTMLButton("Save").primary(),
        ...     HTMLButton("Cancel"),
        ... ])

        >>> # With alignment and gap
        >>> row = HTMLRow([item1, item2, item3]).gap(10).align(AlignItems.CENTER)

        >>> # Button row preset
        >>> row = HTMLRow(buttons).buttons()
    """

    def __init__(
        self,
        children: list[Any] | None = None,
        **styles: str | CSSValue,
    ) -> None:
        """Create a new horizontal row container.

        Args:
            children: List of child elements.
            **styles: Initial CSS styles.
        """
        super().__init__(children, **styles)
        # Set default flex styles
        self._styles["display"] = "flex"
        self._styles["flex-direction"] = "row"

    # =========================================================================
    # Alignment Methods
    # =========================================================================

    def align(self, value: AlignItems | str) -> "HTMLRow":
        """Set vertical alignment of items within the row.

        Args:
            value: AlignItems enum or CSS string (start, center, end, stretch, baseline).

        Returns:
            Self for method chaining.

        Example:
            >>> row.align(AlignItems.CENTER)
            >>> row.align("center")  # Also works
        """
        if isinstance(value, str):
            value = AlignItems(value)
        self._styles["align-items"] = value.to_css()
        self._notify()
        return self

    def justify(self, value: JustifyContent | str) -> "HTMLRow":
        """Set horizontal distribution of items within the row.

        Args:
            value: JustifyContent enum or CSS string
                   (start, center, end, space-between, space-around, space-evenly).

        Returns:
            Self for method chaining.

        Example:
            >>> row.justify(JustifyContent.SPACE_BETWEEN)
            >>> row.justify("space-between")  # Also works
        """
        if isinstance(value, str):
            value = JustifyContent(value)
        self._styles["justify-content"] = value.to_css()
        self._notify()
        return self

    # =========================================================================
    # Wrapping Methods
    # =========================================================================

    def wrap(self, value: FlexWrap | str = FlexWrap.WRAP) -> "HTMLRow":
        """Allow items to wrap to the next line.

        Args:
            value: FlexWrap enum or CSS string (wrap, nowrap, wrap-reverse).
                   Default is WRAP.

        Returns:
            Self for method chaining.

        Example:
            >>> row.wrap()  # Enable wrapping
            >>> row.wrap(FlexWrap.WRAP_REVERSE)  # Wrap in reverse order
        """
        if isinstance(value, str):
            value = FlexWrap(value)
        self._styles["flex-wrap"] = value.to_css()
        self._notify()
        return self

    def nowrap(self) -> "HTMLRow":
        """Prevent items from wrapping (default behavior).

        Returns:
            Self for method chaining.
        """
        self._styles["flex-wrap"] = FlexWrap.NOWRAP.to_css()
        self._notify()
        return self

    # =========================================================================
    # Direction Methods
    # =========================================================================

    def reverse(self) -> "HTMLRow":
        """Reverse the order of items.

        Returns:
            Self for method chaining.
        """
        self._styles["flex-direction"] = "row-reverse"
        self._notify()
        return self

    # =========================================================================
    # Item Sizing
    # =========================================================================

    def min_item_width(self, size: Size | str | int) -> "HTMLRow":
        """Set minimum width for child items (via CSS custom property).

        This works best with `.wrap()` to prevent items from becoming
        too small before wrapping.

        Args:
            size: Minimum item width.

        Returns:
            Self for method chaining.
        """
        if isinstance(size, int):
            size = Size.px(size)
        # Use a CSS custom property that children can reference
        self._styles["--min-item-width"] = _to_css(size)
        self._notify()
        return self

    # =========================================================================
    # Presets
    # =========================================================================

    def buttons(self) -> "HTMLRow":
        """Apply button row styling preset.

        Creates a row with appropriate gap and end-alignment,
        suitable for action buttons in forms or dialogs.

        Returns:
            Self for method chaining.
        """
        self._styles["gap"] = "8px"
        self._styles["justify-content"] = "flex-end"
        self._styles["align-items"] = "center"
        self._notify()
        return self

    def toolbar(self) -> "HTMLRow":
        """Apply toolbar styling preset.

        Creates a compact row suitable for toolbar layouts.

        Returns:
            Self for method chaining.
        """
        self._styles["gap"] = "4px"
        self._styles["align-items"] = "center"
        self._styles["padding"] = "4px 8px"
        self._notify()
        return self

    def centered(self) -> "HTMLRow":
        """Center all items both horizontally and vertically.

        Returns:
            Self for method chaining.
        """
        self._styles["justify-content"] = "center"
        self._styles["align-items"] = "center"
        self._notify()
        return self

    def spaced(self) -> "HTMLRow":
        """Distribute items with space between them.

        Returns:
            Self for method chaining.
        """
        self._styles["justify-content"] = "space-between"
        self._styles["align-items"] = "center"
        self._notify()
        return self

    def start(self) -> "HTMLRow":
        """Align items to the start (left).

        Returns:
            Self for method chaining.
        """
        self._styles["justify-content"] = "flex-start"
        self._notify()
        return self

    def end(self) -> "HTMLRow":
        """Align items to the end (right).

        Returns:
            Self for method chaining.
        """
        self._styles["justify-content"] = "flex-end"
        self._notify()
        return self

    # =========================================================================
    # Override styled and add_class for correct return type
    # =========================================================================

    def styled(self, **styles: str | CSSValue) -> "HTMLRow":
        """Apply additional inline styles.

        Args:
            **styles: CSS property-value pairs.

        Returns:
            Self for method chaining.
        """
        super().styled(**styles)
        return self

    def add_class(self, *class_names: str) -> "HTMLRow":
        """Add CSS classes.

        Args:
            *class_names: CSS class names to add.

        Returns:
            Self for method chaining.
        """
        super().add_class(*class_names)
        return self

    def gap(self, size: Size | str | int) -> "HTMLRow":
        """Set the gap between child elements.

        Args:
            size: Gap size.

        Returns:
            Self for method chaining.
        """
        super().gap(size)
        return self

    def padding(self, size: "Spacing | Size | str | int") -> "HTMLRow":
        """Set internal padding.

        Args:
            size: Padding size.

        Returns:
            Self for method chaining.
        """
        super().padding(size)
        return self

    def margin(self, size: "Spacing | Size | str | int") -> "HTMLRow":
        """Set external margin.

        Args:
            size: Margin size.

        Returns:
            Self for method chaining.
        """
        super().margin(size)
        return self

    def width(self, size: Size | str | int) -> "HTMLRow":
        """Set container width.

        Args:
            size: Width.

        Returns:
            Self for method chaining.
        """
        super().width(size)
        return self

    def height(self, size: Size | str | int) -> "HTMLRow":
        """Set container height.

        Args:
            size: Height.

        Returns:
            Self for method chaining.
        """
        super().height(size)
        return self
