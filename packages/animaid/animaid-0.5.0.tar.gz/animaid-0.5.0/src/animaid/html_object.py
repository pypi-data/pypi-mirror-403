"""Base class for HTML-renderable types."""

from abc import ABC, abstractmethod
from typing import Self


class HTMLObject(ABC):
    """Abstract base class for all HTML-renderable types.

    All HTML* types (HTMLString, HTMLList, HTMLDict) inherit from this
    to ensure a consistent interface for rendering Python objects as
    styled HTML. When rendering nested objects, any item that is an
    HTMLObject will have its render() method called automatically.
    """

    _styles: dict[str, str]
    _css_classes: list[str]

    @abstractmethod
    def render(self) -> str:
        """Return HTML representation of this object.

        Returns:
            A string containing valid HTML that can be embedded in a page.
        """
        ...

    def __html__(self) -> str:
        """Jinja2 auto-escaping protocol.

        When Jinja2 encounters an object with __html__, it calls this
        method and marks the result as safe (no escaping).

        Returns:
            The rendered HTML string.
        """
        return self.render()

    @abstractmethod
    def styled(self, **styles: str) -> Self:
        """Return a copy with additional inline styles.

        Style names use Python convention (underscores) and are
        converted to CSS convention (hyphens) automatically.

        Args:
            **styles: CSS property-value pairs, e.g., font_size="16px"

        Returns:
            A new instance with the combined styles.
        """
        ...

    @abstractmethod
    def add_class(self, *class_names: str) -> Self:
        """Return a copy with additional CSS classes.

        Args:
            *class_names: CSS class names to add.

        Returns:
            A new instance with the additional classes.
        """
        ...

    def _build_style_string(self) -> str:
        """Convert internal styles dict to CSS style attribute value."""
        if not self._styles:
            return ""
        return "; ".join(f"{k}: {v}" for k, v in self._styles.items())

    def _build_class_string(self) -> str:
        """Convert internal classes list to CSS class attribute value."""
        if not self._css_classes:
            return ""
        return " ".join(self._css_classes)

    def _build_attributes(self) -> str:
        """Build the complete HTML attributes string."""
        parts = []

        class_str = self._build_class_string()
        if class_str:
            parts.append(f'class="{class_str}"')

        style_str = self._build_style_string()
        if style_str:
            parts.append(f'style="{style_str}"')

        return " ".join(parts)
