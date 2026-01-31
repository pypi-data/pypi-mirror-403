"""HTMLSelect - A dropdown select widget with two-way binding."""

from __future__ import annotations

import html
import threading
from collections.abc import Callable
from typing import Self


class HTMLSelect:
    """A dropdown select widget with two-way binding.

    The value property is automatically synced from the browser when
    the user selects an option.

    Examples:
        >>> select = HTMLSelect(options=["Red", "Green", "Blue"])
        >>> select = HTMLSelect(
        ...     options=["Small", "Medium", "Large"],
        ...     value="Medium"
        ... ).on_change(handle_change)

        # With Animate - two-way binding
        >>> with Animate() as anim:
        ...     color = HTMLSelect(options=["Red", "Green", "Blue"])
        ...     anim.add(color)
        ...     # Later, read the current value:
        ...     print(color.value)  # Selected option synced from browser
    """

    def __init__(
        self,
        options: list[str],
        value: str | None = None,
    ) -> None:
        """Create a select widget.

        Args:
            options: List of option strings to display.
            value: The initially selected value (defaults to first option).
        """
        self._options = list(options)
        self._value = value if value is not None else (options[0] if options else "")
        self._on_change: Callable[[str], None] | None = None
        self._styles: dict[str, str] = {}
        self._css_classes: list[str] = ["anim-select"]
        self._anim_id: str | None = None
        self._lock = threading.Lock()

    @property
    def value(self) -> str:
        """Get the currently selected value (thread-safe).

        The value is automatically synced from the browser when the user
        selects an option.

        Returns:
            The currently selected option string.
        """
        with self._lock:
            return self._value

    @value.setter
    def value(self, new_value: str) -> None:
        """Set the selected value (thread-safe).

        Note: Setting the value programmatically does not automatically
        update the browser display. Use anim.refresh() to update.

        Args:
            new_value: The new value to select.
        """
        with self._lock:
            self._value = new_value

    @property
    def options(self) -> list[str]:
        """Get the list of options."""
        return list(self._options)

    def on_change(self, callback: Callable[[str], None]) -> "HTMLSelect":
        """Register a callback for selection changes.

        The callback is called when the user selects a different option.

        Args:
            callback: A function that takes the new selected value as argument.

        Returns:
            Self for method chaining.

        Examples:
            >>> def handle_change(value):
            ...     print(f"Selected: {value}")
            >>> select = HTMLSelect(["A", "B", "C"]).on_change(handle_change)
        """
        self._on_change = callback
        return self

    def render(self) -> str:
        """Return HTML representation of this select.

        Returns:
            A string containing valid HTML for the select.
        """
        attrs = self._build_attributes()

        # Add data-anim-id for event handling
        anim_id_attr = ""
        if self._anim_id:
            anim_id_attr = f' data-anim-id="{html.escape(self._anim_id)}"'

        # Build options HTML
        options_html = []
        for option in self._options:
            escaped_option = html.escape(option)
            selected = " selected" if option == self._value else ""
            options_html.append(
                f'<option value="{escaped_option}"{selected}>{escaped_option}</option>'
            )
        options_str = "".join(options_html)

        if attrs:
            return f"<select {attrs}{anim_id_attr}>{options_str}</select>"
        return f"<select{anim_id_attr}>{options_str}</select>"

    def __html__(self) -> str:
        """Jinja2 auto-escaping protocol."""
        return self.render()

    def styled(self, **styles: str) -> "HTMLSelect":
        """Return a copy with additional inline styles.

        Args:
            **styles: CSS property-value pairs.

        Returns:
            A new instance with the combined styles.
        """
        new_select = HTMLSelect(self._options, self._value)
        new_select._on_change = self._on_change
        new_select._anim_id = self._anim_id
        new_select._styles = dict(self._styles)
        new_select._css_classes = list(self._css_classes)

        # Add new styles, converting underscores to hyphens
        for key, value in styles.items():
            css_key = key.replace("_", "-")
            new_select._styles[css_key] = value

        return new_select

    def add_class(self, *class_names: str) -> "HTMLSelect":
        """Return a copy with additional CSS classes.

        Args:
            *class_names: CSS class names to add.

        Returns:
            A new instance with the additional classes.
        """
        new_select = HTMLSelect(self._options, self._value)
        new_select._on_change = self._on_change
        new_select._anim_id = self._anim_id
        new_select._styles = dict(self._styles)
        new_select._css_classes = list(self._css_classes) + list(class_names)
        return new_select

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
    def wide(self) -> "HTMLSelect":
        """Return a copy that expands to full width.

        Returns:
            A new instance with full width styling.
        """
        return self.styled(width="100%")

    def large(self) -> "HTMLSelect":
        """Return a copy with larger text and padding.

        Returns:
            A new instance with large styling.
        """
        return self.styled(font_size="18px", padding="14px 18px")

    def small(self) -> "HTMLSelect":
        """Return a copy with smaller text and padding.

        Returns:
            A new instance with small styling.
        """
        return self.styled(font_size="12px", padding="6px 10px")
