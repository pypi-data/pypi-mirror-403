"""HTMLButton - A clickable button widget."""

from __future__ import annotations

import html
import threading
from collections.abc import Callable
from typing import Self


class HTMLButton:
    """A clickable button widget for use with Animate.

    Buttons support click callbacks and styled presets for common use cases.

    Examples:
        >>> button = HTMLButton("Click Me")
        >>> button = HTMLButton("Submit").primary()
        >>> button = HTMLButton("Delete").danger().on_click(handle_delete)

        # With Animate
        >>> with Animate() as anim:
        ...     def on_click():
        ...         print("Button clicked!")
        ...     anim.add(HTMLButton("Click").on_click(on_click))
    """

    def __init__(self, label: str) -> None:
        """Create a button with the given label.

        Args:
            label: The text to display on the button.
        """
        self._label = label
        self._on_click: Callable[[], None] | None = None
        self._styles: dict[str, str] = {}
        self._css_classes: list[str] = ["anim-button"]
        self._anim_id: str | None = None
        self._lock = threading.Lock()
        # For compatibility with HTMLInput interface
        self._value = None
        self._on_change = None

    @property
    def label(self) -> str:
        """Get the button label."""
        return self._label

    def on_click(self, callback: Callable[[], None]) -> "HTMLButton":
        """Register a callback for button clicks.

        The callback is called whenever the button is clicked in the browser.
        The callback takes no arguments.

        Args:
            callback: A function to call when the button is clicked.

        Returns:
            Self for method chaining.

        Examples:
            >>> def handle_click():
            ...     print("Button was clicked!")
            >>> button = HTMLButton("Click Me").on_click(handle_click)
        """
        self._on_click = callback
        return self

    def render(self) -> str:
        """Return HTML representation of this button.

        Returns:
            A string containing valid HTML for the button.
        """
        attrs = self._build_attributes()
        escaped_label = html.escape(self._label)

        # Add data-anim-id for event handling
        anim_id_attr = ""
        if self._anim_id:
            anim_id_attr = f' data-anim-id="{html.escape(self._anim_id)}"'

        if attrs:
            return f"<button {attrs}{anim_id_attr}>{escaped_label}</button>"
        return f"<button{anim_id_attr}>{escaped_label}</button>"

    def __html__(self) -> str:
        """Jinja2 auto-escaping protocol."""
        return self.render()

    def styled(self, **styles: str) -> "HTMLButton":
        """Return a copy with additional inline styles.

        Style names use Python convention (underscores) and are
        converted to CSS convention (hyphens) automatically.

        Args:
            **styles: CSS property-value pairs, e.g., font_size="16px"

        Returns:
            A new instance with the combined styles.
        """
        new_button = HTMLButton(self._label)
        new_button._on_click = self._on_click
        new_button._anim_id = self._anim_id
        new_button._styles = dict(self._styles)
        new_button._css_classes = list(self._css_classes)

        # Add new styles, converting underscores to hyphens
        for key, value in styles.items():
            css_key = key.replace("_", "-")
            new_button._styles[css_key] = value

        return new_button

    def add_class(self, *class_names: str) -> "HTMLButton":
        """Return a copy with additional CSS classes.

        Args:
            *class_names: CSS class names to add.

        Returns:
            A new instance with the additional classes.
        """
        new_button = HTMLButton(self._label)
        new_button._on_click = self._on_click
        new_button._anim_id = self._anim_id
        new_button._styles = dict(self._styles)
        new_button._css_classes = list(self._css_classes) + list(class_names)
        return new_button

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

    # Styled presets
    def primary(self) -> "HTMLButton":
        """Return a copy styled as a primary button (blue).

        Returns:
            A new instance with primary styling.
        """
        return self.add_class("primary")

    def success(self) -> "HTMLButton":
        """Return a copy styled as a success button (green).

        Returns:
            A new instance with success styling.
        """
        return self.add_class("success")

    def danger(self) -> "HTMLButton":
        """Return a copy styled as a danger button (red).

        Returns:
            A new instance with danger styling.
        """
        return self.add_class("danger")

    def warning(self) -> "HTMLButton":
        """Return a copy styled as a warning button (orange).

        Returns:
            A new instance with warning styling.
        """
        return self.add_class("warning")

    def large(self) -> "HTMLButton":
        """Return a copy styled with larger text and padding.

        Returns:
            A new instance with large styling.
        """
        return self.styled(font_size="18px", padding="14px 28px")

    def small(self) -> "HTMLButton":
        """Return a copy styled with smaller text and padding.

        Returns:
            A new instance with small styling.
        """
        return self.styled(font_size="12px", padding="6px 12px")
