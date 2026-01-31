"""HTMLCard - Visual card container with optional title."""

from __future__ import annotations

import html
from typing import Any

from animaid.containers.base import HTMLContainer, _to_css
from animaid.css_types import (
    Color,
    CSSValue,
    RadiusSize,
    ShadowSize,
    Size,
    Spacing,
)


class HTMLCard(HTMLContainer):
    """A visual card container for grouping related content.

    HTMLCard provides a bordered/shadowed container with optional title,
    commonly used for dashboard panels, info cards, and grouped content.

    Examples:
        >>> from animaid import HTMLCard, HTMLString
        >>> card = HTMLCard([
        ...     HTMLString("User Profile").bold(),
        ...     HTMLString("Name: Alice"),
        ... ])

        >>> # Card with title
        >>> card = HTMLCard(
        ...     title="User Profile",
        ...     children=[HTMLString("Name: Alice")],
        ... )

        >>> # Styled card
        >>> card = HTMLCard(content).shadow().rounded()
        >>> card = HTMLCard(content).elevated()  # Preset with larger shadow
    """

    _title: str | None

    def __init__(
        self,
        children: list[Any] | None = None,
        *,
        title: str | None = None,
        **styles: str | CSSValue,
    ) -> None:
        """Create a new card container.

        Args:
            children: List of child elements.
            title: Optional title text displayed at the top.
            **styles: Initial CSS styles.
        """
        super().__init__(children, **styles)
        self._title = title

        # Default card styles
        self._styles.setdefault("background-color", "white")
        self._styles.setdefault("border-radius", RadiusSize.DEFAULT.to_css())
        self._styles.setdefault("padding", "16px")

    def render(self) -> str:
        """Render the card with optional title.

        Returns:
            HTML string with card structure.
        """
        parts = []

        # Render title if present
        if self._title:
            escaped_title = html.escape(self._title)
            parts.append(
                f'<div style="font-weight: bold; font-size: 1.1em; '
                f'margin-bottom: 12px; padding-bottom: 8px; '
                f'border-bottom: 1px solid #e5e7eb;">{escaped_title}</div>'
            )

        # Render children
        parts.append(self._render_children())

        content = "".join(parts)
        attrs = self._build_attributes()
        if attrs:
            return f"<div {attrs}>{content}</div>"
        return f"<div>{content}</div>"

    # =========================================================================
    # Title Methods
    # =========================================================================

    def set_title(self, text: str | None) -> "HTMLCard":
        """Set or change the card title.

        Args:
            text: Title text, or None to remove title.

        Returns:
            Self for method chaining.
        """
        self._title = text
        self._notify()
        return self

    @property
    def title(self) -> str | None:
        """Get the card title."""
        return self._title

    # =========================================================================
    # Shadow Methods
    # =========================================================================

    def shadow(self, size: ShadowSize | str = ShadowSize.DEFAULT) -> "HTMLCard":
        """Add a box shadow to the card.

        Args:
            size: ShadowSize enum or CSS shadow string.

        Returns:
            Self for method chaining.

        Example:
            >>> card.shadow()  # Default shadow
            >>> card.shadow(ShadowSize.LG)  # Larger shadow
        """
        if isinstance(size, ShadowSize):
            self._styles["box-shadow"] = size.to_css()
        else:
            self._styles["box-shadow"] = size
        self._notify()
        return self

    def no_shadow(self) -> "HTMLCard":
        """Remove the box shadow.

        Returns:
            Self for method chaining.
        """
        self._styles["box-shadow"] = ShadowSize.NONE.to_css()
        self._notify()
        return self

    # =========================================================================
    # Border Radius Methods
    # =========================================================================

    def rounded(self, size: RadiusSize | str = RadiusSize.DEFAULT) -> "HTMLCard":
        """Set the border radius (rounded corners).

        Args:
            size: RadiusSize enum or CSS radius string.

        Returns:
            Self for method chaining.

        Example:
            >>> card.rounded()  # Default rounding
            >>> card.rounded(RadiusSize.LG)  # More rounded
        """
        if isinstance(size, RadiusSize):
            self._styles["border-radius"] = size.to_css()
        else:
            self._styles["border-radius"] = size
        self._notify()
        return self

    def no_rounded(self) -> "HTMLCard":
        """Remove border radius (sharp corners).

        Returns:
            Self for method chaining.
        """
        self._styles["border-radius"] = RadiusSize.NONE.to_css()
        self._notify()
        return self

    # =========================================================================
    # Border Methods
    # =========================================================================

    def bordered(self, color: Color | str = "#e5e7eb") -> "HTMLCard":
        """Add a border to the card.

        Args:
            color: Border color.

        Returns:
            Self for method chaining.
        """
        self._styles["border"] = f"1px solid {_to_css(color)}"
        self._notify()
        return self

    def no_border(self) -> "HTMLCard":
        """Remove the border.

        Returns:
            Self for method chaining.
        """
        if "border" in self._styles:
            del self._styles["border"]
        self._notify()
        return self

    # =========================================================================
    # Background Methods
    # =========================================================================

    def background(self, color: Color | str) -> "HTMLCard":
        """Set the background color.

        Args:
            color: Background color.

        Returns:
            Self for method chaining.
        """
        self._styles["background-color"] = _to_css(color)
        self._notify()
        return self

    # =========================================================================
    # Presets
    # =========================================================================

    def default(self) -> "HTMLCard":
        """Apply default card styling (light border, subtle shadow).

        Returns:
            Self for method chaining.
        """
        self._styles["border"] = "1px solid #e5e7eb"
        self._styles["box-shadow"] = ShadowSize.SM.to_css()
        self._styles["border-radius"] = RadiusSize.DEFAULT.to_css()
        self._notify()
        return self

    def elevated(self) -> "HTMLCard":
        """Apply elevated card styling (prominent shadow).

        Returns:
            Self for method chaining.
        """
        self._styles["box-shadow"] = ShadowSize.LG.to_css()
        self._styles["border-radius"] = RadiusSize.LG.to_css()
        if "border" in self._styles:
            del self._styles["border"]
        self._notify()
        return self

    def outlined(self) -> "HTMLCard":
        """Apply outlined card styling (border only, no shadow).

        Returns:
            Self for method chaining.
        """
        self._styles["border"] = "1px solid #e5e7eb"
        self._styles["box-shadow"] = ShadowSize.NONE.to_css()
        self._notify()
        return self

    def flat(self) -> "HTMLCard":
        """Apply flat card styling (no border or shadow).

        Returns:
            Self for method chaining.
        """
        if "border" in self._styles:
            del self._styles["border"]
        self._styles["box-shadow"] = ShadowSize.NONE.to_css()
        self._notify()
        return self

    def filled(self, color: Color | str = "#f9fafb") -> "HTMLCard":
        """Apply filled card styling with background color.

        Args:
            color: Background color.

        Returns:
            Self for method chaining.
        """
        self._styles["background-color"] = _to_css(color)
        if "border" in self._styles:
            del self._styles["border"]
        self._styles["box-shadow"] = ShadowSize.NONE.to_css()
        self._notify()
        return self

    # =========================================================================
    # Override base methods for correct return type
    # =========================================================================

    def styled(self, **styles: str | CSSValue) -> "HTMLCard":
        """Apply additional inline styles."""
        super().styled(**styles)
        return self

    def add_class(self, *class_names: str) -> "HTMLCard":
        """Add CSS classes."""
        super().add_class(*class_names)
        return self

    def gap(self, size: Size | str | int) -> "HTMLCard":
        """Set the gap between child elements."""
        super().gap(size)
        return self

    def padding(self, size: Spacing | Size | str | int) -> "HTMLCard":
        """Set internal padding."""
        super().padding(size)
        return self

    def margin(self, size: Spacing | Size | str | int) -> "HTMLCard":
        """Set external margin."""
        super().margin(size)
        return self

    def width(self, size: Size | str | int) -> "HTMLCard":
        """Set container width."""
        super().width(size)
        return self

    def height(self, size: Size | str | int) -> "HTMLCard":
        """Set container height."""
        super().height(size)
        return self

    def max_width(self, size: Size | str | int) -> "HTMLCard":
        """Set maximum container width."""
        super().max_width(size)
        return self

    def min_width(self, size: Size | str | int) -> "HTMLCard":
        """Set minimum container width."""
        super().min_width(size)
        return self
