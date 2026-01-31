"""HTMLColumn - Vertical flex container."""

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


class HTMLColumn(HTMLContainer):
    """A vertical flex container for arranging items in a column.

    HTMLColumn uses CSS flexbox with `flex-direction: column` to arrange
    children vertically. It provides methods for controlling alignment,
    justification, and spacing.

    Examples:
        >>> from animaid import HTMLColumn, HTMLString
        >>> column = HTMLColumn([
        ...     HTMLString("Title").bold().xl(),
        ...     HTMLString("Subtitle").muted(),
        ...     HTMLString("Content here..."),
        ... ]).gap(8)

        >>> # Form-style layout
        >>> column = HTMLColumn(form_fields).form()

        >>> # Stacked layout with consistent spacing
        >>> column = HTMLColumn(items).stack()
    """

    def __init__(
        self,
        children: list[Any] | None = None,
        **styles: str | CSSValue,
    ) -> None:
        """Create a new vertical column container.

        Args:
            children: List of child elements.
            **styles: Initial CSS styles.
        """
        super().__init__(children, **styles)
        # Set default flex styles
        self._styles["display"] = "flex"
        self._styles["flex-direction"] = "column"

    # =========================================================================
    # Alignment Methods
    # =========================================================================

    def align(self, value: AlignItems | str) -> "HTMLColumn":
        """Set horizontal alignment of items within the column.

        Args:
            value: AlignItems enum or CSS string (start, center, end, stretch, baseline).

        Returns:
            Self for method chaining.

        Example:
            >>> column.align(AlignItems.CENTER)
            >>> column.align("center")  # Also works
        """
        if isinstance(value, str):
            value = AlignItems(value)
        self._styles["align-items"] = value.to_css()
        self._notify()
        return self

    def justify(self, value: JustifyContent | str) -> "HTMLColumn":
        """Set vertical distribution of items within the column.

        Args:
            value: JustifyContent enum or CSS string
                   (start, center, end, space-between, space-around, space-evenly).

        Returns:
            Self for method chaining.

        Example:
            >>> column.justify(JustifyContent.SPACE_BETWEEN)
            >>> column.justify("space-between")  # Also works
        """
        if isinstance(value, str):
            value = JustifyContent(value)
        self._styles["justify-content"] = value.to_css()
        self._notify()
        return self

    # =========================================================================
    # Wrapping Methods
    # =========================================================================

    def wrap(self, value: FlexWrap | str = FlexWrap.WRAP) -> "HTMLColumn":
        """Allow items to wrap to the next column (rarely used).

        Args:
            value: FlexWrap enum or CSS string.

        Returns:
            Self for method chaining.
        """
        if isinstance(value, str):
            value = FlexWrap(value)
        self._styles["flex-wrap"] = value.to_css()
        self._notify()
        return self

    # =========================================================================
    # Direction Methods
    # =========================================================================

    def reverse(self) -> "HTMLColumn":
        """Reverse the order of items (bottom to top).

        Returns:
            Self for method chaining.
        """
        self._styles["flex-direction"] = "column-reverse"
        self._notify()
        return self

    # =========================================================================
    # Presets
    # =========================================================================

    def stack(self) -> "HTMLColumn":
        """Apply simple stacked layout preset.

        Creates a column with consistent 8px gap between items.

        Returns:
            Self for method chaining.
        """
        self._styles["gap"] = "8px"
        self._notify()
        return self

    def form(self) -> "HTMLColumn":
        """Apply form-style layout preset.

        Creates a column with appropriate spacing for form fields
        and full-width stretching.

        Returns:
            Self for method chaining.
        """
        self._styles["gap"] = "12px"
        self._styles["align-items"] = "stretch"
        self._notify()
        return self

    def centered(self) -> "HTMLColumn":
        """Center all items both horizontally and vertically.

        Returns:
            Self for method chaining.
        """
        self._styles["justify-content"] = "center"
        self._styles["align-items"] = "center"
        self._notify()
        return self

    def spaced(self) -> "HTMLColumn":
        """Distribute items with space between them.

        Returns:
            Self for method chaining.
        """
        self._styles["justify-content"] = "space-between"
        self._notify()
        return self

    def start(self) -> "HTMLColumn":
        """Align items to the start (top).

        Returns:
            Self for method chaining.
        """
        self._styles["justify-content"] = "flex-start"
        self._notify()
        return self

    def end(self) -> "HTMLColumn":
        """Align items to the end (bottom).

        Returns:
            Self for method chaining.
        """
        self._styles["justify-content"] = "flex-end"
        self._notify()
        return self

    def stretch(self) -> "HTMLColumn":
        """Stretch items to fill the column width.

        Returns:
            Self for method chaining.
        """
        self._styles["align-items"] = "stretch"
        self._notify()
        return self

    # =========================================================================
    # Override base methods for correct return type
    # =========================================================================

    def styled(self, **styles: str | CSSValue) -> "HTMLColumn":
        """Apply additional inline styles.

        Args:
            **styles: CSS property-value pairs.

        Returns:
            Self for method chaining.
        """
        super().styled(**styles)
        return self

    def add_class(self, *class_names: str) -> "HTMLColumn":
        """Add CSS classes.

        Args:
            *class_names: CSS class names to add.

        Returns:
            Self for method chaining.
        """
        super().add_class(*class_names)
        return self

    def gap(self, size: Size | str | int) -> "HTMLColumn":
        """Set the gap between child elements.

        Args:
            size: Gap size.

        Returns:
            Self for method chaining.
        """
        super().gap(size)
        return self

    def padding(self, size: Spacing | Size | str | int) -> "HTMLColumn":
        """Set internal padding.

        Args:
            size: Padding size.

        Returns:
            Self for method chaining.
        """
        super().padding(size)
        return self

    def margin(self, size: Spacing | Size | str | int) -> "HTMLColumn":
        """Set external margin.

        Args:
            size: Margin size.

        Returns:
            Self for method chaining.
        """
        super().margin(size)
        return self

    def width(self, size: Size | str | int) -> "HTMLColumn":
        """Set container width.

        Args:
            size: Width.

        Returns:
            Self for method chaining.
        """
        super().width(size)
        return self

    def height(self, size: Size | str | int) -> "HTMLColumn":
        """Set container height.

        Args:
            size: Height.

        Returns:
            Self for method chaining.
        """
        super().height(size)
        return self
