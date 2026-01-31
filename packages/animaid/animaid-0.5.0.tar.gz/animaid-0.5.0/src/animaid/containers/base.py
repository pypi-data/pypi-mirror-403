"""Base class for container widgets."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from animaid.css_types import (
    AlignItems,
    CSSValue,
    FlexWrap,
    JustifyContent,
    Size,
    Spacing,
)
from animaid.html_object import HTMLObject

if TYPE_CHECKING:
    from animaid.animate import Animate


def _to_css(value: object) -> str:
    """Convert a value to its CSS string representation."""
    if hasattr(value, "to_css"):
        return str(value.to_css())
    return str(value)


class HTMLContainer(HTMLObject):
    """Base class for all container widgets.

    Containers hold child elements and provide layout capabilities.
    They can be nested and support reactive updates when children change.

    Example:
        >>> container = HTMLContainer([HTMLString("Hello"), HTMLString("World")])
        >>> container.render()
        '<div>...</div>'
    """

    _styles: dict[str, str]
    _css_classes: list[str]
    _children: list[Any]
    _anim_id: str | None
    _anim: "Animate | None"
    _obs_id: str

    def __init__(
        self,
        children: list[Any] | None = None,
        **styles: str | CSSValue,
    ) -> None:
        """Create a new container.

        Args:
            children: List of child elements (HTMLObject instances or any renderable).
            **styles: Initial CSS styles (underscores converted to hyphens).
        """
        self._children = list(children) if children else []
        self._styles = {}
        self._css_classes = []
        self._anim_id = None
        self._anim = None
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

    def render(self) -> str:
        """Render the container and all children.

        Returns:
            HTML string with container div and rendered children.
        """
        children_html = self._render_children()
        attrs = self._build_attributes()
        if attrs:
            return f"<div {attrs}>{children_html}</div>"
        return f"<div>{children_html}</div>"

    def _render_children(self) -> str:
        """Render all children to HTML.

        Returns:
            Concatenated HTML of all children.
        """
        parts = []
        for child in self._children:
            if hasattr(child, "render"):
                parts.append(child.render())
            else:
                # Escape plain strings for safety
                import html

                parts.append(html.escape(str(child)))
        return "".join(parts)

    def __html__(self) -> str:
        """Jinja2 auto-escaping protocol."""
        return self.render()

    # =========================================================================
    # Child Management
    # =========================================================================

    def append(self, child: Any) -> "HTMLContainer":
        """Add a child element and trigger update.

        Args:
            child: The element to add.

        Returns:
            Self for method chaining.
        """
        self._children.append(child)
        self._notify()
        return self

    def extend(self, children: list[Any]) -> "HTMLContainer":
        """Add multiple child elements.

        Args:
            children: List of elements to add.

        Returns:
            Self for method chaining.
        """
        self._children.extend(children)
        self._notify()
        return self

    def insert(self, index: int, child: Any) -> "HTMLContainer":
        """Insert a child at a specific position.

        Args:
            index: Position to insert at.
            child: The element to insert.

        Returns:
            Self for method chaining.
        """
        self._children.insert(index, child)
        self._notify()
        return self

    def remove(self, child: Any) -> "HTMLContainer":
        """Remove a child element.

        Args:
            child: The element to remove.

        Returns:
            Self for method chaining.
        """
        self._children.remove(child)
        self._notify()
        return self

    def pop(self, index: int = -1) -> Any:
        """Remove and return a child at the given position.

        Args:
            index: Position to remove from (default: last).

        Returns:
            The removed child element.
        """
        child = self._children.pop(index)
        self._notify()
        return child

    def clear(self) -> "HTMLContainer":
        """Remove all children.

        Returns:
            Self for method chaining.
        """
        self._children.clear()
        self._notify()
        return self

    @property
    def children(self) -> list[Any]:
        """Get the list of children (read-only copy)."""
        return list(self._children)

    def __len__(self) -> int:
        """Return the number of children."""
        return len(self._children)

    def __iter__(self):
        """Iterate over children."""
        return iter(self._children)

    def __getitem__(self, index: int) -> Any:
        """Get a child by index."""
        return self._children[index]

    # =========================================================================
    # Styling Methods
    # =========================================================================

    def styled(self, **styles: str | CSSValue) -> "HTMLContainer":
        """Apply additional inline styles.

        Args:
            **styles: CSS property-value pairs (underscores become hyphens).

        Returns:
            Self for method chaining.
        """
        for key, value in styles.items():
            css_key = key.replace("_", "-")
            self._styles[css_key] = _to_css(value)
        self._notify()
        return self

    def add_class(self, *class_names: str) -> "HTMLContainer":
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

    def remove_class(self, *class_names: str) -> "HTMLContainer":
        """Remove CSS classes.

        Args:
            *class_names: CSS class names to remove.

        Returns:
            Self for method chaining.
        """
        for name in class_names:
            if name in self._css_classes:
                self._css_classes.remove(name)
        self._notify()
        return self

    # =========================================================================
    # Common Layout Methods
    # =========================================================================

    def gap(self, size: Size | str | int) -> "HTMLContainer":
        """Set the gap between child elements.

        Args:
            size: Gap size (Size, CSS string like "10px", or int pixels).

        Returns:
            Self for method chaining.
        """
        if isinstance(size, int):
            size = Size.px(size)
        self._styles["gap"] = _to_css(size)
        self._notify()
        return self

    def padding(self, size: Spacing | Size | str | int) -> "HTMLContainer":
        """Set internal padding.

        Args:
            size: Padding size (Spacing, Size, CSS string, or int pixels).

        Returns:
            Self for method chaining.
        """
        if isinstance(size, int):
            size = Size.px(size)
        self._styles["padding"] = _to_css(size)
        self._notify()
        return self

    def margin(self, size: Spacing | Size | str | int) -> "HTMLContainer":
        """Set external margin.

        Args:
            size: Margin size (Spacing, Size, CSS string, or int pixels).

        Returns:
            Self for method chaining.
        """
        if isinstance(size, int):
            size = Size.px(size)
        self._styles["margin"] = _to_css(size)
        self._notify()
        return self

    def width(self, size: Size | str | int) -> "HTMLContainer":
        """Set container width.

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

    def height(self, size: Size | str | int) -> "HTMLContainer":
        """Set container height.

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

    def max_width(self, size: Size | str | int) -> "HTMLContainer":
        """Set maximum container width.

        Args:
            size: Maximum width (Size, CSS string, or int pixels).

        Returns:
            Self for method chaining.
        """
        if isinstance(size, int):
            size = Size.px(size)
        self._styles["max-width"] = _to_css(size)
        self._notify()
        return self

    def max_height(self, size: Size | str | int) -> "HTMLContainer":
        """Set maximum container height.

        Args:
            size: Maximum height (Size, CSS string, or int pixels).

        Returns:
            Self for method chaining.
        """
        if isinstance(size, int):
            size = Size.px(size)
        self._styles["max-height"] = _to_css(size)
        self._notify()
        return self

    def min_width(self, size: Size | str | int) -> "HTMLContainer":
        """Set minimum container width.

        Args:
            size: Minimum width (Size, CSS string, or int pixels).

        Returns:
            Self for method chaining.
        """
        if isinstance(size, int):
            size = Size.px(size)
        self._styles["min-width"] = _to_css(size)
        self._notify()
        return self

    def min_height(self, size: Size | str | int) -> "HTMLContainer":
        """Set minimum container height.

        Args:
            size: Minimum height (Size, CSS string, or int pixels).

        Returns:
            Self for method chaining.
        """
        if isinstance(size, int):
            size = Size.px(size)
        self._styles["min-height"] = _to_css(size)
        self._notify()
        return self

    # =========================================================================
    # Full-Window Layout Methods
    # =========================================================================

    def full_width(self) -> "HTMLContainer":
        """Expand container to fill the full width of its parent.

        Returns:
            Self for method chaining.

        Example:
            >>> row = HTMLRow([...]).full_width()
        """
        self._styles["width"] = "100%"
        self._notify()
        return self

    def full_height(self) -> "HTMLContainer":
        """Expand container to fill the full viewport height.

        Returns:
            Self for method chaining.

        Example:
            >>> column = HTMLColumn([...]).full_height()
        """
        self._styles["min-height"] = "100vh"
        self._notify()
        return self

    def full_screen(self) -> "HTMLContainer":
        """Expand container to fill the entire viewport (width and height).

        Returns:
            Self for method chaining.

        Example:
            >>> layout = HTMLColumn([...]).full_screen()
        """
        self._styles["width"] = "100%"
        self._styles["min-height"] = "100vh"
        self._notify()
        return self

    def expand(self) -> "HTMLContainer":
        """Make this container expand to fill available space in a flex parent.

        Use this on a child container to make it grow and fill remaining space.

        Returns:
            Self for method chaining.

        Example:
            >>> # Header, expandable content, footer layout
            >>> layout = HTMLColumn([
            ...     HTMLString("Header"),
            ...     HTMLColumn([HTMLString("Content")]).expand(),
            ...     HTMLString("Footer"),
            ... ]).full_height()
        """
        self._styles["flex"] = "1"
        self._notify()
        return self
